-- Grain : une ligne par unité légale (dimension partagée avec le futur fait des ouvertures)
select
    siren,
    nom_affiche,
    categorie_juridique,
    est_entrepreneur_individuel,
    etat_administratif,
    statut_diffusion,
    date_creation
from {{ ref('mart_unites_legales') }}