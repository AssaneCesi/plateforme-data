select
    e.siret,
    e.siren,
    e.est_siege,
    e.etat_administratif,
    e.date_creation,
    e.code_commune,
    c.nom_commune,
    c.code_departement,
    e.code_postal,
    e.code_ape,
    ul.categorie_juridique
from {{ ref('stg_etablissements') }} as e
left join {{ ref('stg_unites_legales') }} as ul using (siren)
left join {{ ref('stg_communes') }} as c using (code_commune)
