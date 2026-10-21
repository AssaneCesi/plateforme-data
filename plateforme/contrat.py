"""Data contracts : lecture et contrôle du schéma reçu."""
from pathlib import Path

import yaml

from .config import RACINE
from .journal import journal

log = journal("contrat")


class ContratViole(Exception):
    """Le fichier reçu ne respecte pas le contrat : l'ingestion s'arrête."""


def charger_contrat(nom, dossier=None):
    chemin = Path(dossier or RACINE / "contracts") / f"{nom}.yml"
    with open(chemin, encoding="utf-8") as f:
        return yaml.safe_load(f)


def verifier_schema(contrat, colonnes_source):
    """Compare les colonnes reçues au contrat.

    Lève ContratViole si une colonne requise manque. Signale sans bloquer les colonnes
    optionnelles absentes et les colonnes reçues mais non prévues au contrat.
    """
    recues = set(colonnes_source)
    prevues = {c["source"] for c in contrat["colonnes"]}
    manquantes = [c["source"] for c in contrat["colonnes"] if c["requise"] and c["source"] not in recues]
    if manquantes:
        raise ContratViole(
            f"Contrat {contrat['id']} v{contrat['version']} : colonnes requises absentes du fichier reçu : "
            + ", ".join(manquantes)
            + ". Le producteur a peut-être changé son format : vérifie le dessin de fichier, "
              "puis mets le contrat à jour (nouvelle version) si le changement est confirmé."
        )
    optionnelles_absentes = [c["source"] for c in contrat["colonnes"] if not c["requise"] and c["source"] not in recues]
    if optionnelles_absentes:
        log.warning("Contrat %s : colonnes optionnelles absentes (remplies à NULL) : %s",
                    contrat["id"], ", ".join(optionnelles_absentes))
    nouvelles = sorted(recues - prevues)
    if nouvelles:
        log.info("Contrat %s : %d colonnes reçues non prévues au contrat (ignorées), ex. %s",
                 contrat["id"], len(nouvelles), ", ".join(nouvelles[:5]))
    return True


def liste_selection(contrat, colonnes_source):
    """Expressions SQL de sélection : chaque colonne est lue en texte et renommée.

    Le brut reste « tel que reçu » (tout en texte) ; le typage se fait en staging.
    """
    recues = set(colonnes_source)
    expressions = []
    for c in contrat["colonnes"]:
        if c["source"] in recues:
            expressions.append(f'CAST("{c["source"]}" AS VARCHAR) AS {c["cible"]}')
        else:
            expressions.append(f'CAST(NULL AS VARCHAR) AS {c["cible"]}')
    return expressions


def colonne_source(contrat, cible):
    for c in contrat["colonnes"]:
        if c["cible"] == cible:
            return c["source"]
    raise KeyError(cible)
