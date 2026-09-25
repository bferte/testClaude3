"""Contrôles croisés entre onglets d'un classeur : référentiel couleurs, associations, unicité globale."""
from __future__ import annotations

import pandas as pd

from .controles import COLONNES_CONTEXTE, exemples
from .modele import Anomalie, Classeur
from .outils import nettoyer


def codes_uniques_entre_onglets(classeur: Classeur, config: dict) -> list[Anomalie]:
    if len(classeur.tableaux) < 2:
        return []
    res = []
    for col in ["reference", *(config.get("colonnes_uniques") or [])]:
        lignes = []
        for nom, cat in classeur.tableaux.items():
            if cat.a(col):
                valeurs = nettoyer(cat.df[col])
                lignes.append(pd.DataFrame({"onglet": nom, "ligne": valeurs.index, col: valeurs.values}))
        if len(lignes) < 2:
            continue
        tout = pd.concat(lignes)
        tout = tout[tout[col] != ""]
        multi = tout.groupby(col)["onglet"].transform("nunique") > 1
        if multi.any():
            n = tout.loc[multi, col].nunique()
            res.append(Anomalie(
                f"DOUBLON_INTER_ONGLETS_{col.upper()}", "critique", "Unicité",
                f"{n} « {col} » présent(s) dans plusieurs onglets", n, lignes_touchees=int(multi.sum()),
                conseil="Un même code ne peut pas être à la fois, par exemple, une audioprothèse et un accessoire.",
                exemples=tout[multi].sort_values(col).head(config["seuils"]["exemples_max"]).reset_index(drop=True),
            ))
    return res


def controle_couleurs(classeur: Classeur, config: dict) -> list[Anomalie]:
    regle = (config.get("referentiels") or {}).get("couleurs")
    ref = classeur.referentiels.get("couleurs")
    if not regle or ref is None or regle["code"] not in ref.columns:
        return []
    libelles = dict(zip(nettoyer(ref[regle["code"]]), nettoyer(ref.get(regle["libelle"], ref[regle["code"]]))))
    res, utilises = [], set()
    for nom, cat in classeur.tableaux.items():
        if not cat.a("couleur"):
            continue
        code = nettoyer(cat.df["couleur"])
        utilises |= set(code)
        absent = (code != "") & ~code.isin(libelles)
        if absent.any():
            res.append(Anomalie(
                "COULEUR_INCONNUE", "majeur", "Référentiel",
                f"[{nom}] {int(absent.sum())} code(s) couleur absent(s) de l'onglet Couleurs", int(absent.sum()),
                conseil="Le code couleur doit être déclaré dans l'onglet Couleurs.", onglet=nom,
                exemples=exemples(cat.df, absent[absent].index, COLONNES_CONTEXTE + ["libelle_couleur"], config),
            ))
        if cat.a("libelle_couleur"):
            attendu = code.map(libelles)
            different = attendu.notna() & (nettoyer(cat.df["libelle_couleur"]) != attendu)
            if different.any():
                commentaire = "Libellé du référentiel : " + attendu[different]
                res.append(Anomalie(
                    "COULEUR_LIBELLE", "majeur", "Référentiel",
                    f"[{nom}] {int(different.sum())} nom(s) de couleur différent(s) du référentiel Couleurs",
                    int(different.sum()), onglet=nom,
                    exemples=exemples(cat.df, different[different].index, COLONNES_CONTEXTE + ["libelle_couleur"],
                                      config, commentaire),
                ))
    inutilises = sorted(set(libelles) - utilises - {""})
    if inutilises:
        res.append(Anomalie(
            "COULEUR_INUTILISEE", "info", "Référentiel",
            f"{len(inutilises)} couleur(s) du référentiel non utilisée(s) par un article", len(inutilises),
            lignes_touchees=0, exemples=pd.DataFrame({"code couleur": inutilises}),
        ))
    return res


def controle_associations(classeur: Classeur, config: dict) -> list[Anomalie]:
    regle = (config.get("referentiels") or {}).get("associations")
    assoc = classeur.referentiels.get("associations")
    if not regle or assoc is None or assoc.empty:
        return []
    res = []
    action = config.get("action") or {}
    max_ex = config["seuils"]["exemples_max"]
    colonnes_lien = [l["colonne"] for l in regle["liens"] if l["colonne"] in assoc.columns]

    doublons = assoc.duplicated(subset=colonnes_lien, keep="first") if colonnes_lien else pd.Series(False, index=assoc.index)
    if doublons.any():
        res.append(Anomalie(
            "ASSOCIATION_DOUBLON", "mineur", "Référentiel", f"{int(doublons.sum())} association(s) en double",
            int(doublons.sum()), lignes_touchees=0,
            exemples=assoc[doublons].head(max_ex).reset_index(),
        ))

    for lien in regle["liens"]:
        col = lien["colonne"]
        if col not in assoc.columns:
            continue
        cibles = [classeur.tableaux[o] for o in lien["onglets"] if o in classeur.tableaux]
        if not cibles:
            continue
        cible = lien.get("cible", "reference")
        noms = {}
        supprimes = set()
        for cat in cibles:
            if cat.a(cible):
                refs = nettoyer(cat.df[cible])
                noms.update(zip(refs, nettoyer(cat.df["libelle"]) if cat.a("libelle") else refs))
                if action and cat.a(action["colonne"]):
                    supprimes |= set(refs[nettoyer(cat.df[action["colonne"]]) == str(action["suppression"])])
        code = nettoyer(assoc[col])
        cible_txt = " / ".join(lien["onglets"])

        orphelin = (code != "") & ~code.isin(noms)
        if orphelin.any():
            n = code[orphelin].nunique()
            res.append(Anomalie(
                f"ASSOCIATION_ORPHELINE_{col.upper()}", "critique", "Référentiel",
                f"{n} code(s) de l'onglet Associations introuvable(s) dans {cible_txt}", n,
                lignes_touchees=0,
                conseil="Lien vers un article inexistant : l'association sera rejetée à l'intégration.",
                exemples=assoc[orphelin].head(max_ex).reset_index(),
            ))
        lib = lien.get("libelle")
        if lib in assoc.columns:
            attendu = code.map(noms)
            different = attendu.notna() & (nettoyer(assoc[lib]) != attendu)
            if different.any():
                ex = assoc[different].head(max_ex).assign(nom_dans_l_onglet_article=attendu[different]).reset_index()
                res.append(Anomalie(
                    f"ASSOCIATION_NOM_{col.upper()}", "mineur", "Référentiel",
                    f"{int(different.sum())} association(s) dont le nom de produit diffère de l'onglet {cible_txt}",
                    int(different.sum()), lignes_touchees=0, exemples=ex,
                ))
        vers_supprime = code.isin(supprimes)
        if vers_supprime.any():
            res.append(Anomalie(
                f"ASSOCIATION_SUPPRIME_{col.upper()}", "majeur", "Référentiel",
                f"{int(vers_supprime.sum())} association(s) vers un article déclaré supprimé", int(vers_supprime.sum()),
                lignes_touchees=0, exemples=assoc[vers_supprime].head(max_ex).reset_index(),
            ))

    lien_principal = next((l for l in regle["liens"] if l["colonne"] in assoc.columns), None)
    for nom in regle.get("articles_sans_association") or []:
        cat = classeur.tableaux.get(nom)
        cible = (lien_principal or {}).get("cible", "reference")
        if cat is None or lien_principal is None or not cat.a(cible):
            continue
        refs = nettoyer(cat.df[cible])
        sans = ~refs.isin(set(nettoyer(assoc[lien_principal["colonne"]])))
        if sans.any():
            res.append(Anomalie(
                "SANS_ASSOCIATION", "info", "Référentiel",
                f"[{nom}] {int(sans.sum())} article(s) sans aucun accessoire associé", int(sans.sum()),
                lignes_touchees=0, onglet=nom,
                conseil="Normal pour certains produits ; à vérifier s'il s'agit de nouveautés.",
                exemples=exemples(cat.df, sans[sans].index, COLONNES_CONTEXTE, config),
            ))
    return res


def controle_marques(classeur: Classeur, config: dict) -> list[Anomalie]:
    """Codes marque des articles présents dans le référentiel des marques du fichier (ex. ECHO, enregistrements 03)."""
    regle = (config.get("referentiels") or {}).get("marques")
    ref = classeur.referentiels.get("marques")
    if not regle or ref is None or regle["code"] not in ref.columns:
        return []
    connues = set(nettoyer(ref[regle["code"]]))
    res = []
    for nom, cat in classeur.tableaux.items():
        if not cat.a("marque"):
            continue
        code = nettoyer(cat.df["marque"])
        inconnue = (code != "") & ~code.isin(connues)
        if inconnue.any():
            valeurs = ", ".join(sorted(code[inconnue].unique())[:5])
            res.append(Anomalie(
                "MARQUE_INCONNUE", "majeur", "Référentiel",
                f"[{nom}] {int(inconnue.sum())} article(s) avec un code marque non déclaré ({valeurs})",
                int(inconnue.sum()), onglet=nom,
                conseil="Le code marque doit figurer dans la liste des marques du fichier.",
                exemples=exemples(cat.df, inconnue[inconnue].index, COLONNES_CONTEXTE, config),
            ))
    return res


TOUS = [codes_uniques_entre_onglets, controle_couleurs, controle_marques, controle_associations]
