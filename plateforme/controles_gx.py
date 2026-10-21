"""Contrôles à l'entrée du pipeline, avec Great Expectations (GX Core 1.x).

Ils portent sur le dernier chargement brut, avant toute transformation : c'est
la frontière entre le producteur et nous.
"""
import os

os.environ.setdefault("TQDM_DISABLE", "1")   # pas de barres de progression dans les journaux

import great_expectations as gx  # noqa: E402
from great_expectations.data_context.types.base import ProgressBarsConfig  # noqa: E402

from .journal import journal  # noqa: E402
from .regles import construire_resultat  # noqa: E402

log = journal("controles_gx")


def _suite():
    e = gx.expectations
    return [
        e.ExpectColumnValuesToNotBeNull(column="siret", meta={"regle_id": "R01"}),
        e.ExpectColumnValuesToBeUnique(column="siret", meta={"regle_id": "R02"}),
        e.ExpectColumnValuesToMatchRegex(column="siret", regex=r"^[0-9]{14}$", meta={"regle_id": "R03"}),
        e.ExpectColumnValuesToMatchRegex(column="code_postal", regex=r"^[0-9]{5}$", mostly=0.99, meta={"regle_id": "R08"}),
    ]


def controler_entree(con, regles, run_id, date_chargement):
    df = con.execute(
        "SELECT siret, code_postal FROM raw.etablissements WHERE date_chargement = ?", [date_chargement]
    ).df()

    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = ProgressBarsConfig(globally=False)
    source = context.data_sources.add_pandas(name="sirene")
    asset = source.add_dataframe_asset(name="etablissements_bruts")
    lot = asset.add_batch_definition_whole_dataframe("dernier_chargement")
    suite = context.suites.add(gx.ExpectationSuite(name="entree_etablissements"))
    for attente in _suite():
        suite.add_expectation(attente)
    validation = context.validation_definitions.add(
        gx.ValidationDefinition(name="controle_entree", data=lot, suite=suite))
    resultat = validation.run(batch_parameters={"dataframe": df})

    lignes = []
    for r in resultat.results:
        regle_id = r.expectation_config.meta["regle_id"]
        lignes.append(construire_resultat(
            regles, regle_id, "raw.etablissements",
            nb_controles=r.result.get("element_count", len(df)),
            nb_echecs=r.result.get("unexpected_count", 0),
            run_id=run_id, date_chargement=date_chargement, outil="Great Expectations"))
    en_echec = [l["regle_id"] for l in lignes if l["statut"] != "ok"]
    log.info("Contrôles d'entrée : %d règles, en échec : %s", len(lignes), ", ".join(en_echec) or "aucune")
    return lignes
