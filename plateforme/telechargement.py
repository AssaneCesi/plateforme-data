"""Téléchargement des sources réelles : fichiers stock SIRENE et référentiel des communes."""
import json
import time

import duckdb
import httpx
import pandas as pd

from .journal import journal

log = journal("telechargement")

# Signature attendue de chaque fichier : protège contre une inversion des liens
SIGNATURES = {
    "StockUniteLegale.parquet": ("denominationUniteLegale", "siret"),   # (doit contenir, ne doit pas contenir)
    "StockEtablissement.parquet": ("siret", "denominationUniteLegale"),
}


def _telecharger(url, destination, force=False, essais=3):
    if destination.exists() and not force:
        log.info("%s déjà présent, téléchargement ignoré (option --force pour le refaire)", destination.name)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partiel = destination.with_suffix(destination.suffix + ".part")
    for essai in range(1, essais + 1):
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=httpx.Timeout(60, read=300)) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                recu, prochain_palier = 0, 0.1
                with open(partiel, "wb") as f:
                    for bloc in r.iter_bytes(chunk_size=1 << 20):
                        f.write(bloc)
                        recu += len(bloc)
                        if total and recu / total >= prochain_palier:
                            log.info("%s : %d %%", destination.name, int(100 * recu / total))
                            prochain_palier += 0.1
            partiel.replace(destination)          # écriture atomique : jamais de fichier à moitié écrit
            log.info("%s téléchargé (%.0f Mo)", destination.name, destination.stat().st_size / 1e6)
            return
        except httpx.HTTPError as e:
            attente = 5 * essai
            log.warning("Échec du téléchargement de %s (essai %d/%d) : %s. Nouvel essai dans %d s",
                        destination.name, essai, essais, e, attente)
            time.sleep(attente)
    raise RuntimeError(f"Impossible de télécharger {url}")


def _verifier_signature(chemin):
    doit, ne_doit_pas = SIGNATURES[chemin.name]
    colonnes = [r[0] for r in duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{chemin}')").fetchall()]
    if doit not in colonnes or ne_doit_pas in colonnes:
        raise RuntimeError(
            f"{chemin.name} ne ressemble pas au fichier attendu (colonne {doit} absente ou {ne_doit_pas} présente). "
            "Les deux liens de config.yml sont peut-être inversés, ou la page data.gouv.fr a changé.")


def telecharger_sirene(cfg, force=False):
    dossier = cfg["chemins"]["sirene"]
    for cle, nom in [("unites_legales_parquet", "StockUniteLegale.parquet"),
                     ("etablissements_parquet", "StockEtablissement.parquet")]:
        _telecharger(cfg["sirene"][cle], dossier / nom, force=force)
        _verifier_signature(dossier / nom)


def telecharger_communes(cfg):
    """Communes ET arrondissements municipaux.

    Piège classique : SIRENE code les établissements de Paris, Lyon et Marseille avec
    le code de l'arrondissement (75101…75120), pas celui de la commune (75056). Sans les
    arrondissements, la règle R06 déclarerait fausses des données justes.
    """
    base = cfg["geo_api"].rstrip("/")
    champs = "code,nom,codeDepartement,codesPostaux"
    lignes = []
    for params in ({"fields": champs}, {"fields": champs, "type": "arrondissement-municipal"}):
        r = httpx.get(f"{base}/communes", params=params, timeout=60)
        r.raise_for_status()
        lignes.extend(r.json())
    df = pd.DataFrame(lignes)
    df["codesPostaux"] = df["codesPostaux"].apply(lambda v: json.dumps(v) if isinstance(v, list) else v)
    destination = cfg["chemins"]["referentiels"] / "communes.parquet"
    destination.parent.mkdir(parents=True, exist_ok=True)
    df.astype("string").to_parquet(destination, index=False)
    log.info("Référentiel des communes : %d lignes (communes et arrondissements)", len(df))
