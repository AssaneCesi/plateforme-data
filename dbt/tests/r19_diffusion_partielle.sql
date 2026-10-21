{{ config(
    severity='error',
    meta={
        'regle_id': 'R19',
        'denominateur_modele': 'mart_unites_legales',
        'denominateur_filtre': "statut_diffusion = 'P'"
    }
) }}

-- R19 (bloquante) : aucune donnée nominative exposée pour un entrepreneur individuel
-- en diffusion partielle, et aucun marqueur [ND] ne doit atteindre les marts.
-- Si ce test échoue, dbt ne publie pas la suite : c'est voulu.

select siren, statut_diffusion, nom_affiche
from {{ ref('mart_unites_legales') }}
where (statut_diffusion = 'P' and est_entrepreneur_individuel and nom_affiche is not null)
   or nom_affiche like '%[ND]%'
