"""Lancement de dbt (modèles + tests) sur l'entrepôt DuckDB."""
import os
import shutil
import subprocess
import sys

from .config import RACINE
from .journal import journal

log = journal("dbt")
DOSSIER_DBT = RACINE / "dbt"


def commande_dbt():
    exe = shutil.which("dbt")
    return [exe] if exe else [sys.executable, "-m", "dbt.cli.main"]


def executer_dbt(cfg, arguments=("build",)):
    env = dict(os.environ, OBS_ENTREPOT=str(cfg["chemins"]["entrepot"]))
    cmd = commande_dbt() + list(arguments) + ["--project-dir", str(DOSSIER_DBT), "--profiles-dir", str(DOSSIER_DBT)]
    log.info("Lancement : dbt %s", " ".join(arguments))
    return subprocess.run(cmd, cwd=DOSSIER_DBT, env=env).returncode
