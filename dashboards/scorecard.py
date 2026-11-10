"""Scorecard qualité : une image PNG lisible en dix secondes, construite depuis exports/.

    python dashboards/scorecard.py                      # lit exports/, écrit dashboards/scorecard.png
    python dashboards/scorecard.py --exports exports_historique --sortie dashboards/scorecard_historique.png

Le scorecard est du code : il se régénère après chaque run, se versionne et se relit
en revue, comme le reste du pipeline. Power BI reste possible à partir des mêmes CSV.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent

# Encre, surface, couleurs. Le bleu porte la donnée ; les couleurs de statut ne servent
# qu'aux statuts et sont toujours accompagnées d'un libellé.
SURFACE = "#fcfcfb"
ENCRE = "#0b0b0b"
ENCRE_2 = "#52514e"
ENCRE_3 = "#8a8984"
GRILLE = "#e6e5e1"
BLEU = "#2a78d6"
OK = "#0ca30c"
ECHEC = "#d03b3b"
ATTENTION = "#c9800b"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Segoe UI", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "text.color": ENCRE,
    "axes.edgecolor": GRILLE,
    "axes.labelcolor": ENCRE_2,
    "xtick.color": ENCRE_2,
    "ytick.color": ENCRE_2,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
})

ORDRE_CRITICITE = {"bloquante": 0, "majeure": 1, "mineure": 2}


def pct(x, decimales=2):
    return f"{x:.{decimales}f}".replace(".", ",") + " %"


def nombre(n):
    return f"{int(n):,}".replace(",", " ")


def charger(dossier):
    scores = pd.read_csv(dossier / "dq_scores.csv", parse_dates=["date_chargement"])
    resultats = pd.read_csv(dossier / "dq_resultats.csv", parse_dates=["date_chargement"])
    chargements = pd.read_csv(dossier / "chargements.csv", parse_dates=["date_chargement"])
    return scores, resultats, chargements


def runs_complets(resultats):
    """Un run est complet s'il a évalué autant de règles que le run le plus complet.
    Un run interrompu (dbt en erreur, par exemple) fausserait la tendance."""
    nb = resultats.groupby("run_id")["regle_id"].nunique()
    return set(nb[nb == nb.max()].index)


def dernier_run_par_jour(table, complets):
    t = table[table["run_id"].isin(complets)]
    derniers = t.groupby("date_chargement")["run_id"].max()
    return t[t["run_id"].isin(derniers.values)]


def tuile(ax, titre, valeur, detail, couleur_valeur=ENCRE, pastille=None):
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="white",
                               edgecolor=GRILLE, linewidth=1))
    ax.text(0.07, 0.78, titre, fontsize=9.5, color=ENCRE_2, transform=ax.transAxes)
    x = 0.07
    if pastille:
        ax.scatter([0.10], [0.45], s=150, color=pastille, transform=ax.transAxes, clip_on=False)
        x = 0.17
    ax.text(x, 0.45, valeur, fontsize=22, fontweight="bold", color=couleur_valeur,
            va="center", transform=ax.transAxes)
    ax.text(0.07, 0.14, detail, fontsize=8.5, color=ENCRE_3, transform=ax.transAxes)


def graphe_dimensions(ax, dims):
    dims = dims.sort_values("score_pct")
    y = range(len(dims))
    bas = min(97.0, dims["score_pct"].min() - 0.5)
    ax.hlines(y, bas, dims["score_pct"], color=GRILLE, linewidth=2)
    ax.scatter(dims["score_pct"], y, s=70, color=BLEU, zorder=3, edgecolor="white", linewidth=1.5)
    for i, (_, l) in enumerate(dims.iterrows()):
        ax.text(l["score_pct"] - 0.06, i + 0.28, pct(l["score_pct"]), fontsize=8.5,
                color=ENCRE_2, ha="right", va="bottom")
    ax.set_yticks(list(y), dims["dimension"])
    ax.set_xlim(bas, 100.15)
    ax.set_ylim(-0.6, len(dims) - 0.3)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.5))
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.1f} %".replace(".", ","))
    ax.tick_params(length=0, labelsize=9)
    ax.grid(axis="x", color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.set_title("Score par dimension, dernier run", loc="left", fontsize=11,
                 fontweight="bold", pad=10)
    ax.text(0, 1.01, "Pondéré par la criticité : bloquante ×3, majeure ×2, mineure ×1. "
            "L'axe commence à " + f"{bas:.0f} %.", transform=ax.transAxes, fontsize=8,
            color=ENCRE_3)


def graphe_tendance(ax, tendance):
    ax.plot(tendance["date_chargement"], tendance["score_pct"], color=BLEU, linewidth=2,
            marker="o", markersize=6, markeredgecolor="white", markeredgewidth=1.5)
    der = tendance.iloc[-1]
    ax.annotate(pct(der["score_pct"]), (der["date_chargement"], der["score_pct"]),
                xytext=(6, 8), textcoords="offset points", fontsize=8.5, color=ENCRE_2)
    centre = tendance["score_pct"].mean()
    marge = max(1.0, (tendance["score_pct"].max() - tendance["score_pct"].min()) * 1.5)
    ax.set_ylim(max(0, centre - marge), min(100.2, centre + marge))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f} %".replace(".", ","))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(tendance) // 7 or 1)))
    ax.tick_params(length=0, labelsize=9)
    ax.grid(axis="y", color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.set_title("Score global dans le temps", loc="left", fontsize=11, fontweight="bold", pad=10)
    ax.text(0, 1.01, f"Dernier run complet de chaque jour ({len(tendance)} jours)",
            transform=ax.transAxes, fontsize=8, color=ENCRE_3)


def tableau_regles(ax, regles):
    ax.set_axis_off()
    regles = regles.assign(_c=regles["criticite"].map(ORDRE_CRITICITE)) \
        .sort_values(["nb_echecs", "_c"], ascending=[False, True])
    colonnes = [("Règle", 0.0), ("Libellé", 0.055), ("Dimension", 0.47), ("Criticité", 0.565),
                ("Échecs / contrôlés", 0.655), ("Taux", 0.77), ("Seuil", 0.835), ("Statut", 0.895)]
    droite = {"Échecs / contrôlés": 0.745, "Taux": 0.81, "Seuil": 0.875}
    n = len(regles)
    h = 1 / (n + 1.6)
    y0 = 1 - h * 0.6
    for nom, x in colonnes:
        ax.text(droite.get(nom, x), y0, nom, fontsize=8.5, color=ENCRE_3, fontweight="bold",
                transform=ax.transAxes, va="center", ha="right" if nom in droite else "left")
    ax.plot([0, 1], [y0 - h * 0.55] * 2, color=GRILLE, linewidth=1, transform=ax.transAxes)
    for i, (_, r) in enumerate(regles.iterrows()):
        y = y0 - h * (i + 1.1)
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0, y - h / 2), 1, h, transform=ax.transAxes,
                                       facecolor="#f4f3f0", edgecolor="none"))
        statut = r["statut"]
        libelle_statut, couleur = {"ok": ("Toléré", OK), "echec": ("Au-dessus du seuil", ECHEC),
                                   "erreur": ("Erreur", ATTENTION)}.get(statut, (statut, ENCRE_3))
        valeurs = {
            "Règle": r["regle_id"],
            "Libellé": r["libelle"] if len(r["libelle"]) <= 62 else r["libelle"][:60] + "…",
            "Dimension": r["dimension"],
            "Criticité": r["criticite"],
            "Échecs / contrôlés": f"{nombre(r['nb_echecs'])} / {nombre(r['nb_controles'])}",
            "Taux": pct(100 * r["taux_echec"]),
            "Seuil": pct(100 * r["seuil"], 1),
        }
        for nom, x in colonnes[:-1]:
            ax.text(droite.get(nom, x), y, valeurs[nom], fontsize=8.5, transform=ax.transAxes,
                    va="center", ha="right" if nom in droite else "left",
                    color=ENCRE if nom != "Dimension" else ENCRE_2,
                    fontweight="bold" if nom == "Criticité" and r["criticite"] == "bloquante" else None)
        ax.scatter([colonnes[-1][1] + 0.006], [y], s=45, color=couleur, transform=ax.transAxes,
                   clip_on=False)
        ax.text(colonnes[-1][1] + 0.016, y, libelle_statut, fontsize=8.5, color=ENCRE,
                transform=ax.transAxes, va="center")
    ax.set_title("Règles du dernier run, triées par nombre d'échecs", loc="left", fontsize=11,
                 fontweight="bold", pad=4)


def construire(dossier, sortie, mention):
    scores, resultats, chargements = charger(dossier)
    complets = runs_complets(resultats)
    dernier = max(complets)
    regles = resultats[resultats["run_id"] == dernier]
    s_dernier = scores[scores["run_id"] == dernier]
    global_ = s_dernier.loc[s_dernier["dimension"] == "GLOBAL", "score_pct"].iloc[0]
    dims = s_dernier[s_dernier["dimension"] != "GLOBAL"]
    tendance = dernier_run_par_jour(scores, complets)
    tendance = tendance[tendance["dimension"] == "GLOBAL"].sort_values("date_chargement")
    volumes = chargements[chargements["run_id"] == dernier].set_index("objet")["nb_lignes"]
    vol_jours = dernier_run_par_jour(chargements, complets)
    vol_etab = vol_jours[vol_jours["objet"] == "etablissements"]["nb_lignes"]
    variation = (vol_etab.max() - vol_etab.min()) / vol_etab.max() if len(vol_etab) else 0

    au_dessus = (regles["statut"] != "ok").sum()
    bloquantes_ko = ((regles["criticite"] == "bloquante") & (regles["statut"] != "ok")).sum()
    date_run = regles["date_chargement"].iloc[0]

    fig = plt.figure(figsize=(14, 10.4), dpi=150)
    gs = fig.add_gridspec(3, 4, height_ratios=[1, 2.3, 4.1], hspace=0.42, wspace=0.28,
                          left=0.045, right=0.975, top=0.885, bottom=0.03)

    fig.text(0.045, 0.955, "Scorecard qualité · Plateforme de données d'entreprises (SIRENE)",
             fontsize=17, fontweight="bold")
    fig.text(0.045, 0.927, f"Dernier run : {dernier} du {date_run:%d/%m/%Y} · "
             f"{len(regles)} règles · {resultats['run_id'].nunique()} runs historisés",
             fontsize=10, color=ENCRE_2)
    if mention:
        fig.text(0.975, 0.955, mention, fontsize=9.5, color="#7a4b00", ha="right",
                 fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.45", facecolor="#fff4d6", edgecolor="#f0d48a"))

    tuile(fig.add_subplot(gs[0, 0]), "Score global", pct(global_),
          "Moyenne des dimensions, dernier run")
    tuile(fig.add_subplot(gs[0, 1]), "Règles bloquantes en échec", str(bloquantes_ko),
          "0 = publication autorisée", pastille=OK if bloquantes_ko == 0 else ECHEC)
    tuile(fig.add_subplot(gs[0, 2]), "Règles au-dessus du seuil", f"{au_dessus} / {len(regles)}",
          "Majeures et mineures : alerte sans blocage",
          pastille=OK if au_dessus == 0 else ATTENTION)
    tuile(fig.add_subplot(gs[0, 3]), "Volume chargé",
          nombre(volumes.get("etablissements", 0)),
          f"établissements, {nombre(volumes.get('unites_legales', 0))} UL · "
          + ("stable" if variation == 0 else f"écart {pct(100 * variation, 1)}")
          + f" sur {len(vol_etab)} j")

    sous = gs[1, :2].subgridspec(1, 2, width_ratios=[0.11, 0.89], wspace=0)
    graphe_dimensions(fig.add_subplot(sous[0, 1]), dims)
    graphe_tendance(fig.add_subplot(gs[1, 2:]), tendance)
    tableau_regles(fig.add_subplot(gs[2, :]), regles)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(sortie, dpi=150, facecolor=SURFACE)
    print(f"Scorecard écrit : {sortie}")
    print(f"  score global {pct(global_)} · {au_dessus}/{len(regles)} règles au-dessus du seuil · "
          f"{bloquantes_ko} bloquante(s) en échec")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--exports", type=Path, default=RACINE / "exports")
    p.add_argument("--sortie", type=Path, default=RACINE / "dashboards" / "scorecard.png")
    p.add_argument("--mention", default="Données de test : échantillon synthétique",
                   help="bandeau en haut à droite ; chaîne vide pour le retirer")
    a = p.parse_args()
    construire(a.exports, a.sortie, a.mention)


if __name__ == "__main__":
    main()