/* Dédoublonnage : etablissements_raw contient plusieurs versions 
d'un même SIRET (un par chargement). 
Ne garde que la plus récente selon date_dernier_traitement. */


SELECT *
FROM (
SELECT ROW_NUMBER() OVER (PARTITION BY siret ORDER BY date_dernier_traitement DESC) AS rang,*
FROM raw.etablissements
) f
WHERE rang = 1;
