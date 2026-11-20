"""Enchaînement complet d'une exécution du pipeline.

Étapes appelables séparément (utilisées par le DAG Airflow) :
    etape_chargement        : brut (idempotent : rejouer une date remplace ses lignes)
    etape_controles_entree  : Great Expectations sur le brut ; renvoie les règles bloquantes en échec
    etape_dbt               : dbt build (modèles et tests)
    etape_sortie            : collecte des tests dbt dans dq.resultats, exports, rapport
`executer` les enchaîne dans un seul processus (utilisé par pipeline.py).
"""
from datetime import date, datetime

from . import chargement, collecte, controles_gx, rapport, regles as catalogue_regles
from .entrepot import connexion
from .journal import journal
from .transformation import DOSSIER_DBT, executer_dbt

log = journal("pipeline")


def nouvel_identifiant(date_chargement):
    """Identifiant unique à chaque lancement manuel (date + heure)."""
    return f"{date_chargement:%Y%m%d}_{datetime.now():%H%M%S}"


def identifiant_du_jour(date_chargement):
    """Identifiant déterministe pour une date : rejouer cette date écrase ses résultats
    dans dq.resultats au lieu de les dupliquer (utilisé par le DAG planifié)."""
    return f"{date_chargement:%Y%m%d}_planifie"


def etape_chargement(cfg, source, date_chargement, run_id):
    """Charge le brut. Rejouer la même date remplace ses lignes (voir chargement._ecrire)."""
    with connexion(cfg) as con:
        return chargement.charger(con, cfg, source, date_chargement, run_id)


def etape_controles_entree(cfg, run_id, date_chargement):
    """Contrôles Great Expectations sur le brut, enregistrés dans dq.resultats.

    Renvoie la liste des règles BLOQUANTES en échec (vide si tout va bien) : à l'appelant
    de décider d'arrêter le run avant dbt.
    """
    regles = catalogue_regles.charger_regles()
    with connexion(cfg) as con:
        lignes = controles_gx.controler_entree(con, regles, run_id, date_chargement)
        catalogue_regles.enregistrer(con, lignes)
    return [l for l in lignes if l["criticite"] == "bloquante" and l["statut"] != "ok"]


def etape_entree(cfg, source, date_chargement, run_id):
    """Chargement puis contrôles d'entrée (raccourci). Renvoie les règles bloquantes en échec."""
    etape_chargement(cfg, source, date_chargement, run_id)
    return etape_controles_entree(cfg, run_id, date_chargement)


def etape_dbt(cfg):
    """dbt build. Renvoie le code de retour (0 = tout est passé), sans lever d'exception.

    Les résultats d'un run précédent sont supprimés d'abord : si dbt échoue avant d'écrire
    les siens, on ne doit pas collecter ceux de la veille.
    """
    for nom in ("manifest.json", "run_results.json"):
        (DOSSIER_DBT / "target" / nom).unlink(missing_ok=True)
    return executer_dbt(cfg, ["build"])


def _resultats_dbt_presents():
    cible = DOSSIER_DBT / "target"
    return (cible / "manifest.json").exists() and (cible / "run_results.json").exists()


def etape_sortie(cfg, run_id, date_chargement, afficher_rapport=True):
    """Collecte des résultats dbt dans dq.resultats, exports, rapport.

    Renvoie True si une règle bloquante est en échec. Rejouer ne duplique rien :
    enregistrer() remplace les lignes du même run_id.
    """
    regles = catalogue_regles.charger_regles()
    with connexion(cfg) as con:
        if _resultats_dbt_presents():
            catalogue_regles.enregistrer(con, collecte.collecter_dbt(con, regles, run_id, date_chargement))
        else:
            log.error("Run %s : dbt n'a produit aucun résultat de test, collecte ignorée.", run_id)
        rapport.exporter(con, cfg["chemins"]["exports"])
        if afficher_rapport:
            rapport.afficher(con, run_id)
        return rapport.blocage(con, run_id)


def executer(cfg, source=None, date_chargement=None, afficher_rapport=True):
    """charger → contrôler l'entrée → dbt build → collecter → rapport.

    Retourne 0 si rien de bloquant, 1 si une règle bloquante échoue (publication bloquée).
    """
    source = source or cfg["source"]
    date_chargement = date_chargement or date.today()
    run_id = nouvel_identifiant(date_chargement)
    log.info("Début du run %s (source : %s)", run_id, source)

    etape_entree(cfg, source, date_chargement, run_id)
    code_dbt = etape_dbt(cfg)                         # la connexion est fermée pendant dbt
    bloque = etape_sortie(cfg, run_id, date_chargement, afficher_rapport)

    if bloque or code_dbt != 0:
        log.error("Run %s : règle bloquante en échec ou erreur dbt. Les marts ne doivent pas être publiés.", run_id)
        return 1
    log.info("Run %s terminé : rien de bloquant.", run_id)
    return 0
