-- Unités légales prêtes à l'usage.
-- RGPD : le nom d'un entrepreneur individuel n'est exposé que s'il est diffusible (statut O).
-- Minimisation : les prénoms ne sont pas repris, ils ne servent à aucun usage du projet.

select
    siren,
    categorie_juridique,
    est_entrepreneur_individuel,
    etat_administratif,
    date_creation,
    code_ape,
    statut_diffusion,
    case
        when not est_entrepreneur_individuel then denomination
        when statut_diffusion = 'O' then nom
        else null
    end as nom_affiche
from {{ ref('stg_unites_legales') }}
