"""Génère deux catalogues fictifs (version précédente / actuelle) avec anomalies injectées.

Usage : python exemples/generer_exemples.py
"""
from __future__ import annotations

import copy
import csv
import random
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
random.seed(42)

MARQUES = {  # marque : (préfixe référence, prix d'achat min, max)
    "RAY-BAN": ("RB", 45, 110), "OAKLEY": ("OO", 55, 130), "PERSOL": ("PO", 70, 150),
    "VOGUE": ("VO", 25, 60), "PRADA": ("PR", 110, 220), "GUCCI": ("GG", 130, 260),
    "TOM FORD": ("FT", 120, 240), "CARRERA": ("CA", 35, 80), "POLAROID": ("PLD", 20, 45),
    "ARNETTE": ("AN", 25, 50),
}
MODELES = ["Aviator", "Wayfarer", "Clubmaster", "Round", "Pilot", "Cat Eye", "Square", "Sport", "Oversize", "Browline"]
COULEURS = [("001", "Noir"), ("002", "Havane"), ("003", "Or"), ("004", "Argent"), ("005", "Bleu"),
            ("006", "Rouge"), ("007", "Vert"), ("008", "Écaille")]
TAILLES = ["50", "52", "54", "56"]
ENTETE = ["Référence", "EAN", "Marque", "Libellé", "Code couleur", "Libellé couleur", "Taille",
          "Prix achat HT", "PVC", "Famille"]

_compteur_ean = 100000000


def nouvel_ean() -> str:
    global _compteur_ean
    _compteur_ean += random.randint(1, 50)
    corps = f"380{_compteur_ean:09d}"
    total = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(corps))
    return corps + str((10 - total % 10) % 10)


def prix(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def generer_reference(marque: str, deja: set[str]) -> list[dict]:
    prefixe, pmin, pmax = MARQUES[marque]
    while True:
        ref = f"{prefixe}-{random.randint(1000, 9999)}"
        if ref not in deja:
            deja.add(ref)
            break
    modele, famille = random.choice(MODELES), random.choice(["Solaire", "Optique"])
    pa = random.uniform(pmin, pmax)
    lignes = []
    for code, lib in random.sample(COULEURS, random.randint(1, 3)):
        for taille in random.sample(TAILLES, random.randint(1, 3)):
            pa_v = pa * random.uniform(0.97, 1.03)
            lignes.append({
                "Référence": ref, "EAN": nouvel_ean(), "Marque": marque,
                "Libellé": f"{marque.title()} {ref.split('-')[-1]} {modele} {famille}", "Code couleur": code, "Libellé couleur": lib,
                "Taille": taille, "Prix achat HT": prix(pa_v), "PVC": prix(round(pa_v * random.uniform(2.1, 2.5)) - 0.01),
                "Famille": famille,
            })
    return lignes


def ecrire(nom: str, lignes: list[dict], entete: list[str]):
    with open(DOSSIER / nom, "w", encoding="cp1252", newline="") as f:
        w = csv.DictWriter(f, fieldnames=entete, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)
    print(f"{nom} : {len(lignes)} lignes")


def main():
    refs: set[str] = set()
    precedent = []
    for marque in MARQUES:
        for _ in range(random.randint(30, 50)):
            precedent += generer_reference(marque, refs)
    ecrire("catalogue_precedent.csv", precedent, ENTETE)

    actuel = copy.deepcopy(precedent)
    # --- Évolutions ---------------------------------------------------------
    for _ in range(35):                                    # articles supprimés
        actuel.pop(random.randrange(len(actuel)))
    for _ in range(15):                                    # nouvelles références
        actuel += generer_reference(random.choice(list(MARQUES)), refs)
    for l in actuel:                                       # PERSOL change de codification : PO-1234 -> PO1234
        if l["Marque"] == "PERSOL":
            l["Référence"] = l["Référence"].replace("-", "")
    for l in random.sample(actuel, 8):                     # hausses de prix de +40 %
        l["PVC"] = prix(float(l["PVC"].replace(",", ".")) * 1.4)
    random.choice(actuel)["EAN"] = nouvel_ean()            # EAN modifié pour un article existant

    # --- Anomalies de saisie ------------------------------------------------
    rb = [l for l in actuel if l["Marque"] == "RAY-BAN"]
    for l, ecriture in zip(random.sample(rb, 11), ["RAY BAN"] * 6 + ["Ray-Ban "] * 3 + ["RAYBAN"] * 2):
        l["Marque"] = ecriture
    for l in random.sample([l for l in actuel if l["Marque"] == "OAKLEY"], 2):
        l["Marque"] = "OAKLEYY"
    for l in random.sample(actuel, 4):
        l["Référence"] = ""
    for l in random.sample(actuel, 2):                     # EAN en doublon
        l["EAN"] = random.choice(actuel)["EAN"]
    for l in random.sample(actuel, 3):                     # EAN abîmés par Excel
        l["EAN"] = f"{int(l['EAN']) / 1e12:.5f}E+12".replace(".", ",")
    for l in random.sample(actuel, 2):                     # clé de contrôle fausse
        l["EAN"] = l["EAN"][:-1] + str((int(l["EAN"][-1]) + 1) % 10)
    for l in random.sample(actuel, 3):                     # PV < PA (colonnes inversées)
        l["Prix achat HT"], l["PVC"] = l["PVC"], l["Prix achat HT"]
    for l in random.sample(actuel, 2):                     # prix saisi en centimes
        l["PVC"] = str(int(round(float(l["PVC"].replace(",", ".")) * 100)))
    for l in random.sample(actuel, 3):
        l["Prix achat HT"] = ""
    for l in random.sample([l for l in actuel if l["Code couleur"] == "005"], 3):
        l["Libellé couleur"] = "Bleu marine"
    for l in random.sample(actuel, 5):
        l["Libellé"] += "  "
    for l in random.sample(actuel, 6):
        l["Taille"] = ""
    ca = next(l for l in actuel if l["Marque"] == "CARRERA" and "0" in l["Référence"])  # faute de frappe 0 -> O
    faute = dict(ca, **{"Référence": ca["Référence"].replace("0", "O", 1), "Taille": "58", "EAN": nouvel_ean()})
    actuel.append(faute)
    actuel += [dict(l) for l in random.sample(actuel, 2)]  # doublons exacts
    for l in random.sample(actuel, 2):                     # même article, prix différent
        actuel.append(dict(l, **{"PVC": prix(float(l["PVC"].replace(",", ".")) + 20)}))
    for l in random.sample(actuel, 4):
        l["Commentaire interne"] = "voir avec Julien"

    random.shuffle(actuel)
    ecrire("catalogue_actuel.csv", actuel, ENTETE + ["Commentaire interne"])


if __name__ == "__main__":
    main()
