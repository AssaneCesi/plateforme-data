# Orchestration (phase 2)

Exercice A1 du hub. Aujourd'hui, `python pipeline.py run` enchaîne tout dans un seul
processus. L'objectif de la phase 2 est d'en faire un DAG Airflow quotidien :

1. `charger` : ingestion du fichier du jour (idempotente, clé = date logique du run)
2. `controler_entree` : Great Expectations sur le brut
3. `dbt_build` : modèles et tests
4. `collecter` : résultats dbt vers `dq.resultats`
5. `alerter` : si une règle bloquante dépasse son seuil, ou si le volume dérive (S9)

Première étape : découper `plateforme/execution.py` en fonctions appelables une par
une avec un `run_id` commun. Attention, Airflow 3 est sorti en 2025 : vérifie la version
de chaque tutoriel que tu suis.
