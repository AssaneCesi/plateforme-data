"""DAG de la plateforme : mêmes étapes que `python pipeline.py run`, une tâche par étape.
Le traitement reste dans le package `plateforme` (aucun import Airflow là-bas).
Ici on ne fait que l'orchestrer. Les tâches échangent des valeurs simples (run_id, date,
code dbt) : les données restent dans l'entrepôt DuckDB.
"""
import pendulum

from datetime import datetime

from airflow.sdk import dag, task, get_current_context

try:                                                    # l'emplacement a changé selon les versions
    from airflow.sdk.exceptions import AirflowFailException
except ImportError:
    from airflow.exceptions import AirflowFailException


@dag(
    dag_id="pipeline_plateforme_donnees",
    schedule="0 11 1 * *",                  # lancement manuel pour l'instant
    start_date=pendulum.datetime(2026, 10, 30, tz="Europe/Paris"),
    catchup=False,
    max_active_runs=1,              # DuckDB : un seul écrivain à la fois
    tags=["plateforme"],
)
def plateforme_donnees():

    @task
    def preparer():
        from datetime import date
        from plateforme.execution import nouvel_identifiant
        jour = date.today()
        return {"run_id": nouvel_identifiant(jour), "date": jour.isoformat()}

    @task
    def entree(ctx):
        from datetime import date
        from plateforme.config import charger_config
        from plateforme.execution import etape_entree
        cfg = charger_config()
        etape_entree(cfg, cfg["source"], date.fromisoformat(ctx["date"]), ctx["run_id"])

    @task
    def dbt_build():
        from plateforme.config import charger_config
        from plateforme.execution import etape_dbt
        return etape_dbt(charger_config())              # renvoie le code, n'échoue pas

    @task
    def sortie(ctx):
        from datetime import date
        from plateforme.config import charger_config
        from plateforme.execution import etape_sortie
        return etape_sortie(charger_config(), ctx["run_id"],
                            date.fromisoformat(ctx["date"]), afficher_rapport=False)

    @task
    def verdict(code_dbt, bloque):
        if bloque or code_dbt != 0:
            raise AirflowFailException("Règle bloquante en échec ou erreur dbt : marts non publiés.")

    ctx = preparer()
    e, d, s = entree(ctx), dbt_build(), sortie(ctx)
    e >> d >> s                                         # strictement séquentiel
    verdict(d, s)


plateforme_donnees()