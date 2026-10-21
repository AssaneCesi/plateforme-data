"""Connexion à l'entrepôt DuckDB et tables techniques."""
import duckdb

DDL = [
    "CREATE SCHEMA IF NOT EXISTS raw",
    "CREATE SCHEMA IF NOT EXISTS dq",
    """CREATE TABLE IF NOT EXISTS raw.chargements (
        run_id VARCHAR, objet VARCHAR, date_chargement DATE, source VARCHAR,
        nb_lignes BIGINT, charge_le TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS dq.resultats (
        run_id VARCHAR, regle_id VARCHAR, libelle VARCHAR, dimension VARCHAR,
        criticite VARCHAR, outil VARCHAR, objet VARCHAR,
        nb_controles BIGINT, nb_echecs BIGINT, taux_echec DOUBLE, seuil DOUBLE,
        statut VARCHAR, date_chargement DATE, execute_le TIMESTAMP)""",
]


def connexion(cfg, lecture_seule=False):
    chemin = cfg["chemins"]["entrepot"]
    chemin.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(chemin), read_only=lecture_seule)
    if not lecture_seule:
        for requete in DDL:
            con.execute(requete)
    return con


def table_existe(con, schema, table):
    return con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = ? AND table_name = ?",
        [schema, table],
    ).fetchone()[0] > 0


def dernier_chargement(con):
    if not table_existe(con, "raw", "etablissements"):
        return None
    return con.execute("SELECT max(date_chargement) FROM raw.etablissements").fetchone()[0]
