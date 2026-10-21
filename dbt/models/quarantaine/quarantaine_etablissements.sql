-- Lignes du dernier chargement écartées à l'entrée (R01, R03).
-- Conservées pour analyse et pour être signalées au producteur : on ne corrige pas en silence.

select
    *,
    case
        when siret is null then 'R01 : SIRET absent'
        else 'R03 : SIRET mal formé'
    end as motif_quarantaine
from {{ source('raw', 'etablissements') }}
where date_chargement = (select max(date_chargement) from {{ source('raw', 'etablissements') }})
  and (siret is null or not regexp_full_match(siret, '[0-9]{14}'))
