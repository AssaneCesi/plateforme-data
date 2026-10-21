-- Grain : une ligne par couple (commune, code postal) observé chez les sièges,
-- pour les communes connues du référentiel, plus un membre inconnu
with couples as (
    select distinct code_commune, code_postal
    from {{ ref('stg_etablissements') }}
    where est_siege and code_commune is not null
)

select
    c.code_commune || '-' || coalesce(c.code_postal, 'SANS-CP') as cle_localisation,
    c.code_commune,
    c.code_postal,
    r.nom_commune,
    r.code_departement
from couples as c
join {{ ref('stg_communes') }} as r on r.code_commune = c.code_commune

union all

select 'INCONNUE', null, null, 'Localisation absente du référentiel', null