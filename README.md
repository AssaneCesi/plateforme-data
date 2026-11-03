# Plateforme de données d'entreprises, qualité intégrée

> Pipeline de bout en bout sur les données publiques d'entreprises françaises
> (SIRENE, Insee), avec la qualité et la gouvernance intégrées à chaque étape.

![Scorecard qualité](dashboards/scorecard.png)

## En 30 secondes
- [N] millions de lignes, [N] départements (ou tout le territoire en v2)
- Ingestion pilotée par contrats, chargements idempotents, modèle en étoile
- [N] règles de qualité sur [N] dimensions, quarantaine, score historisé
- Orchestration Airflow, CI, [Spark sur Databricks en v2]

## Deux façons de lire ce projet
| Data engineering | Qualité et gouvernance |
|---|---|
| Contrats, incrémental, modèle en étoile | Règles, seuils, quarantaine |
| Orchestration, rejeu, backfill | Score par dimension, historisé |
| Tests, CI, Docker, [Spark] | Glossaire, lignage, RGPD, incident |

## Architecture
[schéma de la version en cours]

## Ce que les données m'ont appris
Trois constats chiffrés : [1], [2], [3].

## Choix techniques et compromis
- DuckDB puis Spark : [ta note de dimensionnement, en 3 lignes]
- Contrôles à l'entrée (GX) et dans les modèles (dbt) : [pourquoi]
- Quarantaine plutôt que correction silencieuse : [pourquoi]
- Ce que j'ai volontairement laissé de côté : [..]

## Incident simulé
[5 lignes : ce qui s'est passé, comment c'est détecté, ce qui a été bloqué,
comment on a rejoué, quelle règle l'empêche désormais.]

## Lancer le projet
```bash
pip install -r requirements.txt
python pipeline.py echantillon && python pipeline.py run
```

## Limites et suite
- [limite 1]
- [prochaine étape]
