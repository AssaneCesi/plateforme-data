/*Liste les établissements incohérents avec le motif : 
fermé sans date de fermeture, actif avec une date de fermeture, 
fermé avant d'être créé, créé dans le futur.*/


SHOW ALL TABLES;



/*SELECT siren, etat_administratif, date_creation, date_fermeture,
    CASE WHEN etat_administratif = 'C' AND date_fermeture IS NULL THEN 'True'  ELSE 'False' END AS incoherent_fermeture,
    CASE WHEN etat_administratif = 'A' AND date_fermeture IS NOT NULL THEN 'True' ELSE 'False' END AS incoherent_ouverture,
    CASE WHEN date_creation < date_fermeture THEN 'True' ELSE 'False' END AS incoherent_création,
    CASE WHEN date_creation > CAST(GETDATE() AS DATE) THEN 'True' ELSE 'False' END AS incoherent_date_creation
FROM raw.unites_legales 
LIMIT 5;*/