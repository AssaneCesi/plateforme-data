/*Un SIREN valide a 9 chiffres et respecte l'algorithme de Luhn : 
en partant de la droite, on double un chiffre sur deux, on retire
 9 si le double dépasse 9, et la somme totale doit être un multiple
  de 10.
 Écris la requête qui renvoie chaque SIREN et un booléen luhn_ok.*/
EXPLAIN ANALYZE
WITH chiffres AS (
  SELECT u.siren,
         g.i,
         CAST(SUBSTRING(u.siren, g.i, 1) AS INTEGER) AS d
  FROM raw.unites_legales u
  CROSS JOIN generate_series(1, 9) AS g(i)
  WHERE u.siren ~ '^[0-9]{9}$'
)
SELECT siren,
       SUM(CASE WHEN i % 2 = 0
                THEN CASE WHEN d * 2 > 9 THEN d * 2 - 9 ELSE d * 2 END
                ELSE d END) % 10 = 0 AS luhn_ok
FROM chiffres
GROUP BY siren;