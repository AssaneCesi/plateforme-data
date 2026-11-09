"""Téléchargement des sources réelles : fichiers stock SIRENE et référentiel des communes."""
import json
import time

import duckdb
import httpx
import pandas as pd

from .journal import journal

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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

# --- Mise à jour depuis le DAG -------------------------------------------------------
# Les fichiers stock sont republiés une fois par mois. Le DAG tourne chaque jour : il ne
# retélécharge que si data.gouv.fr publie une version plus récente que le fichier local.

# Ajoute en haut du fichier, avec les autres imports :
#   from datetime import datetime, timezone
#   from email.utils import parsedate_to_datetime

FICHIERS_SIRENE = [("unites_legales_parquet", "StockUniteLegale.parquet"),
                   ("etablissements_parquet", "StockEtablissement.parquet")]


def _date_locale(chemin):
    return datetime.fromtimestamp(chemin.stat().st_mtime, tz=timezone.utc)


def _date_publication(url):
    """Last-Modified du fichier publié (requête HEAD, sans télécharger), ou None."""
    try:
        r = httpx.head(url, follow_redirects=True, timeout=30)
        r.raise_for_status()
        valeur = r.headers.get("last-modified")
        return parsedate_to_datetime(valeur) if valeur else None
    except (httpx.HTTPError, TypeError, ValueError) as e:
        log.warning("Date de publication illisible pour %s : %s", url, e)
        return None


def _du_mois_precedent(chemin, maintenant):
    locale = _date_locale(chemin)
    return (locale.year, locale.month) < (maintenant.year, maintenant.month)


def a_mettre_a_jour(url, chemin, maintenant=None):
    """(bool, raison). Absent : oui. Sinon on compare avec la date de publication ;
    si le serveur ne la donne pas, repli : un fichier d'un mois précédent est périmé."""
    maintenant = maintenant or datetime.now(timezone.utc)
    if not chemin.exists():
        return True, "fichier absent"
    publie = _date_publication(url)
    if publie is None:
        return _du_mois_precedent(chemin, maintenant), "repli mensuel (date de publication inconnue)"
    if publie > _date_locale(chemin):
        return True, f"nouvelle version publiée le {publie:%Y-%m-%d}"
    return False, f"à jour (version publiée le {publie:%Y-%m-%d})"


def mettre_a_jour_sources(cfg, force=False):
    """Tâche `telecharger` du DAG. Renvoie un petit résumé (stocké en XCom)."""
    maintenant = datetime.now(timezone.utc)
    resume = {}
    for cle, nom in FICHIERS_SIRENE:
        url, chemin = cfg["sirene"][cle], cfg["chemins"]["sirene"] / nom
        maj, raison = (True, "forcé") if force else a_mettre_a_jour(url, chemin, maintenant)
        log.info("%s : %s", nom, raison)
        if maj:
            _telecharger(url, chemin, force=True)
        _verifier_signature(chemin)          # même sans téléchargement : on ne charge jamais un fichier douteux
        resume[nom] = {"telecharge": maj, "raison": raison,
                       "taille_mo": round(chemin.stat().st_size / 1e6)}

    resume["nouvelle_version"] = any(v["telecharge"] for v in resume.values())

    communes = cfg["chemins"]["referentiels"] / "communes.parquet"
    maj = force or not communes.exists() or _du_mois_precedent(communes, maintenant)
    if maj:
        telecharger_communes(cfg)
    resume["communes.parquet"] = {"telecharge": maj}
    return resume