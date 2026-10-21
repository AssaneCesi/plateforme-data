"""Point d'entrée unique du projet.

Exemples :
    python pipeline.py echantillon          # génère des données synthétiques
    python pipeline.py run                  # exécute tout le pipeline
    python pipeline.py telecharger          # récupère les vrais fichiers SIRENE
    python pipeline.py run --source reel    # exécute sur les données réelles
"""
import argparse
import random
import sys
from datetime import date, timedelta

from plateforme.config import charger_config


def main(argv=None):
    p = argparse.ArgumentParser(description="Plateforme de données d'entreprises, qualité intégrée")
    sp = p.add_subparsers(dest="commande", required=True)

    e = sp.add_parser("echantillon", help="Générer un échantillon synthétique au format SIRENE")
    e.add_argument("--taille", type=int, default=4000, help="nombre d'unités légales (défaut 4000)")
    e.add_argument("--graine", type=int, default=42)

    t = sp.add_parser("telecharger", help="Télécharger les fichiers stock SIRENE et le référentiel des communes")
    t.add_argument("--force", action="store_true", help="retélécharger même si les fichiers existent")

    r = sp.add_parser("run", help="Exécuter tout le pipeline")
    r.add_argument("--source", choices=["echantillon", "reel"])
    r.add_argument("--date", type=date.fromisoformat, help="date de chargement (AAAA-MM-JJ), défaut : aujourd'hui")

    h = sp.add_parser("historique", help="Simuler plusieurs jours de chargement (échantillon) pour le scorecard et la dérive")
    h.add_argument("--jours", type=int, default=7)
    h.add_argument("--incident", type=int, default=5, help="jour (1..N) avec une chute de volume, 0 pour aucun")

    sp.add_parser("rapport", help="Réafficher le rapport du dernier run")
    sp.add_parser("catalogue", help="Régénérer docs/catalogue-regles.md")
    sp.add_parser("docs", help="Générer la documentation dbt (lignage)")

    a = sp.add_parser("api", help="Interroger l'API Recherche d'entreprises pour un échantillon de SIREN (phase 2)")
    a.add_argument("--n", type=int, default=50)

    args = p.parse_args(argv)
    cfg = charger_config()

    if args.commande == "echantillon":
        from plateforme.echantillon import ecrire
        ecrire(cfg["chemins"]["echantillon"], n_unites=args.taille, graine=args.graine)
        return 0

    if args.commande == "telecharger":
        from plateforme.telechargement import telecharger_communes, telecharger_sirene
        telecharger_communes(cfg)
        telecharger_sirene(cfg, force=args.force)
        return 0

    if args.commande == "run":
        from plateforme.execution import executer
        return executer(cfg, source=args.source, date_chargement=args.date)

    if args.commande == "historique":
        from plateforme.echantillon import ecrire
        from plateforme.execution import executer
        rng = random.Random(7)
        for jour in range(1, args.jours + 1):
            d = date.today() - timedelta(days=args.jours - jour)
            volume = 0.6 if jour == args.incident else rng.uniform(0.97, 1.03)
            ecrire(cfg["chemins"]["echantillon"], graine=42, graine_anomalies=100 + jour, facteur_volume=volume, jour=d)
            executer(cfg, source="echantillon", date_chargement=d, afficher_rapport=(jour == args.jours))
        return 0

    if args.commande == "rapport":
        from plateforme.entrepot import connexion
        from plateforme.rapport import afficher
        with connexion(cfg) as con:
            dernier = con.execute("SELECT run_id FROM dq.resultats ORDER BY execute_le DESC LIMIT 1").fetchone()
            if not dernier:
                print("Aucun run enregistré : lance d'abord python pipeline.py run")
                return 1
            afficher(con, dernier[0])
        return 0

    if args.commande == "catalogue":
        from plateforme.catalogue import generer_catalogue
        print(f"Catalogue écrit : {generer_catalogue()}")
        return 0

    if args.commande == "docs":
        from plateforme.transformation import executer_dbt
        return executer_dbt(cfg, ["docs", "generate"])

    if args.commande == "api":
        from plateforme.api_recherche import ClientRechercheEntreprises, exporter_sirens
        from plateforme.entrepot import connexion
        with connexion(cfg) as con:
            sirens = [r[0] for r in con.execute(
                "SELECT siren FROM main.stg_unites_legales WHERE etat_administratif = 'A' "
                "ORDER BY random() LIMIT ?", [args.n]).fetchall()]
        client = ClientRechercheEntreprises(cfg["api_recherche"])
        exporter_sirens(client, sirens, cfg["chemins"]["api"] / f"recherche_{date.today():%Y%m%d}.jsonl")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
