"""Lecture de la configuration (config.yml)."""
import os
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent


def charger_config(chemin=None):
    """Charge config.yml et convertit les chemins en chemins absolus.

    La variable d'environnement OBS_CONFIG permet de pointer vers un autre fichier
    (utilisé par les tests).
    """
    chemin = Path(chemin or os.environ.get("OBS_CONFIG") or RACINE / "config.yml")
    with open(chemin, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    base = chemin.parent
    for cle, valeur in cfg["chemins"].items():
        p = Path(valeur)
        cfg["chemins"][cle] = p if p.is_absolute() else (base / p).resolve()
    return cfg
