"""Catalogue des règles (qualite/regles.yml) et enregistrement des résultats."""
from datetime import datetime

import yaml

from .config import RACINE

POIDS = {"bloquante": 3, "majeure": 2, "mineure": 1}


def charger_regles(chemin=None):
    with open(chemin or RACINE / "qualite" / "regles.yml", encoding="utf-8") as f:
        return {r["id"]: r for r in yaml.safe_load(f)["regles"]}


def construire_resultat(regles, regle_id, objet, nb_controles, nb_echecs, run_id, date_chargement, outil=None):
    """Une ligne de dq.resultats, enrichie avec le catalogue et un statut."""
    r = regles[regle_id]
    if nb_echecs is None:
        taux, statut = None, "erreur"
    elif not nb_controles:
        taux, statut = 0.0, "ok"
    else:
        taux = nb_echecs / nb_controles
        statut = "ok" if taux <= float(r["seuil"]) else "echec"
    return {
        "run_id": run_id, "regle_id": regle_id, "libelle": r["libelle"], "dimension": r["dimension"],
        "criticite": r["criticite"], "outil": outil or r["outil"], "objet": objet,
        "nb_controles": nb_controles, "nb_echecs": nb_echecs, "taux_echec": taux,
        "seuil": float(r["seuil"]), "statut": statut, "date_chargement": date_chargement,
        "execute_le": datetime.now(),
    }


def enregistrer(con, lignes):
    """Écrit les résultats ; rejouer un run remplace ses lignes (idempotent)."""
    colonnes = ["run_id", "regle_id", "libelle", "dimension", "criticite", "outil", "objet",
                "nb_controles", "nb_echecs", "taux_echec", "seuil", "statut", "date_chargement", "execute_le"]
    for l in lignes:
        con.execute("DELETE FROM dq.resultats WHERE run_id = ? AND regle_id = ? AND objet = ?",
                    [l["run_id"], l["regle_id"], l["objet"]])
        con.execute(f"INSERT INTO dq.resultats ({', '.join(colonnes)}) VALUES ({', '.join('?' * len(colonnes))})",
                    [l[c] for c in colonnes])
