import sys
import duckdb

requete = open(sys.argv[1], encoding="utf-8").read()
with duckdb.connect("data/bac_a_sable.duckdb", read_only=False) as con:
    print(con.sql(requete))