"""Transforme les résultats des tests dbt en lignes de dq.resultats.

dbt écrit deux fichiers après chaque exécution :
- target/manifest.json : la description de chaque test (dont meta.regle_id) ;
- target/run_results.json : le statut et le nombre d'échecs de chaque test.
Seuls les tests qui portent un regle_id alimentent le score ; les autres sont
des garde-fous techniques.
"""
import json

from .journal import journal
from .regles import construire_resultat
from .transformation import DOSSIER_DBT

log = journal("collecte")


def _denominateur(con, manifest, noeud):
    """Nombre de lignes contrôlées : taille du modèle testé (avec le filtre du test)."""
    meta = noeud.get("config", {}).get("meta") or noeud.get("meta") or {}
    if meta.get("denominateur_modele"):
        modele = next(n for n in manifest["nodes"].values()
                      if n["resource_type"] == "model" and n["name"] == meta["denominateur_modele"])
        filtre = meta.get("denominateur_filtre")
    else:
        attache = noeud.get("attached_node") or next(
            (d for d in noeud["depends_on"]["nodes"] if d.startswith("model.")), None)
        modele = manifest["nodes"][attache]
        filtre = noeud.get("config", {}).get("where")
    requete = f"SELECT count(*) FROM {modele['relation_name']}" + (f" WHERE {filtre}" if filtre else "")
    return con.execute(requete).fetchone()[0], modele["name"]


def collecter_dbt(con, regles, run_id, date_chargement):
    manifest = json.loads((DOSSIER_DBT / "target" / "manifest.json").read_text(encoding="utf-8"))
    resultats = json.loads((DOSSIER_DBT / "target" / "run_results.json").read_text(encoding="utf-8"))
    lignes = []
    for res in resultats["results"]:
        uid = res["unique_id"]
        if not uid.startswith("test."):
            continue
        noeud = manifest["nodes"][uid]
        meta = noeud.get("config", {}).get("meta") or noeud.get("meta") or {}
        regle_id = meta.get("regle_id")
        if not regle_id:
            continue
        if res["status"] in ("error", "skipped"):
            nb_controles, objet = None, noeud["name"]
            nb_echecs = None
        else:
            nb_controles, objet = _denominateur(con, manifest, noeud)
            nb_echecs = res.get("failures") or 0
        lignes.append(construire_resultat(regles, regle_id, objet, nb_controles, nb_echecs,
                                          run_id, date_chargement, outil="dbt"))
    en_echec = [l["regle_id"] for l in lignes if l["statut"] != "ok"]
    log.info("Tests dbt collectés : %d règles, en échec : %s", len(lignes), ", ".join(en_echec) or "aucune")
    return lignes
