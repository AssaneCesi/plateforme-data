-- Unités légales du dernier chargement, typées et dédoublonnées.
-- Les marqueurs [ND] (données non diffusées) deviennent de vrais NULL.

with dernier_chargement as (
    select *
    from {{ source('raw', 'unites_legales') }}
    where date_chargement = (select max(date_chargement) from {{ source('raw', 'unites_legales') }})
),

dedoublonnes as (
    select
        *,
        row_number() over (
            partition by siren
            order by try_cast(date_dernier_traitement as timestamp) desc nulls last
        ) as rang
    from dernier_chargement
)

select
    siren,
    statut_diffusion,
    etat_administratif,
    try_cast(date_creation as date)                 as date_creation,
    try_cast(date_dernier_traitement as timestamp)  as date_dernier_traitement,
    nullif(trim(denomination), '')                  as denomination,
    nullif(nullif(trim(nom), ''), '[ND]')           as nom,
    nullif(nullif(trim(prenom1), ''), '[ND]')       as prenom1,
    categorie_juridique,
    categorie_juridique = '1000'                    as est_entrepreneur_individuel,
    nullif(trim(activite_principale), '')           as code_ape,
    nic_siege,
    date_chargement
from dedoublonnes
where rang = 1
