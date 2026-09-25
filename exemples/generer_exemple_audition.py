"""Génère deux classeurs Audition fictifs au format fournisseur multi-onglets.

- audition_precedent.xlsx : version N-1, propre
- audition_actuel.xlsx    : version N, avec anomalies injectées

Données entièrement inventées (marques et produits fictifs).
Usage : python exemples/generer_exemple_audition.py
"""
from __future__ import annotations

import copy
import random
from pathlib import Path

import yaml
from openpyxl import Workbook

DOSSIER = Path(__file__).resolve().parent
random.seed(7)

OUI_NON = "Non :  0\nOui :  1"
APPAREILS = [  # (groupe, en-tête avec liste de valeurs éventuelle, clé)
    ("Général", "Code fabricant", "fab"), ("", "Nom du fabricant", "nom_fab"),
    ("", "Code du distributeur", "dist"), ("", "Code produit fabricant", "ref"), ("", "Nom du produit", "nom"),
    ("", "Code commande", "cc"),
    ("", "Type\nBTE : Derrière l'oreille\nRIC : Récepteur dans le canal\nITE : Dans l'oreille\nCIC : Complètement dans le canal", "type"),
    ("", "Gamme", "gamme"), ("", "Marque\nCode - Libellé", "marque"),
    ("", "Code de la couleur", "coul"), ("", "Nom de la couleur", "nom_coul"),
    ("Technique", "Nombre de canaux", "canaux"), ("", "Alimentation\n1 : Pile\n2 : Batterie rechargeable", "alim"),
    ("", "Bluetooth\n" + OUI_NON, "bt"), ("", "Bobine T\n" + OUI_NON, "bobine"),
    ("Commercial", "Action\n1 : Modifié\n2 : Supprimé", "action"),
    ("", "Date de début de validité", "debut"), ("", "Date de fin de validité", "fin"),
    ("", "Classe de remboursement\n1 : Classe 1\n2 : Classe 2\nNO : Pas de classe", "classe"),
    ("", "Achat", "achat"), ("", "Vente", "vente"), ("", "Vate Rate", "tva"), ("", "Eco Tax", "eco"),
]
ACCESSOIRES = [
    ("Général", "Code fabricant", "fab"), ("", "Nom du fabricant", "nom_fab"),
    ("", "Code du distributeur", "dist"), ("", "Code produit fabricant", "ref"), ("", "Nom du produit", "nom"),
    ("", "Code commande", "cc"),
    ("", "Type\n1 : Casque\n2 : Connexion sans fil\n3 : Ecouteur\n9 : Autre", "type"),
    ("", "Marque\nCode - Libellé", "marque"),
    ("Commercial", "Action\n1 : Modifié\n2 : Supprimé", "action"),
    ("", "Achat", "achat"), ("", "Vente", "vente"), ("", "Vate Rate", "tva"), ("", "Eco Tax", "eco"),
]
MARQUES = ["AUR - Auris", "SON - Sonora", "ECH - Echo"]
COULEURS = [("BEI", "Beige"), ("NOI", "Noir"), ("ARG", "Argent"), ("BLE", "Bleu nuit")]


def ean13(n: int) -> str:
    corps = f"376{n:09d}"
    total = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(corps))
    return corps + str((10 - total % 10) % 10)


def generer():
    appareils, accessoires, associations = [], [], []
    n = 1000
    for marque in MARQUES:
        for gamme in [f"{marque[6:]} {g}" for g in ("Alto", "Brio", "Cielo")]:
            niveau_prix = random.choice([900, 1200, 1600])
            for forme in ["BTE", "RIC", "ITE"]:
                for code, nom_coul in random.sample(COULEURS, 2):
                    n += 1
                    appareils.append(dict(
                        fab="SBX", nom_fab="SOUNDBOX", dist="DST", ref=ean13(n), nom=f"{gamme} / {forme}",
                        cc=str(300000 + n), type=forme, gamme=gamme, marque=marque, coul=code, nom_coul=nom_coul,
                        canaux=random.choice(["12", "16", "20"]), alim=random.choice(["1", "2"]), bt="1",
                        bobine=random.choice(["0", "1"]), action="1", debut="2026-01-15 00:00:00", fin="",
                        classe="2", achat=str(niveau_prix + random.choice([0, 50, 100])),
                        vente=random.choice(["", "0"]), tva="5,5", eco="0,04",
                    ))
        for i, (nom, prix, typ) in enumerate([("DOME OUVERT 8 mm (10 pcs)", "4,5", "9"), ("FILTRE CERUMEN", "5,9", "9"),
                                               ("CHARGEUR COMPACT", "189", "9"), ("STREAMER TV", "240", "2")]):
            n += 1
            accessoires.append(dict(fab="SBX", nom_fab="SOUNDBOX", dist="DST", ref=str(700000 + n), nom=f"{nom} {marque[:3]}",
                                    cc=str(700000 + n), type=typ, marque=marque, action="1", achat=prix, vente="",
                                    tva="5,5" if typ == "9" else "20", eco="0"))
    for app in appareils:
        for acc in accessoires:
            if acc["marque"] == app["marque"]:
                associations.append((app["ref"], app["nom"], acc["ref"], acc["nom"]))
    return appareils, accessoires, associations


def ecrire(nom, appareils, accessoires, associations, couleurs, colonnes_en_plus=()):
    wb = Workbook()
    wb.remove(wb.active)
    for titre, modele, lignes in [("Audioprothèses", APPAREILS, appareils), ("Accessoires audio", ACCESSOIRES, accessoires)]:
        ws = wb.create_sheet(titre)
        modele = list(modele) + [("", c, c) for c in colonnes_en_plus if titre == "Audioprothèses"]
        ws.append([g or None for g, _, _ in modele])
        ws.append([h for _, h, _ in modele])
        for ligne in lignes:
            ws.append([ligne.get(k, "") or None for _, _, k in modele])
    ws = wb.create_sheet("Couleurs")
    ws.append(["Couleurs", None, None])
    ws.append(["Code fabricant", "Code de la couleur", "Nom de la couleur"])
    for code, lib in couleurs:
        ws.append(["SBX", code, lib])
    ws = wb.create_sheet("Associations")
    ws.append(["Audioprothèse", None, None, None, "Accessoire audio", None, None, None])
    ws.append(["Code fabricant", "Code du distributeur", "Code produit", "Nom du produit"] * 2)
    for a_ref, a_nom, x_ref, x_nom in associations:
        ws.append(["SBX", "DST", a_ref, a_nom, "SBX", "DST", x_ref, x_nom])
    wb.save(DOSSIER / nom)
    print(f"{nom} : {len(appareils)} appareils, {len(accessoires)} accessoires, {len(associations)} associations")


def ecrire_echo(nom, appareils, accessoires, associations, couleurs, retouches=None):
    """Même catalogue au format ECHO (enregistrements typés), positions lues dans config/formats."""
    spec = yaml.safe_load(open(DOSSIER.parent / "config" / "formats" / "echo_audition.yaml", encoding="utf-8"))
    positions = {str(code): {v.replace(" (?)", ""): int(i) for i, v in r["champs"].items()}
                 for code, r in spec["enregistrements"].items()}
    entetes = {"Audioprothèses": APPAREILS, "Accessoires audio": ACCESSOIRES}

    def valeurs(ligne, onglet):
        v = {h.split("\n")[0]: ligne.get(k, "") for _, h, k in entetes[onglet]}
        v["Marque"] = v["Marque"].split(" - ")[0]
        for d in ("Date de début de validité", "Date de fin de validité"):
            if v.get(d):
                a, m, j = v[d][:10].split("-")
                v[d] = f"{j}/{m}/{a} 00:00:00"
        return v

    def enregistrement(code, v):
        champs = [""] * (max(positions[code].values()) + 1)
        champs[0] = code
        for nom_champ, i in positions[code].items():
            champs[i] = str(v.get(nom_champ, "") or "")
        return champs

    lignes = [["00", "5", "2026", "20260115", "Catalogue fictif", "EUR", "", "0"],
              ["01", "SBX", "SOUNDBOX", "1 rue de l'Exemple", "75000", "Paris", "FR", "M"],
              ["02", "DST", "DISTRIB", "", "", "", "", "M"]]
    lignes += [["03", m.split(" - ")[0], m.split(" - ")[1]] for m in MARQUES]
    modeles = {}
    for app in appareils:
        modeles.setdefault(app["nom"].replace(" / ", "_"), []).append(app)
    for code_modele, declinaisons in modeles.items():
        v = valeurs(declinaisons[0], "Audioprothèses")
        lignes.append(enregistrement("20", dict(v, **{"Code modèle": code_modele, "Code produit modèle": code_modele})))
        for app in declinaisons:
            lignes.append(enregistrement("81", dict(valeurs(app, "Audioprothèses"), **{"Code modèle": code_modele})))
    lignes += [enregistrement("23", valeurs(acc, "Accessoires audio")) for acc in accessoires]
    lignes += [["80", "SBX", code, lib, "", "", ""] for code, lib in couleurs]
    vues = set()
    for a_ref, a_nom, x_ref, x_nom in associations:
        modele = next((m for m, d in modeles.items() if any(x["ref"] == a_ref for x in d)), a_ref)
        if (modele, x_ref) not in vues:
            vues.add((modele, x_ref))
            lignes.append(["8", "SBX", "DST", modele, a_nom, "SBX", "DST", x_ref, x_nom, "", "", ""])
    if retouches:
        lignes = retouches(lignes)
    with open(DOSSIER / nom, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\r\n".join(";".join(l) for l in lignes) + "\r\n")
    print(f"{nom} : {len(lignes)} enregistrements")


def anomalies_echo(lignes):
    """Erreurs propres au format ECHO, injectées dans les enregistrements."""
    modeles = [l for l in lignes if l[0] == "20"]
    declinaisons = [l for l in lignes if l[0] == "81"]
    modeles[0][19] = "Oui"                          # Bluetooth hors liste (attendu 0/1)
    modeles[1][11] = "XYZ"                          # code marque non déclaré en 03
    modeles[2][44] = ""                             # classe de remboursement manquante
    modeles[3][45] = str(int(modeles[3][45]) * 100) # prix en centimes
    declinaisons[1][6] = declinaisons[0][6]         # EAN en doublon
    declinaisons[2][4] = "ROU"                      # couleur absente du référentiel 80
    lignes.append(["81", "SBX", "DST", "FANTOME_BTE", "BEI", "Beige", "3761234567897", "399999"] + [""] * 6)
    lignes.append(["23", "SBX", "SOUNDBOX", "DST"])  # enregistrement tronqué
    lignes.append(["99", "enregistrement inconnu"])
    lignes.append(["8", "SBX", "DST", modeles[0][8], modeles[0][5], "SBX", "DST", "799999", "INCONNU", "", "", ""])
    return lignes


def main():
    appareils, accessoires, associations = generer()
    ecrire("audition_precedent.xlsx", appareils, accessoires, associations, COULEURS)
    ecrire_echo("audition_echo_precedent.csv", appareils, accessoires, associations, COULEURS)
    ecrire_echo("audition_echo_actuel.csv", appareils, accessoires, associations, COULEURS, anomalies_echo)

    app, acc, assoc = copy.deepcopy(appareils), copy.deepcopy(accessoires), list(associations)
    retire = app.pop(5)                                          # disparu sans Action = 2
    assoc = [a for a in assoc if a[0] != retire["ref"]]
    app[0]["action"] = "2"                                       # suppression déclarée (mais encore associée)
    app[1]["bt"] = "Oui"                                         # valeur hors liste (attendu 0/1)
    app[2]["type"] = "RITE"                                      # type inconnu de la liste
    app[3]["marque"] = "Sonora"                                  # format CODE - Libellé non respecté
    app[4]["coul"], app[4]["nom_coul"] = "ROU", "Rouge"          # couleur absente du référentiel
    app[6]["nom_coul"] = "Beige clair"                           # nom différent du référentiel
    app[7]["cc"] = app[8]["cc"]                                  # code commande en doublon
    app[9]["ref"] = app[9]["ref"][:-1] + str((int(app[9]["ref"][-1]) + 1) % 10)  # clé EAN fausse
    app[10]["achat"] = str(int(app[10]["achat"]) * 100)          # prix saisi en centimes
    app[11]["debut"], app[11]["fin"] = "2026-03-01 00:00:00", "2025-12-31 00:00:00"  # dates inversées
    app[12]["tva"] = "19,6"                                      # taux de TVA inattendu
    app[13]["classe"] = ""                                       # classe de remboursement manquante
    app[14]["vente"] = str(int(app[14]["achat"]) - 200)          # vente < achat
    acc[0]["ref"] = app[15]["ref"]                               # même code dans deux onglets
    assoc.append((app[16]["ref"], app[16]["nom"], "799999", "ACCESSOIRE INCONNU"))  # lien orphelin
    ecrire("audition_actuel.xlsx", app, acc, assoc, COULEURS, colonnes_en_plus=("Remise client",))


if __name__ == "__main__":
    main()
