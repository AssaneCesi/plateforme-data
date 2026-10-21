# Catalogue des règles de qualité

Fichier généré par `python pipeline.py catalogue` à partir de `qualite/regles.yml`.
Ne pas modifier à la main : modifie le YAML, puis régénère.

Seuil : taux d'échec toléré. Criticité : poids 3 (bloquante), 2 (majeure), 1 (mineure) dans le score.

| Id | Règle | Dimension | Criticité | Seuil | Outil | Objet | État |
|----|-------|-----------|-----------|-------|-------|-------|------|
| R01 | SIRET renseigné | Complétude | bloquante | 0.1 % | GX, à l'entrée | `raw.etablissements` | implémentée |
| R02 | SIRET unique dans le chargement | Unicité | majeure | 0 | GX, à l'entrée ; règle de survie en staging | `raw.etablissements` | implémentée |
| R03 | SIRET composé de 14 chiffres | Validité | bloquante | 0.1 % | GX, à l'entrée ; lignes en quarantaine | `raw.etablissements` | implémentée |
| R04 | Clé de contrôle du SIRET (Luhn, exception La Poste) | Validité | majeure | 0 | dbt test personnalisé | `stg_etablissements` | implémentée |
| R05 | Le SIREN de l'établissement existe dans les unités légales | Intégrité | majeure | 0 | dbt relationships | `stg_etablissements` | implémentée |
| R06 | Code commune présent dans le référentiel géographique | Validité | majeure | 0 | dbt relationships | `stg_etablissements` | implémentée |
| R07 | Code APE au format NAF (99.99X) | Validité | majeure | 0 | dbt test personnalisé | `stg_etablissements` | implémentée |
| R08 | Code postal à 5 chiffres | Validité | mineure | 1 % | GX, seuil 99 % | `raw.etablissements` | implémentée |
| R09 | État administratif A ou F | Validité | majeure | 0 | dbt test personnalisé | `stg_etablissements` | implémentée |
| R10 | Date de création non future | Cohérence | majeure | 0 | dbt test personnalisé | `stg_etablissements` | implémentée |
| R11 | Établissement fermé avec une date de début de période renseignée | Cohérence | mineure | 0 | dbt | `stg_etablissements` | à faire (exercice S4) |
| R12 | Un seul siège actif par unité légale active | Cohérence | mineure | 0.5 % | dbt test singulier (à valider avec le métier) | `stg_unites_legales` | implémentée |
| R13 | Dénomination renseignée pour les personnes morales | Complétude | majeure | 0 | dbt not_null conditionnel | `stg_unites_legales` | implémentée |
| R14 | Adresse complète pour les établissements actifs | Complétude | mineure | 2 % | dbt | `stg_etablissements` | à faire (exercice S1) |
| R15 | Doublons potentiels (nom normalisé et code postal) | Unicité | mineure | 0 | SQL | `stg_unites_legales` | à faire (exercice M1) |
| R16 | Dénomination identique entre SIRENE et l'API Recherche d'entreprises | Exactitude | mineure | 1 % | Python + dbt | `stg_unites_legales` | à faire (exercice phase 2) |
| R17 | Volume du chargement dans ±3 écarts-types des 7 précédents | Fraîcheur et volume | majeure | 0 | SQL, orchestrateur | `raw.etablissements` | à faire (exercice S9) |
| R18 | Dernier chargement plus récent que le seuil du contrat | Fraîcheur | bloquante | 0 | dbt source freshness | `raw.etablissements` | à faire (exercice D3) |
| R19 | Diffusion partielle respectée : aucune donnée nominative exposée | Conformité | bloquante | 0 | dbt test singulier, bloquant | `mart_unites_legales` | implémentée |
| R20 | Aucune unité repassée de cessée à active sans explication | Cohérence | mineure | 0 | dbt snapshot | `stg_unites_legales` | à faire (exercice D4) |
