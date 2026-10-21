import pandas as pd
import great_expectations as gx
import duckdb
from great_expectations.data_context.types.base import ProgressBarsConfig 

# 1. Simuler quelques données SIRENE

with duckdb.connect("data/entrepot.duckdb", read_only=True) as con:
    df = con.execute("""
        SELECT
            siret,
            code_postal,
            etat_administratif
        FROM raw.etablissements
        LIMIT 1000
    """).df()

df1 = pd.DataFrame({
    "siret": [
        "12345678900012",
        "12345678900013",
        None,
    ],
    "code_postal": [
        "75056",
        "691238",
        "33063",
    ],
    "etat_administratif": [
        "C",
        "A",
        "F",
    ],
})


context = gx.get_context(mode="ephemeral")
context.variables.progress_bars = ProgressBarsConfig(globally=False)

data_source = context.data_sources.add_pandas("source")
data_asset = data_source.add_dataframe_asset(name ="etablissements")
batch_definition =  (data_asset.add_batch_definition_whole_dataframe("lot_complet"))
batch = batch_definition.get_batch(batch_parameters={"dataframe":df})

expectations = [
    gx.expectations.ExpectColumnValuesToNotBeNull(column="siret"),
    gx.expectations.ExpectColumnValuesToBeUnique(column="siret"),
    gx.expectations.ExpectColumnValuesToMatchRegex(column="siret", regex=r"^[0-9]{14}$"),
    gx.expectations.ExpectColumnValuesToMatchRegex(column="code_postal", regex=r"^[0-9]{5}$", mostly=0.99),
    gx.expectations.ExpectColumnValuesToBeInSet(column="etat_administratif", value_set=["A","F"])
]

suite  = context.suites.add(gx.ExpectationSuite(name="exercie_G1"))

for expectation in expectations:
    suite.add_expectation(expectation)

result  = batch.validate(suite)

for r in result.results:
    cfg = r.expectation_config
    print(cfg.type, cfg.kwargs.get("column"),
          "ok" if r.success else "ÉCHEC",
          r.result.get("unexpected_count"))


