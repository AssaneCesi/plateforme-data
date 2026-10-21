import httpx

from plateforme.api_recherche import ClientRechercheEntreprises


def _client(gestionnaire):
    return ClientRechercheEntreprises("https://exemple.test", transport=httpx.MockTransport(gestionnaire),
                                      attente_base=0.01, dormir=lambda s: None)


def test_pagination_complete():
    def gestionnaire(requete):
        page = int(requete.url.params["page"])
        return httpx.Response(200, json={"results": [{"siren": f"{page}{i}"} for i in range(2)], "total_pages": 3})
    assert len(list(_client(gestionnaire).rechercher("boulangerie"))) == 6


def test_reprise_apres_limite_de_debit():
    appels = {"n": 0}

    def gestionnaire(requete):
        appels["n"] += 1
        if appels["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"results": [{"siren": "123"}], "total_pages": 1})
    resultats = list(_client(gestionnaire).rechercher("123"))
    assert resultats == [{"siren": "123"}] and appels["n"] == 2
