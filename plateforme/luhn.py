"""Clé de contrôle des identifiants SIREN et SIRET.

Règle générale : algorithme de Luhn. En partant de la droite, on double un chiffre
sur deux (on retire 9 si le double dépasse 9) ; la somme doit être un multiple de 10.

Exception documentée : les SIRET de La Poste (SIREN 356000000) ne respectent pas
Luhn. Pour eux, la somme des 14 chiffres doit être un multiple de 5.
"""

SIREN_LA_POSTE = "356000000"


def luhn_valide(numero: str) -> bool:
    if not numero or not numero.isdigit():
        return False
    total = 0
    for rang, caractere in enumerate(reversed(numero)):
        chiffre = int(caractere)
        if rang % 2 == 1:
            chiffre *= 2
            if chiffre > 9:
                chiffre -= 9
        total += chiffre
    return total % 10 == 0


def cle_la_poste_valide(siret: str) -> bool:
    return len(siret) == 14 and siret.isdigit() and sum(int(c) for c in siret) % 5 == 0


def siret_valide(siret: str) -> bool:
    if not siret or len(siret) != 14 or not siret.isdigit():
        return False
    if siret.startswith(SIREN_LA_POSTE):
        return cle_la_poste_valide(siret)
    return luhn_valide(siret)


def siren_valide(siren: str) -> bool:
    return bool(siren) and len(siren) == 9 and luhn_valide(siren)


def completer_luhn(prefixe: str) -> str:
    """Ajoute le chiffre qui rend le numéro valide au sens de Luhn."""
    for d in "0123456789":
        if luhn_valide(prefixe + d):
            return prefixe + d
    raise ValueError(prefixe)  # impossible en pratique
