"""Alertes sur les règles bloquantes et les échecs du pipeline.

Aucun import Airflow ici : le DAG appelle ces fonctions, qui se testent seules.
Canal : Telegram si TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID sont définies dans
l'environnement (mets-les dans env.sh, jamais dans le dépôt). Sinon l'alerte est écrite
dans le journal seulement.
"""
import os

import httpx

from .entrepot import connexion
from .journal import journal
from .rapport import regles_bloquantes_en_echec

log = journal("alerte")


def regles_bloquantes(cfg, run_id):
    """Règles bloquantes en échec pour ce run, lues en lecture seule.

    Renvoie une liste vide si l'entrepôt ou la table n'existe pas encore (échec très tôt).
    """
    try:
        with connexion(cfg, lecture_seule=True) as con:
            return regles_bloquantes_en_echec(con, run_id)
    except Exception as e:                      # pas d'entrepôt, base verrouillée...
        log.warning("Impossible de lire dq.resultats pour l'alerte : %s", type(e).__name__)
        return []


def message_echec(dag_id, tache, date_chargement, regles, erreur=None):
    lignes = [f"[plateforme] Échec : {dag_id} / {tache} (données du {date_chargement})"]
    if regles:
        lignes.append("Règles bloquantes en échec :")
        for regle_id, libelle, nb_echecs, nb_controles, taux, seuil, statut in regles:
            if statut == "erreur" or taux is None:
                lignes.append(f"- {regle_id} {libelle} : règle non exécutée (erreur)")
            else:
                lignes.append(f"- {regle_id} {libelle} : {nb_echecs}/{nb_controles} "
                              f"({taux:.2%}, seuil {seuil:.2%})")
    elif erreur:
        lignes.append(f"Erreur : {str(erreur)[:300]}")
    return "\n".join(lignes)


def envoyer_alerte(message):
    """Journal toujours ; Telegram si configuré. Renvoie True si le message est parti."""
    log.error("ALERTE : %s", message)
    jeton, conversation = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (jeton and conversation):
        log.warning("Telegram non configuré (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) : journal seulement.")
        return False
    try:
        r = httpx.post(f"https://api.telegram.org/bot{jeton}/sendMessage",
                       json={"chat_id": conversation, "text": message[:4000]}, timeout=10)
        r.raise_for_status()
        return True
    except httpx.HTTPError as e:
        # on n'affiche jamais le message d'erreur httpx : il contient l'URL, donc le jeton
        log.warning("Envoi Telegram impossible (%s).", type(e).__name__)
        return False


def alerter(cfg, dag_id, tache, date_chargement, run_id, erreur=None):
    """Construit le message (avec les règles bloquantes du run) et l'envoie."""
    regles = regles_bloquantes(cfg, run_id)
    return envoyer_alerte(message_echec(dag_id, tache, date_chargement, regles, erreur))
