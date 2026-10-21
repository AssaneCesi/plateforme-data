# Scorecard qualité

Chaque exécution écrit trois fichiers dans `exports/` :

- `dq_scores.csv` : score par dimension et score global, pour chaque run (courbe de tendance) ;
- `dq_resultats.csv` : une ligne par règle et par run (détail, drill-down) ;
- `chargements.csv` : volumes chargés par jour (suivi des dérives).

Pour avoir une tendance dès le début : `python pipeline.py historique --jours 7`.

## Power BI (ou Metabase)
1. Obtenir les données > Texte/CSV > `exports/dq_scores.csv`, puis `dq_resultats.csv`.
2. Page 1 : score global du dernier run, score par dimension, courbe du score global dans le temps.
3. Page 2 : règles triées par nombre d'échecs, avec criticité et seuil.
4. Règle d'or : le scorecard se lit en dix secondes, et chaque chiffre se décompose.

Dépose ici les captures (`scorecard.png`) utilisées dans le README.
