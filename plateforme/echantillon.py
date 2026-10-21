"""Génère un échantillon SYNTHÉTIQUE au format des fichiers stock SIRENE.

Les colonnes portent les mêmes noms que les vrais fichiers : le même pipeline tourne
sur l'échantillon et sur les données réelles. Les entreprises sont inventées, et des
anomalies connues sont injectées pour que chaque règle ait quelque chose à trouver.
"""
import random
from datetime import date, datetime, timedelta

import pandas as pd

from .journal import journal
from .luhn import SIREN_LA_POSTE, completer_luhn, luhn_valide

log = journal("echantillon")

COMMUNES = (
    [(f"751{a:02d}", f"Paris {a}e Arrondissement" if a > 1 else "Paris 1er Arrondissement", "75", f"750{a:02d}") for a in range(1, 21)]
    + [("92012", "Boulogne-Billancourt", "92", "92100"), ("92040", "Issy-les-Moulineaux", "92", "92130"),
       ("92050", "Nanterre", "92", "92000"), ("92044", "Levallois-Perret", "92", "92300"),
       ("92051", "Neuilly-sur-Seine", "92", "92200"), ("92026", "Courbevoie", "92", "92400"),
       ("92062", "Puteaux", "92", "92800"), ("92073", "Suresnes", "92", "92150")]
)
NAF = ["47.11F", "56.10A", "62.01Z", "70.22Z", "68.20B", "43.21A", "86.21Z", "96.02A",
       "47.71Z", "69.20Z", "74.10Z", "85.59A", "41.20A", "49.32Z", "10.71C"]
CATEGORIES_PM = ["5710", "5499", "5720", "6540", "9220"]  # SAS, SARL, SASU, SCI, association
ACTIVITES = ["Boulangerie", "Atelier", "Cabinet", "Studio", "Garage", "Café", "Conseil", "Librairie",
             "Menuiserie", "Agence", "Épicerie", "Imprimerie", "Transports", "Pharmacie"]
NOMS = ["Martin", "Bernard", "Diallo", "Nguyen", "Moreau", "Laurent", "Traoré", "Lefèvre", "Mercier",
        "Benali", "Fontaine", "Rousseau", "Diop", "Garnier", "Chevalier", "Da Silva", "Faure", "Ndiaye"]
PRENOMS = ["Awa", "Lucas", "Fatou", "Hugo", "Inès", "Karim", "Léa", "Moussa", "Chloé", "Yanis"]
SUFFIXES = ["", " Conseil", " et Fils", " Services", " Paris", " Associés"]


def _date(rng, debut, fin):
    return debut + timedelta(days=rng.randint(0, (fin - debut).days))


def _siren_unique(rng, deja):
    while True:
        s = completer_luhn(str(rng.randint(10_000_000, 99_999_999)).zfill(8))
        if s not in deja and s != SIREN_LA_POSTE:
            deja.add(s)
            return s


def _siret(siren, rang):
    return completer_luhn(siren + str(rang).zfill(4))


def _siret_la_poste(rng, deja):
    """SIRET de La Poste : somme des chiffres multiple de 5, et invalide au sens de Luhn."""
    while True:
        nic = str(rng.randint(0, 99_999)).zfill(5)
        s = SIREN_LA_POSTE + nic
        if sum(map(int, s)) % 5 == 0 and not luhn_valide(s) and s not in deja:
            deja.add(s)
            return s


def generer(n_unites=4000, graine=42, facteur_volume=1.0, jour=None, graine_anomalies=None):
    """Retourne (unites_legales, etablissements, communes) sous forme de DataFrames.

    graine fixe les entreprises ; graine_anomalies fait varier les anomalies d'un jour à
    l'autre sans changer les entreprises. facteur_volume < 1 simule un fichier tronqué.
    """
    rng = random.Random(graine)
    jour = jour or date.today()
    n_unites = max(50, int(n_unites * facteur_volume))
    sirens = set()
    ul, etab = [], []

    for _ in range(n_unites):
        siren = _siren_unique(rng, sirens)
        est_ei = rng.random() < 0.35
        categorie = "1000" if est_ei else rng.choice(CATEGORIES_PM)
        active = rng.random() < 0.85
        diffusion = "P" if (est_ei and rng.random() < 0.12) or rng.random() < 0.02 else "O"
        nom = rng.choice(NOMS)
        creation = _date(rng, date(1985, 1, 1), jour - timedelta(days=30))
        denomination = None if est_ei else f"{rng.choice(ACTIVITES)} {nom}{rng.choice(SUFFIXES)}"
        ul.append({
            "siren": siren, "statutDiffusionUniteLegale": diffusion,
            "dateCreationUniteLegale": creation.isoformat(),
            "dateDernierTraitementUniteLegale": datetime.combine(_date(rng, date(2024, 1, 1), jour), datetime.min.time()).isoformat(),
            "etatAdministratifUniteLegale": "A" if active else "C",
            "denominationUniteLegale": denomination,
            "nomUniteLegale": ("[ND]" if diffusion == "P" else nom.upper()) if est_ei else None,
            "prenom1UniteLegale": ("[ND]" if diffusion == "P" else rng.choice(PRENOMS).upper()) if est_ei else None,
            "categorieJuridiqueUniteLegale": categorie,
            "activitePrincipaleUniteLegale": rng.choice(NAF),
            "nicSiegeUniteLegale": None, "dateDebut": creation.isoformat(),
        })
        n_etab = 1 + (rng.random() < 0.3) + (rng.random() < 0.1) + (rng.random() < 0.05)
        for rang in range(1, n_etab + 1):
            code, libelle, _, cp = rng.choice(COMMUNES)
            siret = _siret(siren, rang)
            siege = rang == 1
            if siege:
                ul[-1]["nicSiegeUniteLegale"] = siret[9:]
            ouvert = active and (siege or rng.random() < 0.8)
            debut_etab = _date(rng, creation, jour - timedelta(days=1))
            etab.append({
                "siren": siren, "nic": siret[9:], "siret": siret,
                "statutDiffusionEtablissement": diffusion,
                "dateCreationEtablissement": debut_etab.isoformat(),
                "dateDernierTraitementEtablissement": datetime.combine(_date(rng, date(2024, 1, 1), jour), datetime.min.time()).isoformat(),
                "etablissementSiege": "true" if siege else "false",
                "codePostalEtablissement": cp, "libelleCommuneEtablissement": libelle.upper(),
                "codeCommuneEtablissement": code, "dateDebut": debut_etab.isoformat(),
                "etatAdministratifEtablissement": "A" if ouvert else "F",
                "activitePrincipaleEtablissement": ul[-1]["activitePrincipaleUniteLegale"],
                "activitePrincipaleNAF25Etablissement": None,
            })

    # La Poste : identifiants valides selon leur règle propre (exception à documenter)
    deja = set()
    ul.append({**ul[0], "siren": SIREN_LA_POSTE, "denominationUniteLegale": "LA POSTE", "nomUniteLegale": None,
               "prenom1UniteLegale": None, "categorieJuridiqueUniteLegale": "5599", "statutDiffusionUniteLegale": "O",
               "etatAdministratifUniteLegale": "A"})
    for i in range(3):
        s = _siret_la_poste(rng, deja)
        if i == 0:
            ul[-1]["nicSiegeUniteLegale"] = s[9:]
        etab.append({**etab[0], "siren": SIREN_LA_POSTE, "nic": s[9:], "siret": s, "etablissementSiege": "true" if i == 0 else "false",
                     "etatAdministratifEtablissement": "A", "statutDiffusionEtablissement": "O"})

    etab, ul = _injecter_anomalies(random.Random(graine_anomalies if graine_anomalies is not None else graine), etab, ul, jour)
    communes = pd.DataFrame([{"code": c, "nom": n, "codeDepartement": d, "codesPostaux": cp} for c, n, d, cp in COMMUNES])
    log.info("Échantillon généré : %d unités légales, %d établissements (graine %d)", len(ul), len(etab), graine)
    return pd.DataFrame(ul).astype("string"), pd.DataFrame(etab).astype("string"), communes.astype("string")


def _injecter_anomalies(rng, etab, ul, jour):
    n = len(etab)
    choisis = lambda part: rng.sample(range(n), max(1, int(n * part)))

    for i in choisis(0.005):                                   # R04 clé de contrôle fausse
        s = etab[i]["siret"]
        etab[i]["siret"] = s[:-1] + str((int(s[-1]) + 1) % 10)
    for i in choisis(0.004):                                   # R06 commune inconnue du référentiel
        etab[i]["codeCommuneEtablissement"] = rng.choice(["75199", "92999"])
    for i in choisis(0.003):                                   # R07 code APE mal formé
        etab[i]["activitePrincipaleEtablissement"] = rng.choice(["4711F", "47.1F", "62-01Z"])
    for i in choisis(0.012):                                   # R08 code postal invalide
        etab[i]["codePostalEtablissement"] = rng.choice(["7501", "750011", "75O11"])
    for i in choisis(0.002):                                   # R09 état inconnu
        etab[i]["etatAdministratifEtablissement"] = "X"
    for i in choisis(0.002):                                   # R10 création dans le futur
        etab[i]["dateCreationEtablissement"] = (jour + timedelta(days=rng.randint(30, 2000))).isoformat()

    orphelins = []                                             # R05 SIREN absent des unités légales
    for i in choisis(0.003):
        siren = completer_luhn(str(rng.randint(10_000_000, 99_999_999)))
        orphelins.append({**etab[i], "siren": siren, "nic": "00017", "siret": _siret(siren, 1)})

    doublons = []                                              # R02 même SIRET deux fois dans le chargement
    for i in choisis(0.01):
        ancien = datetime.fromisoformat(etab[i]["dateDernierTraitementEtablissement"]) - timedelta(days=rng.randint(10, 400))
        doublons.append({**etab[i], "dateDernierTraitementEtablissement": ancien.isoformat(),
                         "libelleCommuneEtablissement": etab[i]["libelleCommuneEtablissement"].title()})

    formes = ["1234567890123", "12345678A01234", "9876543210987654"]                       # R03 : 0,05 %
    mal_formes = [{**etab[i], "siret": formes[k % 3], "siren": formes[k % 3][:9]}
                  for k, i in enumerate(rng.sample(range(n), max(1, round(n * 0.0005))))]
    absents = [{**etab[i], "siret": None} for i in rng.sample(range(n), max(1, round(n * 0.0003)))]  # R01 : 0,03 %

    # R12 : deux sièges actifs pour quelques unités actives
    actives = [u["siren"] for u in ul if u["etatAdministratifUniteLegale"] == "A" and u["siren"] != SIREN_LA_POSTE]
    for siren in rng.sample(actives, max(1, int(len(actives) * 0.005))):
        for e in etab:
            if e["siren"] == siren and e["etablissementSiege"] == "false":
                e["etablissementSiege"] = "true"
                e["etatAdministratifEtablissement"] = "A"
                break

    # R13 : personnes morales sans dénomination
    pm = [u for u in ul if u["categorieJuridiqueUniteLegale"] != "1000" and u["siren"] != SIREN_LA_POSTE]
    for u in rng.sample(pm, max(1, int(len(pm) * 0.005))):
        u["denominationUniteLegale"] = rng.choice([None, "", "  "])

    return etab + orphelins + doublons + mal_formes + absents, ul


def ecrire(dossier, n_unites=4000, graine=42, facteur_volume=1.0, jour=None, graine_anomalies=None):
    dossier.mkdir(parents=True, exist_ok=True)
    ul, etab, communes = generer(n_unites, graine, facteur_volume, jour, graine_anomalies)
    ul.to_parquet(dossier / "StockUniteLegale.parquet", index=False)
    etab.to_parquet(dossier / "StockEtablissement.parquet", index=False)
    communes.to_parquet(dossier / "communes.parquet", index=False)
    log.info("Fichiers écrits dans %s", dossier)
