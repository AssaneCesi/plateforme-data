-- Établissements du dernier chargement, typés, conformes et dédoublonnés.

with dernier_chargement as (
    select *
    from {{ source('raw', 'etablissements') }}
    where date_chargement = (select max(date_chargement) from {{ source('raw', 'etablissements') }})
),

conformes as (
    -- R01 et R03 : les SIRET absents ou mal formés partent en quarantaine
    -- (modèle quarantaine_etablissements) au lieu de polluer la suite.
    select *
    from dernier_chargement
    where siret is not null
      and regexp_full_match(siret, '[0-9]{14}')
),

dedoublonnes as (
    -- R02 : règle de survie = la version la plus récemment traitée par l'Insee.
    select
        *,
        row_number() over (
            partition by siret
            order by try_cast(date_dernier_traitement as timestamp) desc nulls last
        ) as rang
    from conformes
)

select
    siret,
    left(siret, 9)                                              as siren,
    substr(siret, 10, 5)                                        as nic,
    lower(trim(etablissement_siege)) in ('true', 't', '1', 'oui') as est_siege,
    etat_administratif,
    try_cast(date_creation as date)                             as date_creation,
    try_cast(date_debut as date)                                as date_debut_periode,
    try_cast(date_dernier_traitement as timestamp)              as date_dernier_traitement,
    nullif(trim(code_postal), '')                               as code_postal,
    nullif(trim(code_commune), '')                              as code_commune,
    libelle_commune,
    nullif(trim(activite_principale), '')                       as code_ape,
    activite_principale_naf25                                   as code_ape_naf25,
    statut_diffusion,
    date_chargement
from dedoublonnes
where rang = 1
