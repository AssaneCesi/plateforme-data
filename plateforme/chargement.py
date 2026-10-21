"""Chargement des fichiers stock dans la couche brute (raw) de l'entrepôt.

Principes :
- le contrat de chaque source décide des colonnes lues et de leur nom ;
- tout est chargé en texte : le brut reste « tel que reçu », le typage vient en staging ;
- chaque chargement est daté ; recharger une date remplace ses lignes (idempotence).
"""
import re
from datetime import date, datetime

from .contrat import charger_contrat, colonne_source, liste_selection, verifier_schema
from .entrepot import table_existe
from .journal import journal

log = journal("chargement")
MOTIF_DEPARTEMENT = re.compile(r"^(\d{2,3}|2[AB])$")


def _colonnes_fichier(con, chemin):
    return [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{chemin}')").fetchall()]


def _ecrire(con, table, requete, date_chargement, params=()):
    """Crée la table au besoin, ajoute les nouvelles colonnes, remplace la date chargée."""
    con.execute(f"CREATE TEMP TABLE _lot AS {requete}", list(params))
    if not table_existe(con, "raw", table):
        con.execute(f"CREATE TABLE raw.{table} AS SELECT * FROM _lot WHERE false")
    existantes = {r[0] for r in con.execute(f"DESCRIBE raw.{table}").fetchall()}
    for nom, type_ in [(r[0], r[1]) for r in con.execute("DESCRIBE _lot").fetchall()]:
        if nom not in existantes:                       # le contrat a gagné une colonne
            log.info("Évolution de schéma : ajout de raw.%s.%s", table, nom)
            con.execute(f"ALTER TABLE raw.{table} ADD COLUMN {nom} {type_}")
    con.execute(f"DELETE FROM raw.{table} WHERE date_chargement = ?", [date_chargement])
    con.execute(f"INSERT INTO raw.{table} BY NAME SELECT * FROM _lot")
    n = con.execute("SELECT count(*) FROM _lot").fetchone()[0]
    con.execute("DROP TABLE _lot")
    return n


def charger(con, cfg, source, date_chargement: date, run_id: str):
    dossier = cfg["chemins"]["echantillon"] if source == "echantillon" else cfg["chemins"]["sirene"]
    fichier_ul = dossier / "StockUniteLegale.parquet"
    fichier_etab = dossier / "StockEtablissement.parquet"
    for f in (fichier_ul, fichier_etab):
        if not f.exists():
            conseil = "python pipeline.py echantillon" if source == "echantillon" else "python pipeline.py telecharger"
            raise FileNotFoundError(f"{f} introuvable. Lance d'abord : {conseil}")

    contrat_etab = charger_contrat("sirene_etablissements")
    contrat_ul = charger_contrat("sirene_unites_legales")
    verifier_schema(contrat_etab, _colonnes_fichier(con, fichier_etab))
    verifier_schema(contrat_ul, _colonnes_fichier(con, fichier_ul))

    # Établissements : périmètre géographique en données réelles, tout l'échantillon sinon
    selection = ",\n  ".join(liste_selection(contrat_etab, _colonnes_fichier(con, fichier_etab)))
    filtre = "true"
    if source == "reel":
        deps = [str(d) for d in cfg["departements"]]
        invalides = [d for d in deps if not MOTIF_DEPARTEMENT.match(d)]
        if invalides:
            raise ValueError(f"Codes département invalides dans config.yml : {invalides}")
        col_commune = colonne_source(contrat_etab, "code_commune")
        filtre = " OR ".join(f"starts_with(CAST(\"{col_commune}\" AS VARCHAR), '{d}')" for d in deps)
    requete_etab = f"""
        SELECT {selection},
               CAST(? AS DATE) AS date_chargement, CAST(? AS VARCHAR) AS run_id
        FROM read_parquet('{fichier_etab}') WHERE {filtre}"""
    n_etab = _ecrire(con, "etablissements", requete_etab, date_chargement, (date_chargement, run_id))

    # Unités légales : seulement celles qui ont au moins un établissement dans le périmètre
    selection = ",\n  ".join(liste_selection(contrat_ul, _colonnes_fichier(con, fichier_ul)))
    col_siren = colonne_source(contrat_ul, "siren")
    requete_ul = f"""
        SELECT {selection},
               CAST(? AS DATE) AS date_chargement, CAST(? AS VARCHAR) AS run_id
        FROM read_parquet('{fichier_ul}')
        WHERE CAST("{col_siren}" AS VARCHAR) IN (
            SELECT DISTINCT siren FROM raw.etablissements WHERE date_chargement = ?)"""
    n_ul = _ecrire(con, "unites_legales", requete_ul, date_chargement, (date_chargement, run_id, date_chargement))

    n_com = charger_communes(con, cfg, source)

    for objet, n, fichier in [("etablissements", n_etab, fichier_etab), ("unites_legales", n_ul, fichier_ul)]:
        con.execute("DELETE FROM raw.chargements WHERE objet = ? AND date_chargement = ?", [objet, date_chargement])
        con.execute("INSERT INTO raw.chargements VALUES (?, ?, ?, ?, ?, ?)",
                    [run_id, objet, date_chargement, str(fichier), n, datetime.now()])
    log.info("Chargement du %s : %d établissements, %d unités légales, %d communes",
             date_chargement, n_etab, n_ul, n_com)
    return n_etab, n_ul


def charger_communes(con, cfg, source):
    """Référentiel géographique : remplacé en entier à chaque chargement."""
    if source == "echantillon":
        fichier = cfg["chemins"]["echantillon"] / "communes.parquet"
    else:
        fichier = cfg["chemins"]["referentiels"] / "communes.parquet"
    if not fichier.exists():
        log.warning("Référentiel des communes absent (%s) : la règle R06 échouera. "
                    "Lance : python pipeline.py telecharger", fichier)
        con.execute("CREATE OR REPLACE TABLE raw.communes (code VARCHAR, nom VARCHAR, code_departement VARCHAR, codes_postaux VARCHAR)")
        return 0
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.communes AS
        SELECT CAST(code AS VARCHAR) AS code, CAST(nom AS VARCHAR) AS nom,
               CAST("codeDepartement" AS VARCHAR) AS code_departement,
               CAST("codesPostaux" AS VARCHAR) AS codes_postaux
        FROM read_parquet('{fichier}')""")
    return con.execute("SELECT count(*) FROM raw.communes").fetchone()[0]
