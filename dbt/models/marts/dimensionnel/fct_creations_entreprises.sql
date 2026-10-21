-- Grain : une ligne par unité légale créée (un SIREN),
-- dont le siège fait partie du périmètre chargé
with unites as (
    select siren, date_creation, code_ape, nic_siege, date_chargement
    from {{ ref('stg_unites_legales') }}
),

sieges as (
    select siret, code_commune, code_postal
    from {{ ref('stg_etablissements') }}
    where est_siege
)

select
    u.siren,
    u.date_creation,
    coalesce(l.cle_localisation, 'INCONNUE') as cle_localisation,
    coalesce(a.cle_activite, 'INCONNU')      as cle_activite,
    1                                        as nb_creations,
    u.date_chargement
from unites as u
join sieges as s
  on s.siret = u.siren || u.nic_siege
left join {{ ref('dim_localisation') }} as l
  on  l.code_commune = s.code_commune
  and l.code_postal is not distinct from s.code_postal
left join {{ ref('dim_activite') }} as a
  on a.code_ape = u.code_ape