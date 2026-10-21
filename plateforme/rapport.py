"""Score qualité par dimension, règles en échec, et exports pour le scorecard."""
from .journal import journal

log = journal("rapport")

SCORES = """
WITH poids AS (
    SELECT * FROM (VALUES ('bloquante', 3), ('majeure', 2), ('mineure', 1)) AS p(criticite, poids)
), par_dimension AS (
    SELECT r.run_id, r.date_chargement, r.dimension,
           1 - SUM(r.nb_echecs * p.poids) * 1.0 / NULLIF(SUM(r.nb_controles * p.poids), 0) AS score
    FROM dq.resultats r JOIN poids p USING (criticite)
    WHERE r.statut <> 'erreur'
    GROUP BY r.run_id, r.date_chargement, r.dimension
)
SELECT run_id, date_chargement, dimension, ROUND(100 * score, 2) AS score_pct FROM par_dimension
UNION ALL
SELECT run_id, date_chargement, 'GLOBAL', ROUND(100 * AVG(score), 2) FROM par_dimension
GROUP BY run_id, date_chargement
"""

LIBELLE_STATUT = {"ok": "toléré", "echec": "AU-DESSUS DU SEUIL", "erreur": "ERREUR"}


def _nombre(n):
    return f"{n:,}".replace(",", " ")


def afficher(con, run_id):
    scores = con.execute(f"SELECT dimension, score_pct FROM ({SCORES}) WHERE run_id = ? "
                         "ORDER BY dimension = 'GLOBAL', dimension", [run_id]).fetchall()
    regles = con.execute("""
        SELECT regle_id, criticite, nb_echecs, nb_controles, taux_echec, seuil, statut, libelle
        FROM dq.resultats WHERE run_id = ? ORDER BY regle_id""", [run_id]).fetchall()
    print()
    print(f"Rapport qualité, run {run_id}")
    print("=" * 78)
    print("Score par dimension (pondéré par la criticité)")
    for dimension, score in scores:
        print(f"  {dimension:<22} {score:>7.2f} %" if score is not None else f"  {dimension:<22}    n/a")
    avec_echecs = [r for r in regles if r[6] == "erreur" or (r[2] or 0) > 0]
    au_dessus = [r for r in regles if r[6] != "ok"]
    print()
    print(f"{len(regles)} règles évaluées, {len(avec_echecs)} avec des échecs, {len(au_dessus)} au-dessus de leur seuil")
    if avec_echecs:
        print(f"  {'Règle':<6} {'Criticité':<10} {'Échecs / contrôlés':>22} {'Taux':>8} {'Seuil':>8}  Statut")
    for regle_id, criticite, nb_echecs, nb_controles, taux, seuil, statut, libelle in avec_echecs:
        if statut == "erreur":
            print(f"  {regle_id:<6} {criticite:<10} {'':>22} {'':>8} {'':>8}  ERREUR ({libelle})")
            continue
        ratio = f"{_nombre(nb_echecs)} / {_nombre(nb_controles)}"
        print(f"  {regle_id:<6} {criticite:<10} {ratio:>22} {100 * taux:7.2f}% {100 * seuil:7.2f}%  "
              f"{LIBELLE_STATUT[statut]}")
    print("=" * 78)
    print()


def exporter(con, dossier):
    """CSV pour Power BI (ou tout autre outil) : historique complet, scores, chargements."""
    dossier.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY (SELECT * FROM dq.resultats ORDER BY execute_le, regle_id) TO '{dossier / 'dq_resultats.csv'}' (HEADER)")
    con.execute(f"COPY ({SCORES} ORDER BY 1, 3) TO '{dossier / 'dq_scores.csv'}' (HEADER)")
    con.execute(f"COPY (SELECT * FROM raw.chargements ORDER BY charge_le) TO '{dossier / 'chargements.csv'}' (HEADER)")
    log.info("Exports écrits dans %s", dossier)


def blocage(con, run_id):
    """Vrai si une règle bloquante dépasse son seuil ou n'a pas pu s'exécuter."""
    return con.execute("""SELECT count(*) FROM dq.resultats
        WHERE run_id = ? AND criticite = 'bloquante' AND statut <> 'ok'""", [run_id]).fetchone()[0] > 0
