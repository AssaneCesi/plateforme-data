"""Enchaînement complet d'une exécution du pipeline.

Trois étapes appelables séparément (utilisées par le DAG Airflow) :
    etape_entree : charger le brut + contrôles d'entrée
    etape_dbt    : dbt build (modèles et tests)
    etape_sortie : collecte des tests dbt + rapport + exports
`executer` les enchaîne dans le même processus (utilisé par pipeline.py).
"""
from datetime import date, datetime

from . import chargement, collecte, controles_gx, rapport, regles as catalogue_regles
from .entrepot import connexion
from .journal import journal
from .transformation import executer_dbt

log = journal("pipeline")


def nouvel_identifiant(date_chargement):
    return f"{date_chargement:%Y%m%d}_{datetime.now():%H%M%S}"


def etape_entree(cfg, source, date_chargement, run_id):
    """Brut + contrôles d'entrée. Lève une exception si le chargement échoue."""
    regles = catalogue_regles.charger_regles()
    with connexion(cfg) as con:
        chargement.charger(con, cfg, source, date_chargement, run_id)
        lignes = controles_gx.controler_entree(con, regles, run_id, date_chargement)
        catalogue_regles.enregistrer(con, lignes)


def etape_dbt(cfg):
    """dbt build. Renvoie le code de retour (0 = tout est passé), sans lever d'exception."""
    return executer_dbt(cfg, ["build"])


def etape_sortie(cfg, run_id, date_chargement, afficher_rapport=True):
    """Collecte des résultats dbt, rapport, exports. Renvoie True si une règle bloquante échoue."""
    regles = catalogue_regles.charger_regles()
    with connexion(cfg) as con:
        catalogue_regles.enregistrer(con, collecte.collecter_dbt(con, regles, run_id, date_chargement))
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