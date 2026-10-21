# Glossaire métier

Chaque terme a une définition compréhensible sans SQL, une règle de calcul, une source,
un propriétaire et un steward. Exercice Gv1 du hub : complète les quatre termes restants,
puis reporte-les dans le catalogue (OpenMetadata ou DataHub) en phase 2.

## Entreprise active

| | |
|---|---|
| Définition | Unité légale dont l'état administratif est « actif » à la date d'observation. |
| Règle de calcul | `etat_administratif = 'A'` dans `stg_unites_legales`, au dernier chargement. |
| Source | SIRENE (Insee), fichier stock des unités légales |
| Propriétaire | [rôle responsable du référentiel entreprises] |
| Steward | [toi] |
| Termes liés | Établissement actif, Cessation |
| Point d'attention | « Active » dans le répertoire ne garantit pas une activité économique réelle. |

## Établissement
| | | |
|---|---|---|
| Définition | Etablissement d'une unité légales identifié par son  |
Règle de calcul | siret = siren + nic, chaque siret est unique et non nul|
Source | SIRENE (Insee), fichier stock des établissements | 
Termes liés| Activité, Adresse, Siège	|
## Siège
#### à choisir : Localisation du siège

| | | |
|---|---|---|
| Définition | Avantage | Limite |
Commune du siège | Simple, disponible pour chaque entreprise |	Faussée par la domiciliation |
Commune du premier établissement ouvert | Plus proche du lieu de démarrage | Souvent le siège lui-même|
Commune qui compte le plus d'établissements | Reflète l'activité réelle	|Arbitraire en cas d'égalité, change dans le temps |


## Date de création
[à compléter : de l'unité légale ou de l'établissement ? les deux existent]
| | | |
|---|---|---|
| Définition | unité légale | établissement |
| Définition |Date de première immatriculation de l'ul, distincte de la date de débu d'activité| Date d'enregistrement au repertoire sirene a l'INSEE et d'attribution de numero siret|


## Entrepreneur individuel
[à compléter : catégorie juridique 1000, données personnelles, statut de diffusion]
