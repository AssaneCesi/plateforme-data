from plateforme.luhn import completer_luhn, luhn_valide, siren_valide, siret_valide


def test_numero_complete_est_valide():
    assert luhn_valide(completer_luhn("12345678"))


def test_numero_modifie_devient_invalide():
    siren = completer_luhn("73282932")
    faux = siren[:-1] + str((int(siren[-1]) + 1) % 10)
    assert siren_valide(siren) and not siren_valide(faux)


def test_format_invalide():
    assert not siret_valide("1234567890123")      # 13 chiffres
    assert not siret_valide("12345678A01234")     # lettre
    assert not siret_valide(None)


def test_exception_la_poste():
    # Le SIREN de La Poste respecte Luhn ; ses SIRET suivent une règle propre (somme multiple de 5)
    assert siren_valide("356000000")
    siret = "35600000049085"
    assert sum(map(int, siret)) % 5 == 0 and not luhn_valide(siret)
    assert siret_valide(siret)
