select
    code             as code_commune,
    nom              as nom_commune,
    code_departement
from {{ source('raw', 'communes') }}
