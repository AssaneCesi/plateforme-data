import duckdb
import pandas as pd
import pytest

from plateforme.contrat import ContratViole, charger_contrat, liste_selection, verifier_schema


def test_colonne_requise_absente_arrete_le_chargement():
    contrat = charger_contrat("sirene_etablissements")
    colonnes = [c["source"] for c in contrat["colonnes"] if c["source"] != "codeCommuneEtablissement"]
    with pytest.raises(ContratViole, match="codeCommuneEtablissement"):
        verifier_schema(contrat, colonnes)


def test_colonne_optionnelle_absente_devient_null(tmp_path):
    contrat = charger_contrat("sirene_etablissements")
    colonnes = [c["source"] for c in contrat["colonnes"] if c["requise"]]
    assert verifier_schema(contrat, colonnes)
    fichier = tmp_path / "etab.parquet"
    pd.DataFrame([{c: "x" for c in colonnes}]).to_parquet(fichier)
    requete = f"SELECT {', '.join(liste_selection(contrat, colonnes))} FROM read_parquet('{fichier}')"
    ligne = duckdb.sql(requete).df().iloc[0]
    assert pd.isna(ligne["activite_principale_naf25"]) and ligne["siret"] == "x"
