"""Génère docs/catalogue-regles.md à partir de qualite/regles.yml."""
from .config import RACINE
from .regles import charger_regles

ENTETE = """# Catalogue des règles de qualité

Fichier généré par `python pipeline.py catalogue` à partir de `qualite/regles.yml`.
Ne pas modifier à la main : modifie le YAML, puis régénère.

Seuil : taux d'échec toléré. Criticité : poids 3 (bloquante), 2 (majeure), 1 (mineure) dans le score.

| Id | Règle | Dimension | Criticité | Seuil | Outil | Objet | État |
|----|-------|-----------|-----------|-------|-------|-------|------|
"""


def generer_catalogue():
    lignes = []
    for r in charger_regles().values():
        etat = "implémentée" if r["statut"] == "implementee" else f"à faire (exercice {r.get('exercice', '?')})"
        seuil = "0" if float(r["seuil"]) == 0 else f"{100 * float(r['seuil']):g} %"
        lignes.append(f"| {r['id']} | {r['libelle']} | {r['dimension']} | {r['criticite']} | {seuil} | "
                      f"{r['outil']} | `{r['objet']}` | {etat} |")
    chemin = RACINE / "docs" / "catalogue-regles.md"
    chemin.write_text(ENTETE + "\n".join(lignes) + "\n", encoding="utf-8")
    return chemin
