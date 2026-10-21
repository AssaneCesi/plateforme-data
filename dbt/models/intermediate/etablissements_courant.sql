{{
    config(
        materialized='incremental',
        unique_key='siret',
        incremental_strategy='merge',
        merge_update_columns=[
            'code_commune',
            'etat_administratif',
            'date_dernier_traitement',
            'date_derniere_mise_a_jour'
        ]
    )
}}

select
    siret,
    code_commune,
    etat_administratif,
    date_dernier_traitement,

    current_timestamp as date_premiere_apparition,
    current_timestamp as date_derniere_mise_a_jour
from {{ref('stg_etablissements')}}

{% if is_incremental() %}
where date_dernier_traitement >= (
    select coalesce(max(date_dernier_traitement), cast('1900-01-01' as timestamp))
    from {{ this }}
)

{% endif %}