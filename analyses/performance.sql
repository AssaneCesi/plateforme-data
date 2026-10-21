

/*
Performance : EXPLAIN avant et après indexMoyen
Sur PostgreSQL : (1) lance EXPLAIN ANALYZE SELECT * 
FROM etablissements WHERE siren = '552100554'; et note le type de 
parcours et le temps. (2) Crée un index sur siren, lance ANALYZE 
etablissements;, relance. (3) Remplace le filtre par 
WHERE LEFT(siret, 9) = '552100554'. (4) Essaie un index sur 
etat_administratif avec WHERE etat_administratif = 'A'. 
Explique chaque résultat.
*/

/* Total Time: 0.0594s, scan sequentiel*/
USE entrepot;

DROP INDEX IF EXISTS raw.idx_unites_legales_siren;

CREATE INDEX idx_unites_legales_siren
ON raw.unites_legales (siren);

ANALYZE raw.unites_legales;

EXPLAIN ANALYZE

SELECT * 
FROM raw.unites_legales
WHERE etat_administratif  = 'A'; 

/*
SELECT * 
FROM raw.etablissements
WHERE siren = '552100554'; */



