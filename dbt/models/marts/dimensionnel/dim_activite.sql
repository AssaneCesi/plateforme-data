-- Grain : une ligne par code APE d'unité légale, plus un membre inconnu
select distinct
    code_ape          as cle_activite,
    code_ape,
    left(code_ape, 2) as division
from {{ ref('stg_unites_legales') }}
where code_ape is not null

union all

select 'INCONNU', null, null