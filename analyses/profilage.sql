/* Profilage en une requête */

SELECT COUNT(*) nb_de_lignes,
    COUNT(DISTINCT siren) nb_siren_differents,
    COUNT(DISTINCT siret) nb_siret_differents, 
    COUNT(NULLIF(TRIM(code_postal), '')) as nb_code_postal_non_vides,
    ROUND(100.0 * COUNT(NULLIF(TRIM(code_postal), ''))
          / NULLIF(COUNT(*), 0), 2)                 AS taux_remplissage_code_postal,
    ROUND(100.0 * COUNT(NULLIF(TRIM(code_commune), ''))
          / NULLIF(COUNT(*), 0), 2)                 AS taux_remplissage_code_commune,
    MIN(date_creation) date_creation_min,
    MAX(date_creation) date_creation_max,
    COUNT(DISTINCT etat_administratif) nb_etat_administratif_differents
FROM  raw.etablissements
;