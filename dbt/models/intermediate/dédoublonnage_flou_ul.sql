-- Repérer des SIREN différents qui semblent désigner la même entreprise ---
-- Qu'est ce qui pourrait différencier deux denomination?(toute ponctuation et carac special, majuscules, rajout du jaro winkler)
-- § denominnation, nom et prenom1 ont déja été TRIM
-- étapes: 1 normalisation des noms(majuscules, ponctuations, retrait statut_juridique ),
--         2 detection des doublons après normalisation avec jaro winkler, 


with normalise as( 
select u.siren siren,
    u.denomination,
    REGEXP_REPLACE(--- retirer les formes juridiques
        REGEXP_REPLACE(--- remplacer toutes ponctuations par un espace
        replace(--- remplacer les points et &
            replace(coalesce(UPPER(u.denomination),UPPER(u.nom ||' '|| u.prenom1)), '.','')
                ,'&','ET'),
            '[^A-Z0-9]+', ' ', 'g'),
     '\b(SARL|SASU|SAS|SA|EURL|SCI|SNC|SELARL|SCOP|SCM|SCP|GIE|EARL|GAEC|SOCIETE|STE)\b', ' ', 'g') denomination_norm,
    e.code_postal code_postal,
    u.nic_siege nic_siege
from {{ref("stg_unites_legales")}} u
left join {{ref("stg_etablissements")}} e
    on u.siren = e.siren 
where denomination_norm IS NOT NULL
),

paires as (
    select
        na.siren AS siren_1,
        na.denomination AS denomination_1,
        nb.siren AS siren_2,
        nb.denomination AS denomination_2,
        JARO_WINKLER_SIMILARITY(
            na.denomination_norm,
            nb.denomination_norm
        ) AS similarite
    from normalise na
    join normalise nb
        on na.siren<nb.siren
        and na.code_postal = nb.code_postal
)

SELECT *
FROM paires
WHERE similarite >= 0.90
ORDER BY similarite DESC
LIMIT 100;

-------------------------------------------

with normalise as( 
select u.siren siren,
    u.denomination,
    REGEXP_REPLACE(
        REGEXP_REPLACE(
        replace(
            replace(coalesce(UPPER(u.denomination),UPPER(u.nom ||' '|| u.prenom1)), '.','')
                ,'&','ET'),
            '[^A-Z0-9]+', ' ', 'g'),
     '\b(SARL|SASU|SAS|SA|EURL|SCI|SNC|SELARL|SCOP|SCM|SCP|GIE|EARL|GAEC|SOCIETE|STE)\b', ' ', 'g') denomination_norm,
    e.code_postal code_postal,
    u.nic_siege nic_siege
from main.stg_unites_legales u
left join main.stg_etablissements e
    on u.siren = e.siren 
where denomination_norm IS NOT NULL
),

paires as (
    select
        na.siren AS siren_1,
        na.denomination AS denomination_1,
        nb.siren AS siren_2,
        nb.denomination AS denomination_2,
        JARO_WINKLER_SIMILARITY(
            na.denomination_norm,
            nb.denomination_norm
        ) AS similarite
    from normalise na
    join normalise nb
        on na.siren<nb.siren
        and na.code_postal = nb.code_postal
)

SELECT *
FROM paires
WHERE similarite >= 0.90
ORDER BY similarite DESC
LIMIT 100;