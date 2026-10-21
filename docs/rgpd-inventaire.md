# Inventaire des données personnelles

Exercice Gv3 du hub. Rappel : une donnée publique reste soumise au RGPD, et l'Insee
demande de respecter le statut de diffusion le plus récent de chaque personne.

| Donnée | Table source | Personnelle ? | Pourquoi on la garde (finalité) | Mesure appliquée |
|---|---|---|---|---|
| Nom d'un entrepreneur individuel | `raw.unites_legales.nom` | Oui | Denomination des EI | Masqué dans les marts si diffusion partielle (R19) |
| Prénom | `raw.unites_legales.prenom1` | Oui | Denomination des EI | Non repris dans les marts (minimisation) |
| Adresse d'un établissement en diffusion partielle | raw.etablissements.code_postal/code_commune/libelle_commune | Non | Localisation d'un etablissement | Aucune |
| [..] | [..] | [..] | [..] | [..] |

## Durée de conservation

Les données du repertoire sirene sont mises a jour chaque mois et il nous faut au minimum 2 chargements dans le raw, donc nous allon les garder 90j afin d'avoir une marge.

## Qui accède à quoi

* raw: DE en lecture et ecriture.
* marts: Analyste en lecture, DE en lecture et ecriture et Qaulity en lecture. 
* intermediare/staging/quarantaine: DE en elcture et ecriture, Quality en lecture.
