

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



