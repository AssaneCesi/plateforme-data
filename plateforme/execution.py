"""Enchaînement complet d'une exécution du pipeline."""
from datetime import date, datetime

from . import chargement, collecte, controles_gx, rapport, regles as catalogue_regles
from .entrepot import connexion
from .journal import journal
from .transformation import executer_dbt

log = journal("pipeline")


def nouvel_identifiant(date_chargement):
    return f"{date_chargement:%Y%m%d}_{datetime.now():%H%M%S}"


def executer(cfg, source=None, date_chargement=None, afficher_rapport=True):
    """charger → contrôler l'entrée → dbt build → collecter → rapport.

    Retourne 0 si rien de bloquant, 1 si une règle bloquante échoue (publication bloquée).
    """
    source = source or cfg["source"]
    date_chargement = date_chargement or date.today()
    run_id = nouvel_identifiant(date_chargement)
    regles = catalogue_regles.charger_regles()
    log.info("Début du run %s (source : %s)", run_id, source)

    with connexion(cfg) as con:                       # 1. brut + 2. contrôles d'entrée
        chargement.charger(con, cfg, source, date_chargement, run_id)
        lignes = controles_gx.controler_entree(con, regles, run_id, date_chargement)
        catalogue_regles.enregistrer(con, lignes)

    code_dbt = executer_dbt(cfg, ["build"])           # 3. modèles et tests (la connexion est fermée)

    with connexion(cfg) as con:                       # 4. collecte + 5. rapport
        catalogue_regles.enregistrer(con, collecte.collecter_dbt(con, regles, run_id, date_chargement))
        rapport.exporter(con, cfg["chemins"]["exports"])
        if afficher_rapport:
            rapport.afficher(con, run_id)
        bloque = rapport.blocage(con, run_id)

    if bloque or code_dbt != 0:
        log.error("Run %s : règle bloquante en échec ou erreur dbt. Les marts ne doivent pas être publiés.", run_id)
        return 1
    log.info("Run %s terminé : rien de bloquant.", run_id)
    return 0
