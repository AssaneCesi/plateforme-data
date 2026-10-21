# Glossaire métier

Chaque terme a une définition compréhensible sans SQL, une règle de calcul, une source,
un propriétaire et un steward. À reporter dans le catalogue (OpenMetadata ou DataHub) en phase 2.

| Terme | Définition courte |
|---|---|
| [Entreprise active](#entreprise-active) | Unité légale à l'état « actif » au dernier chargement |
| [Établissement](#établissement) | Lieu où s'exerce l'activité d'une unité légale |
| [Siège](#siège) | Établissement qui porte l'adresse juridique de l'unité légale |
| [Date de création](#date-de-création) | Date de création déclarée, de l'unité légale ou de l'établissement |
| [Entrepreneur individuel](#entrepreneur-individuel) | Personne physique exerçant en son nom propre |

---

## Entreprise active

| Rubrique | Contenu |
|---|---|
| Définition | Unité légale dont l'état administratif est « actif » à la date d'observation. |
| Règle de calcul | `etat_administratif = 'A'` dans `stg_unites_legales`, au dernier chargement. |
| Source | SIRENE (Insee), fichier stock des unités légales |
| Règles qualité liées | `dans_liste` : valeurs autorisées `A`, `C` |
| Propriétaire | Responsable du référentiel entreprises |
| Steward | Data steward référentiel entreprises |
| Termes liés | Établissement, Cessation |
| Point d'attention | « Active » dans le répertoire ne garantit pas une activité économique réelle : une entreprise sans activité peut rester active tant qu'elle n'a pas déclaré sa cessation. |

---

## Établissement

| Rubrique | Contenu |
|---|---|
| Définition | Lieu géographique où s'exerce tout ou partie de l'activité d'une unité légale. Une unité légale a un ou plusieurs établissements, dont un seul siège. |
| Règle de calcul | `siret` = `siren` (9 chiffres) + `nic` (5 chiffres) ; colonne `stg_etablissements.siret`. |
| Source | SIRENE (Insee), fichier stock des établissements |
| Règles qualité liées | R01 (non nul), R02 (unique), R03 (format 14 chiffres, clé de Luhn) |
| Propriétaire | Responsable du référentiel entreprises |
| Steward | Data steward référentiel entreprises |
| Termes liés | Unité légale, Siège, Activité (APE), Adresse |
| Point d'attention | Un établissement fermé (`etat_administratif = 'F'`) reste dans le fichier : filtrer selon l'usage. Chaque établissement porte son propre code APE, qui peut différer de celui de l'unité légale. |

---

## Siège

| Rubrique | Contenu |
|---|---|
| Définition | Établissement qui porte l'adresse juridique de l'unité légale. Une unité légale a exactement un siège. |
| Règle de calcul | `est_siege = true` dans `stg_etablissements`, ou `siret = siren || nic_siege` depuis `stg_unites_legales`. |
| Source | SIRENE (Insee), fichiers stock des établissements et des unités légales |
| Règles qualité liées | Un et un seul siège par unité légale du périmètre(R12) |
| Propriétaire | Responsable du référentiel entreprises |
| Steward | Data steward référentiel entreprises |
| Termes liés | Établissement, Unité légale, Domiciliation |
| Point d'attention | Le siège n'est pas forcément le lieu de l'activité : les sociétés domiciliées (beaucoup de codes APE 70.10Z) ont leur siège chez un domiciliataire. Avec le filtre de départements, environ 12 % des sièges sont hors périmètre et introuvables dans l'entrepôt. |

### Décision : localiser une entreprise

| Option | Avantage | Limite |
|---|---|---|
| **Commune du siège** (retenue) | Simple, une seule valeur par entreprise, disponible partout | Faussée par la domiciliation |
| Commune du premier établissement ouvert | Plus proche du lieu de démarrage | C'est souvent le siège lui-même |
| Commune qui compte le plus d'établissements | Reflète l'activité réelle | Arbitraire en cas d'égalité, change dans le temps |

**Règle retenue :** la localisation d'une *entreprise* est la commune de son siège. Pour analyser l'activité d'un *territoire*, on compte les établissements, pas les sièges.

---

## Date de création

La date de création existe à deux niveaux, avec deux sens différents.

| Rubrique | Unité légale | Établissement |
|---|---|---|
| Définition | Date de création déclarée de l'entreprise (statuts ou déclaration de création). Ce n'est ni la date d'immatriculation au RCS ni le début de la période en cours. | Date de création déclarée de l'établissement, c'est-à-dire l'ouverture de ce lieu d'activité. |
| Colonne | `stg_unites_legales.date_creation` | `stg_etablissements.date_creation` |
| Source | SIRENE (Insee), stock des unités légales | SIRENE (Insee), stock des établissements |
| Règles qualité liées | `pas_dans_le_futur` | `pas_dans_le_futur` ; pas antérieure à la date de création de l'unité légale |

| Rubrique | Contenu |
|---|---|
| Propriétaire | Responsable du référentiel entreprises |
| Steward | Data steward référentiel entreprises |
| Termes liés | Unité légale, Établissement, Période |
| Point d'attention | Ne pas confondre avec `date_debut` (renommée `date_debut_periode` en staging), qui est le début de la **période historisée en cours** (dernier changement d'état, d'activité…), pas le début d'activité. Un établissement peut être créé bien après son unité légale (ouverture d'un nouveau site). |

> À vérifier dans la documentation des variables Sirene de l'Insee : formulation officielle de `dateCreationUniteLegale` et `dateCreationEtablissement`.

---

## Entrepreneur individuel

| Rubrique | Contenu |
|---|---|
| Définition | Personne physique qui exerce une activité en son nom propre, sans créer de personne morale distincte. Les micro-entrepreneurs en font partie. |
| Règle de calcul | `categorie_juridique = '1000'` → colonne `est_entrepreneur_individuel` dans `stg_unites_legales`. |
| Source | SIRENE (Insee), fichier stock des unités légales |
| Règles qualité liées | Un entrepreneur individuel a un `nom` et pas de `denomination` |
| Propriétaire | Responsable du référentiel entreprises |
| Steward | Data steward référentiel entreprises |
| Termes liés | Unité légale, Statut de diffusion, Données personnelles |
| Point d'attention | `nom` et `prenom1` sont des **données personnelles** : accès réservé au data engineer, jamais exposés dans les marts ni les exports. Si `statut_diffusion = 'P'`, la personne s'est opposée à la diffusion : les champs masqués valent `[ND]` dans la source (convertis en NULL en staging) et `mart_unites_legales` masque le nom. Sans dénomination, ils sont exclus du rapprochement des doublons flous (M1). |