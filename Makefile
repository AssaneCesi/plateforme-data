PY ?= python

.PHONY: install echantillon run reel telecharger historique rapport catalogue docs test nettoyer

install:
	$(PY) -m pip install -r requirements.txt

echantillon:
	$(PY) pipeline.py echantillon

run:
	$(PY) pipeline.py run

telecharger:
	$(PY) pipeline.py telecharger

reel:
	$(PY) pipeline.py run --source reel

historique:
	$(PY) pipeline.py historique --jours 7

rapport:
	$(PY) pipeline.py rapport

catalogue:
	$(PY) pipeline.py catalogue

docs:
	$(PY) pipeline.py docs

test:
	$(PY) -m pytest -q

nettoyer:
	rm -rf data/entrepot.duckdb exports dbt/target dbt/logs
