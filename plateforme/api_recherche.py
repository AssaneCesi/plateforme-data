"""Client de l'API Recherche d'entreprises (recherche-entreprises.api.gouv.fr).

Sert à la règle R16 (cohérence entre SIRENE et l'API), prévue en phase 2.
Ce qui est testé ici, avec un faux serveur : pagination, limite de débit, reprise
sur erreur. Avant d'exploiter les réponses, vérifie les noms de paramètres et de
champs dans la documentation officielle : ils sont regroupés ci-dessous.
"""
import json
import time

import httpx

from .journal import journal

log = journal("api_recherche")

# Noms utilisés par l'API : à vérifier dans la documentation officielle
CHEMIN_RECHERCHE = "/search"
PARAM_TEXTE, PARAM_PAGE, PARAM_PAR_PAGE = "q", "page", "per_page"
CLE_RESULTATS, CLE_NB_PAGES = "results", "total_pages"
PAR_PAGE_MAX = 25
INTERVALLE_MIN = 0.2          # l'API annonce une limite de 7 appels par seconde ; on reste en dessous


class ClientRechercheEntreprises:
    def __init__(self, url_base, transport=None, essais=5, attente_base=1.0, dormir=time.sleep):
        self.client = httpx.Client(base_url=url_base, timeout=httpx.Timeout(20),
                                   transport=transport, headers={"Accept": "application/json"})
        self.essais, self.attente_base, self.dormir = essais, attente_base, dormir
        self._dernier_appel = 0.0

    def _get(self, params):
        for essai in range(1, self.essais + 1):
            ecart = time.monotonic() - self._dernier_appel
            if ecart < INTERVALLE_MIN:
                self.dormir(INTERVALLE_MIN - ecart)
            self._dernier_appel = time.monotonic()
            try:
                r = self.client.get(CHEMIN_RECHERCHE, params=params)
            except httpx.TransportError as e:
                attente = self.attente_base * 2 ** (essai - 1)
                log.warning("Erreur réseau (%s), nouvel essai dans %.1f s", e, attente)
                self.dormir(attente)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                retry_after = r.headers.get("Retry-After")
                attente = float(retry_after) if retry_after and retry_after.isdigit() else self.attente_base * 2 ** (essai - 1)
                log.warning("HTTP %d, nouvel essai dans %.1f s (essai %d/%d)", r.status_code, attente, essai, self.essais)
                self.dormir(attente)
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Échec après {self.essais} essais : {params}")

    def rechercher(self, texte, max_pages=None, **filtres):
        """Itère sur tous les résultats, page par page."""
        page = 1
        while True:
            donnees = self._get({PARAM_TEXTE: texte, PARAM_PAGE: page, PARAM_PAR_PAGE: PAR_PAGE_MAX, **filtres})
            yield from donnees.get(CLE_RESULTATS, [])
            nb_pages = donnees.get(CLE_NB_PAGES, 1) or 1
            if page >= nb_pages or (max_pages and page >= max_pages):
                break
            page += 1


def exporter_sirens(client, sirens, destination):
    """Interroge l'API pour chaque SIREN et garde la réponse brute (JSONL), sans la transformer."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(destination, "w", encoding="utf-8") as f:
        for siren in sirens:
            resultats = list(client.rechercher(siren, max_pages=1))
            f.write(json.dumps({"siren_demande": siren, "reponse": resultats[:1]}, ensure_ascii=False) + "\n")
            n += 1
    log.info("%d réponses brutes écrites dans %s", n, destination)
    return n
