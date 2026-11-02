"""DAG de la plateforme de données — version commentée.

Où trouver chaque exigence dans ce fichier
------------------------------------------
1. Quotidien                        -> `schedule=` dans @dag (§ 3)
2. Ingestion                        -> tâche `ingerer`
3. Contrôles GX à l'entrée,
   échec BLOQUANT                   -> tâche `controles_entree` (AirflowFailException) + le
                                       chaînage : dbt_build ne démarre que si elle réussit
4. dbt build                        -> tâche `dbt_build`
5. Publication dans dq.resultats    -> tâche `publier_resultats`
6. Alerte si règle bloquante        -> `_alerter` (callback) branché dans default_args
7. Deux retries avec délai          -> `retries` / `retry_delay` dans default_args
8. Ingestion idempotente            -> trois morceaux qui marchent ensemble :
                                       a. `_date_du_run` : la date vient du RUN, pas de l'horloge
                                       b. `preparer`     : run_id déterministe (AAAAMMJJ_planifie)
                                       c. plateforme/chargement.py::_ecrire : DELETE + INSERT
                                          dans une transaction (tout ou rien)

Flux :  preparer -> ingerer -> controles_entree -> dbt_build -> publier_resultats -> verdict

Le traitement reste dans le package `plateforme` : ce fichier ne fait qu'ORCHESTRER
(ordre, relances, alertes). C'est ce qui permet de garder `python pipeline.py run`.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pendulum
from airflow.sdk import dag, get_current_context, task

# Ces deux imports ont changé de place selon les versions d'Airflow 3.x : on essaie les deux.
try:
    from airflow.sdk import CronTriggerTimetable
except ImportError:
    from airflow.timetables.trigger import CronTriggerTimetable

try:
    from airflow.sdk.exceptions import AirflowFailException
except ImportError:
    from airflow.exceptions import AirflowFailException

PARIS = ZoneInfo("Europe/Paris")


# ---------------------------------------------------------------------------
# § 8a — IDEMPOTENCE : d'où vient la date des données ?
# ---------------------------------------------------------------------------
def _date_du_run(contexte):
    """Renvoie la date (Paris) du run Airflow, et NON la date du jour.

    Pourquoi : avec date.today(), rejouer le run du 3 novembre le 5 chargerait le 5,
    donc ne remplacerait rien et créerait un doublon. Avec la date du run, la même
    valeur ressort à chaque relance, à chaque « Clear » et à chaque rejeu manuel.

    logical_date = l'instant planifié du run ; run_after = fallback (run déclenché à la main).
    """
    run = contexte["dag_run"]
    instant = run.logical_date or run.run_after or datetime.now(PARIS)
    return instant.astimezone(PARIS).date()


# ---------------------------------------------------------------------------
# § 6 — ALERTE
# ---------------------------------------------------------------------------
def _alerter(contexte):
    """Callback appelé quand une tâche échoue DÉFINITIVEMENT.

    Airflow l'appelle une fois les retries épuisés (ou tout de suite pour une
    AirflowFailException, qui interdit les relances). Elle liste les règles bloquantes
    en échec et envoie le message (journal + Telegram si TELEGRAM_BOT_TOKEN et
    TELEGRAM_CHAT_ID sont définies dans l'environnement ; voir plateforme/alerte.py).
    """
    try:
        from plateforme1.alerte import alerter
        from plateforme.config import charger_config
        from plateforme1.execution import identifiant_du_jour

        jour = _date_du_run(contexte)
        ti = contexte["task_instance"]
        alerter(charger_config(), dag_id=ti.dag_id, tache=ti.task_id, date_chargement=jour,
                run_id=identifiant_du_jour(jour), erreur=contexte.get("exception"))
    except Exception as e:
        # Une alerte ratée ne doit jamais masquer l'échec d'origine : on journalise seulement.
        print(f"Alerte impossible : {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# § 3 — LE DAG
# ---------------------------------------------------------------------------
@dag(
    dag_id="pipeline_plateforme_donnees_complete",

    # QUOTIDIEN : tous les jours à 11:00, heure de Paris.
    # On passe un objet CronTriggerTimetable plutôt qu'une simple chaîne cron pour fixer
    # le fuseau explicitement (sinon l'heure dépend du fuseau de start_date / de la config).
    # Pour revenir à ton rythme mensuel : "0 11 1 * *" (le 1er du mois à 11:00).
    schedule=CronTriggerTimetable("0 11 * * *", timezone="Europe/Paris"),

    # start_date : première date à partir de laquelle des runs peuvent exister. Elle doit
    # être DANS LE PASSÉ : avec une date future, Airflow marque le run « success » sans
    # exécuter aucune tâche.
    start_date=pendulum.datetime(2026, 10, 30, tz="Europe/Paris"),

    # catchup=False : en réactivant le DAG après une pause, Airflow ne rejoue pas tous les
    # jours manqués (chaque run recharge de toute façon la source complète).
    catchup=False,

    # max_active_runs=1 : DuckDB n'accepte qu'UN écrivain à la fois. Deux runs en parallèle
    # se bloqueraient sur le fichier .duckdb.
    max_active_runs=1,

    # § 7 — default_args s'applique à CHAQUE tâche du DAG.
    default_args={
        "retries": 2,                                  # 2 relances => 3 tentatives au total
        "retry_delay": timedelta(minutes=5),           # attente entre deux tentatives
        "execution_timeout": timedelta(minutes=30),    # une tâche bloquée est tuée (puis relancée)
        "on_failure_callback": _alerter,               # § 6
    },
    tags=["plateforme", "qualite"],
)
def plateforme_donnees_complete():

    # -- Tâche 1 : figer la date et l'identifiant du run (§ 8b) ---------------------------
    @task
    def preparer():
        """Calcule UNE FOIS la date et le run_id, que toutes les tâches suivantes réutilisent.

        Le run_id est déterministe : même jour => même identifiant (`20261103_planifie`).
        Les résultats GX et dbt de ce jour sont donc REMPLACÉS au rejeu, pas dupliqués
        (regles.enregistrer supprime par run_id + règle avant d'insérer).
        Le dictionnaire passe d'une tâche à l'autre par XCom : réservé aux petites valeurs.
        """
        from plateforme1.execution import identifiant_du_jour

        jour = _date_du_run(get_current_context())
        return {"date": jour.isoformat(), "run_id": identifiant_du_jour(jour)}

    # -- Tâche 2 : ingestion (§ 2, § 8c) ----------------------------------------------------
    @task
    def ingerer(ctx):
        """Charge le brut dans raw.* avec date_chargement = date du run.

        Idempotence : chargement._ecrire fait DELETE de cette date puis INSERT dans une
        TRANSACTION. Si ça plante entre les deux, le DELETE est annulé : la date garde ses
        anciennes lignes au lieu de rester vide. Les autres dates ne sont jamais touchées.
        """
        from plateforme.config import charger_config
        from plateforme1.execution import etape_chargement

        cfg = charger_config()
        etape_chargement(cfg, cfg["source"], date.fromisoformat(ctx["date"]), ctx["run_id"])

    # -- Tâche 3 : contrôles Great Expectations, ÉCHEC BLOQUANT (§ 3) --------------------
    @task
    def controles_entree(ctx):
        """Joue les règles GX sur le brut et écrit les résultats dans dq.resultats.

        Si une règle de criticité « bloquante » est en échec, on lève AirflowFailException :
        - la tâche passe en « failed » SANS relance (relancer ne corrigerait pas la donnée) ;
        - dbt_build, en aval, passe en « upstream_failed » : dbt ne tourne pas ;
        - le callback _alerter envoie le message avec la liste des règles.
        Une erreur technique (exception ordinaire) serait, elle, relancée 2 fois.
        """
        from plateforme.config import charger_config
        from plateforme1.execution import etape_controles_entree

        bloquantes = etape_controles_entree(charger_config(), ctx["run_id"], date.fromisoformat(ctx["date"]))
        if bloquantes:
            ids = ", ".join(l["regle_id"] for l in bloquantes)
            raise AirflowFailException(f"Contrôles d'entrée : règle(s) bloquante(s) en échec ({ids}). dbt non lancé.")

    # -- Tâche 4 : dbt build (§ 4) -----------------------------------------------------------
    @task
    def dbt_build():
        """Lance `dbt build` et RENVOIE son code retour sans lever d'exception.

        Choix volontaire : si dbt échoue, on veut quand même publier les résultats des
        tests dbt (tâche suivante). C'est `verdict`, en fin de chaîne, qui fait échouer
        le run. Le code (un entier) passe par XCom.
        """
        from plateforme.config import charger_config
        from plateforme1.execution import etape_dbt

        return etape_dbt(charger_config())

    # -- Tâche 5 : publication des résultats (§ 5) ------------------------------------------
    @task
    def publier_resultats(ctx):
        """Lit les artefacts dbt (run_results.json) -> dq.resultats, et exporte les CSV."""
        from plateforme.config import charger_config
        from plateforme1.execution import etape_sortie

        etape_sortie(charger_config(), ctx["run_id"], date.fromisoformat(ctx["date"]), afficher_rapport=False)

    # -- Tâche 6 : verdict (dernière tâche = état final du run) -------------------------------
    @task
    def verdict(ctx, code_dbt):
        """Fait échouer le run si une règle bloquante est en échec OU si dbt a échoué.

        Pourquoi une tâche dédiée : l'état d'un run dépend de ses tâches FEUILLES.
        Sans elle, un run avec dbt en erreur pourrait s'afficher « success ».
        """
        from plateforme1.alerte import regles_bloquantes
        from plateforme.config import charger_config

        bloquantes = regles_bloquantes(charger_config(), ctx["run_id"])
        raisons = []
        if bloquantes:
            raisons.append("règles bloquantes en échec (" + ", ".join(b[0] for b in bloquantes) + ")")
        if code_dbt != 0:
            raisons.append(f"dbt en erreur (code {code_dbt})")
        if raisons:
            raise AirflowFailException("Marts non publiés : " + " ; ".join(raisons) + ".")

    # -- Chaînage ----------------------------------------------------------------------------
    # `>>` définit l'ordre. Appeler une tâche avec une autre en argument (ingerer(ctx)) crée
    # aussi une dépendance et transmet la valeur via XCom.
    ctx = preparer()
    code = dbt_build()
    ingerer(ctx) >> controles_entree(ctx) >> code >> publier_resultats(ctx) >> verdict(ctx, code)


plateforme_donnees_complete()