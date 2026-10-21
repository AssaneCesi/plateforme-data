import sys
import duckdb

requete = open(sys.argv[1], encoding="utf-8").read()
with duckdb.connect("data/entrepot.duckdb", read_only=True) as con:
    print(con.sql(requete))