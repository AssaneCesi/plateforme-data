"""Exécute tout le pipeline sur un petit échantillon synthétique (c'est aussi le test de la CI)."""
import duckdb
import yaml

from plateforme.config import charger_config
from plateforme.echantillon import ecrire
from plateforme.execution import executer


def test_pipeline_complet(tmp_path, monkeypatch):
    config = {
        "source": "echantillon", "departements": ["75"],
        "chemins": {k: str(tmp_path / k) for k in ["echantillon", "sirene", "referentiels", "api", "exports"]}
        | {"entrepot": str(tmp_path / "entrepot.duckdb")},
        "sirene": {}, "geo_api": "", "api_recherche": "",
    }
    chemin = tmp_path / "config.yml"
    chemin.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setenv("OBS_CONFIG", str(chemin))
    cfg = charger_config()

    ecrire(cfg["chemins"]["echantillon"], n_unites=1500, graine=1)
    assert executer(cfg, afficher_rapport=False) == 0

    con = duckdb.connect(str(cfg["chemins"]["entrepot"]), read_only=True)
    resultats = {r[0]: r[1:] for r in con.execute(
        "SELECT regle_id, nb_echecs, statut FROM dq.resultats").fetchall()}
    attendues = {"R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R12", "R13", "R19"}
    assert attendues <= set(resultats), f"règles manquantes : {attendues - set(resultats)}"
    assert resultats["R04"][0] > 0          # les anomalies injectées sont bien trouvées
    assert resultats["R19"] == (0, "ok")    # aucune donnée nominative exposée
    assert con.execute("SELECT count(*) FROM main.quarantaine_etablissements").fetchone()[0] >= 2  # R01 + R03
    assert (cfg["chemins"]["exports"] / "dq_scores.csv").exists()
