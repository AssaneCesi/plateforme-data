# Journal du projet

Cinq minutes par jour : ce que j'ai fait, ce que j'ai appris, ce qui m'a surpris.
C'est la matière première des posts LinkedIn et des réponses en entretien.

## [30/09/2026]
- Fait : Installé le kit puis lancé un run (run du pipeline complet + rapport qualité) et un test (tests, dont le pipeline de bout en bout)sur l'échantillon. =>  On utilmise dbt ou GX pour appliquer différentes règles de qualité données.
- Appris : 
- Surpris par : Je me demande en quoi consiste les tests, comment les metriques sont définies pour le rapport qualité et quelles technos et methodes sont utilisées pour run le pipeline et faire les tests.

## [07/10/2026]
- Fait :
    - Telechargement des vraies données et run sur ces dernières. Relever des volumes (envrion 3Go) et temps d'execution(environ 17min). (Voir run Run 20261007_165712 pour les rapports) qualité etc.
    - Profilage des données en une requete:
        - COUNT(colonne) ignore les NULL, COUNT(*) non. Le ratio des deux donne le taux de remplissage.
        - NULLIF(TRIM(colonne),'') pour ne pas oublier les valeurs non nulles mais pas remplies
- Appris : 
    - faire des requetes sql dans le terminal grace au cli duckdb (winget install DuckDB.cli) ou fichier .sql + fichier executer .py (en cmd: python executer.py profilage.sql) ou jupyter.

    - Profilage des donneés. Récupérer des informations sur les données et les analyser en utilisant les 7 dimensions de la qualité des données et une idée de l'objectif final afin de définir des règles et des seuil. 

- Surpris par :Score de qualité global de 98.68%

## [09/10/2026]:

- Fait :
    - dédoubloannage avec ROW_NUMBER()
    - validité: Clé de Luhn
    -  cohérence états et dates
- Appris :
    - generate_series()
    - UDF python pour SQL plus simple mais pas souhaitable car surchagre d'appels apr lignes. => Apprendre à gere ce gerne de cas avec SQL uniquement
    -  GETDATE() pour récupérer la date d'ajourd'hui avec l'heure
- Surpris :Il n'y a pas de colonne date_fermeture

## [12/10/2026]:

- Fait : 
    - EXPLAIN ANALYZE sur requete.=> Total Time: 0.0343s, scan sequentiel
    - CREATE INDEX ON... sur requete.=> Total Time: 0.0104s, Index Scan
    - Avec l'index le filtre WHERE LEFT(siret, 9) = '552100554' était aussi rapide que sans index=> Les index ne reconnaissent pas les fonctions.
    - Test filtre sur colonne a deux valeurs (etat_administratif) avec index=>Sequential Scan effectué à la place de index scan car deux valeurs uniquement donc la machine a trouvé sequentieal scan moins couteux. Total Time: 0.191s 
- Appris : 
    - Définir sur l'exeecuter si read-only ou autre (important pour CREATE)
    - USE entrepot pour s'assurer de la source de données.
    - DROP INDEX IF EXISTS idx_etablissements_siren pour supprimer un index
- Surpris :
    - le scan sequentiel allait plus vite que Index Scan a force de repetition grace au cache Windows


## [14/10/2026]:

- Fait : 
    - Grain de la table (table de faits sur les créations d'entreprise): une ligne = une creation(creation_id, , siren(PK,FK))
    - Dimensions: entreprise, activité, localisation"celle du siège"(siren,code_postal, code_commune,libelle_commune)
    - 

- Appris : 
    - le modele en étoile se fait avec les données du stg pas raw. La couche raw contient tous les chargements successifs, des doublons, des SIRET invalides, et tout y est en texte. Le staging a déjà réglé tout ça.Le modele en étoile se fait dans le marts ou dans la couche gold car fait pour l'analyse.
    - Mettre une mesure dans la table des faits (ex: nb_créeation, avec ici chaque siren est une création)
    - Bien réviser les définitions métier de chaque attribut
    - Créer un memebre inconnu dans une dimensions afin la jointure avec sa table de fait n'ommete pas de ligne si celle ci n'est pas renseigné dans la dim

- Surpris :
    - Il faut prendre en compte k'historisation(par exemeple une entreprise qui change de catégorie juridique, il faut que l'ancienne puisse etre stocké(SCD type 1 ou 2))
    - il faut bien définir le grain de chaque dimension. 
    - Les définitions métier de chaque attribut compte pour beacoup:
        => 458 000 sièges introuvables : un problème de périmètre, pas de qualité
        Cela représente 12 % des unités légales. Ce sont des entreprises qui ont au moins un établissement dans tes départements, mais dont le siège est ailleurs. Par exemple, une enseigne nationale qui a une boutique à Paris et son siège à Lyon : ton chargement l'embarque grâce à la boutique, mais le siège n'est pas dans tes fichiers. 
        12 % des sièges semblaient manquants. En réalité, c'était le périmètre de chargement : j'ai choisi de définir le fait par la localisation du siège, plutôt que de masquer ces lignes dans un membre inconnu. 

## [14/10/2026]:

- Fait : 
    - 20 regles de qualité de donnée
- Appris :
    - GX ou dbt : comment répartir tes règles
        GX, à l'entrée : ce qui se vérifie sur le brut du dernier chargement, avant toute transformation. Formats, présence, unicité dans le lot, valeurs autorisées, volume. C'est la frontière avec le producteur.
        dbt, dans les modèles : ce qui demande des données typées, nettoyées ou croisées. Relations entre tables, cohérence entre colonnes, règles métier (un siège actif par entreprise, diffusion partielle). Les règles simples sur une colonne se déclarent dans un .yml avec config: meta: {regle_id: ...}, les règles plus complexes en SQL dans dbt/tests/.
        Une règle sur les doublons ou les formats reçus se mesure donc en raw : en staging, elle passerait toujours, puisque le problème y a déjà été traité. Une règle qui compare des dates ou relie deux tables se mesure en staging : en raw, tout est en texte et tous les chargements successifs sont mélangés.
- Surpris :

## [16/10/2026]:

- Fait : 
    - Créer une table etablissements_courant dans le dossier intermdeidare dans dbt. La table fais des mises à jours incrémentielles avec un merge sur les siret. Test d'unicité sur la variable siret dans le yaml.
    - L'operation est idempotante grace à la condition sur la date.
- Appris :
    - Commandes build dbt: dbt build --select etablissements_courant --profiles-dir .=>  Le modèle et ses tests
    - Si un etb est supp du lot de chargment pour x ou y raison, ce dernier ne le sera pas de la table. En revanche, ces etb seront identifié grace a la colonne date_derniere_vue qui note les sirets présents dans le dernier lot. Couplé à R17 cela nous permet d'avoir des informations si des sirets manquent sans prendre le risque de les supprimer automatiquement.
    C'est possible ici parce que le fichier SIRENE est un stock complet : tous les établissements y sont à chaque fois, donc on peut comparer la liste complète des SIRET d'un lot à l'autre. Avec une source qui ne livre que les modifications, on ne pourrait pas voir les disparitions : il faudrait du CDC. => à implémnter en cas normal, mon code ne fait rien de ceci
- Surpris :

## [16/10/2026]:

- Fait : 
    - Créer une validation de df provenant de raw.etb de DuckDB avec GX.
    - mostly=0.99 est ma première notion de seuil : une règle peut tolérer un faible taux d'échec sur les codes postaux car il y a des exceptions avec la poste par exemple.
- Appris :
    - Configuration sur GX (voir doc Drive) 
- Surpris :

## [18/10/2026]:

- Fait :
    - Redaction de data contracts pour l'ingestion des etb.
- Appris :
    - ODCS (Open Data Contract Standard) qui est un accord entre celui qui produit al donnée(ici la base sirene) et celui qui l'utilise. Il prévient les changements de sources abruptes qui casseent tout le pipeline en aval. Ces règels sont ensuite vérifiées par GX ou dbt. Les SLA font partie du data contract et donnent des précisions sur quand à et quel point je peux compter sur les données que je reçois.
    - L'historique n'est pas noté en ODCS dans le data contract, il est tenu à part dans un changelog.md ou customProperties. Ici nous avond décidé de le mettre dans le data contract car plus lisible.
- Surpris :
    - Le data contract estt un engagement du producteur envers le consomateur de la donnée.(Ona ici un contrat consommateur car l'INSEE ne promet rien)


## [19/10/2026]:

- Fait :
    - Dédoublonnage flou avec dbt dans intérmediare. ... puis approche dterministe avec jaro_winkler(cette approche ne couvre que les cas prévus, bien ici car on sait à peux pret quelles erreurs rencontrer).
- Appris :
    - MDM et RDM
- Surpris :
    - Attention pour jaro winkler avec jointure bien definir le perimetre(on va comparer ici deux entreprises au siren different mais sans argument suppplémentaire on compare chaque siren(longueur de la table - 1)). Il nous faut donc bloquer avec le CP.

## [29/10/2026]:

- Fait :
    - Integration de airflow via WSL2 sur ma machine:
        => on clone le projet dans ~/plateforme-donnees-entreprises et un crée un nouveau venv
        => on installe airflow
        => on crée un dossier dag avec un fichier python avec un dag minimal

- Appris :
    - ORCHESTRATION AVEC AIRFLOW:
         => découper les étapes du pipeline (télécharger, valider le brut, transformer, profiler, charger). Les petites données (metadonnées) passent par Xcom et les grosses doivent etre stockées dans des fichiers parquet par exemple.Chaque tache recois un chemin
         => attention conflits dépendances avec airflow et mes autres dépendances (un conteneur par tache idéalement)
         =>  Dans airflow les imports son faits dans les taches pour pas ralentir le scheduler
- Surpris :