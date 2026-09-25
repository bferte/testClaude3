"""Comparaison du catalogue actuel avec la version précédente."""
from __future__ import annotations

import pandas as pd

from .controles import COLONNES_CONTEXTE, cle_article, colonnes_cle, exemples
from .modele import Anomalie, Catalogue
from .outils import cle_reference, cle_texte, en_nombre, signature


def _preparer(cat: Catalogue, cols: list[str]) -> pd.DataFrame:
    df = cat.df.apply(lambda s: s.str.strip())
    df = df[df["reference"] != ""].copy()
    df["_cle"] = cle_article(df, cols)
    return df[~df["_cle"].duplicated()]


def _changement_codification(a: pd.DataFrame, p: pd.DataFrame) -> list[str]:
    """Compare le format dominant des références, globalement et par marque."""
    def groupes(df):
        g = {"l'ensemble du catalogue": df}
        if "marque" in df.columns:
            g.update({m: sous for m, sous in df.groupby(df["marque"].map(cle_texte)) if m})
        return g

    constats = []
    ga, gp = groupes(a), groupes(p)
    for nom in ga.keys() & gp.keys():
        sa, sp = ga[nom]["reference"].map(signature), gp[nom]["reference"].map(signature)
        if len(sa) < 20 or len(sp) < 20:
            continue
        pa, pp = sa.value_counts(normalize=True), sp.value_counts(normalize=True)
        ancien, nouveau = pp.index[0], pa.index[0]
        if ancien != nouveau and pa.iloc[0] >= 0.5 and pa.get(ancien, 0) < 0.2:
            constats.append(f"{nom} : {ancien} ({pp.iloc[0]:.0%}) -> {nouveau} ({pa.iloc[0]:.0%})")
    return sorted(constats, key=lambda c: not c.startswith("l'ensemble"))


def comparer(cat: Catalogue, prec: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    seuils = config["seuils"]

    ajoutees = [c for c in cat.df.columns if c not in prec.df.columns]
    retirees = [c for c in prec.df.columns if c not in cat.df.columns]
    if ajoutees or retirees:
        detail = "; ".join(filter(None, [
            f"ajoutée(s) : {', '.join(ajoutees)}" if ajoutees else "",
            f"retirée(s) : {', '.join(retirees)}" if retirees else "",
        ]))
        res.append(Anomalie("EVOL_COLONNES", "majeur", "Évolution", f"Colonnes modifiées depuis la version précédente ({detail})",
                            len(ajoutees) + len(retirees), lignes_touchees=0,
                            conseil="Le mapping d'intégration doit peut-être être adapté."))

    cols = [c for c in colonnes_cle(cat, config) if prec.a(c)]
    if not cols or not prec.a("reference"):
        return res
    a, p = _preparer(cat, cols), _preparer(prec, cols)
    cles_a, cles_p = set(a["_cle"]), set(p["_cle"])
    supprimes = p[~p["_cle"].isin(cles_a)]
    ajoutes = a[~a["_cle"].isin(cles_p)]

    # 1. Recodification : même EAN, clé différente
    if "ean" in a.columns and "ean" in p.columns:
        nouvelle_cle = ajoutes[ajoutes["ean"] != ""].drop_duplicates("ean").set_index("ean")["_cle"]
        recod = supprimes[supprimes["ean"].isin(nouvelle_cle.index) & (supprimes["ean"] != "")]
        if not recod.empty:
            ancienne = recod.drop_duplicates("ean").set_index("ean")["_cle"]
            nouveaux = ajoutes[ajoutes["ean"].isin(ancienne.index)].drop_duplicates("ean")
            commentaire = nouveaux["ean"].map(lambda e: f"Ancien article : {ancienne[e]}")
            res.append(Anomalie(
                "EVOL_RECODIFICATION", "majeur", "Évolution",
                f"{len(nouveaux)} article(s) recodifié(s) : même EAN, nouvelle référence", len(nouveaux),
                conseil="Changement de codification non annoncé ? Sans table de correspondance, l'historique "
                        "(ventes, stock) sera perdu et des doublons créés.",
                exemples=exemples(a, nouveaux.index, COLONNES_CONTEXTE, config, commentaire),
            ))
            supprimes = supprimes.drop(recod.index)
            ajoutes = ajoutes.drop(nouveaux.index)

    # 2. Références renommées : même référence à la casse / séparateur / O-0 près
    ref_sup = pd.Series(supprimes["reference"].unique())
    ref_ajt = pd.Series(ajoutes["reference"].unique())
    if len(ref_sup) and len(ref_ajt):
        par_cle = dict(zip(ref_ajt.map(cle_reference), ref_ajt))
        paires = {r: par_cle[cle_reference(r)] for r in ref_sup if cle_reference(r) in par_cle}
        if paires:
            nouvelles = {v: k for k, v in paires.items()}
            masque = ajoutes["reference"].isin(nouvelles)
            commentaire = ajoutes.loc[masque, "reference"].map(lambda r: f"Ancienne référence : {nouvelles[r]}")
            res.append(Anomalie(
                "EVOL_RENOMMAGE", "majeur", "Évolution",
                f"{len(paires)} référence(s) réécrite(s) différemment (ex. {next(iter(paires))} -> "
                f"{next(iter(paires.values()))})", len(paires), lignes_touchees=int(masque.sum()),
                conseil="Même référence écrite autrement : faute de frappe ou changement de format ?",
                exemples=exemples(a, ajoutes[masque].index, COLONNES_CONTEXTE, config, commentaire),
            ))
            supprimes = supprimes[~supprimes["reference"].isin(paires)]
            ajoutes = ajoutes[~masque]

    # 3. Changement global de format de codification
    constats = _changement_codification(a, p)
    if constats:
        res.append(Anomalie(
            "EVOL_FORMAT", "majeur", "Évolution",
            f"Changement de format des références ({constats[0]})", len(constats), lignes_touchees=0,
            conseil="Le fournisseur semble avoir changé sa codification : demander une table de correspondance.",
            exemples=pd.DataFrame({"constat": constats}),
        ))

    # 4. Suppressions / ajouts non expliqués
    if len(supprimes):
        pct = 100 * len(supprimes) / max(len(p), 1)
        sev = "majeur" if pct > seuils["suppressions_majeur_pct"] else "mineur"
        declare = " sans être déclaré(s) supprimé(s) (Action)" if (config.get("action") or {}).get("colonne") in a.columns else ""
        res.append(Anomalie(
            "EVOL_SUPPRESSIONS", sev, "Évolution",
            f"{len(supprimes)} article(s) absent(s) depuis la version précédente{declare} ({pct:.1f} %)", len(supprimes),
            lignes_touchees=0,
            conseil="Fin de série ou oubli du fournisseur ? Les articles encore en stock doivent être vérifiés.",
            exemples=exemples(p, supprimes.index, COLONNES_CONTEXTE, config, "Présent dans la version précédente"),
        ))
    if len(ajoutes):
        pct = 100 * len(ajoutes) / max(len(a), 1)
        sev = "majeur" if pct > seuils["ajouts_majeur_pct"] else "info"
        res.append(Anomalie(
            "EVOL_AJOUTS", sev, "Évolution", f"{len(ajoutes)} nouvel(s) article(s) ({pct:.1f} %)", len(ajoutes),
            lignes_touchees=0,
            exemples=exemples(a, ajoutes.index, COLONNES_CONTEXTE, config, "Nouveau"),
        ))

    # 5. Articles communs : changements de données
    communs = a.reset_index().merge(p.reset_index(), on="_cle", suffixes=("", "_prec"))
    communs = communs.set_index("ligne")
    if "ean" in communs.columns and "ean_prec" in communs.columns:
        change = (communs["ean"] != communs["ean_prec"]) & (communs["ean"] != "") & (communs["ean_prec"] != "")
        if change.any():
            com = "EAN précédent : " + communs.loc[change, "ean_prec"]
            res.append(Anomalie(
                "EVOL_EAN", "critique", "Évolution", f"{int(change.sum())} article(s) dont l'EAN a changé",
                int(change.sum()), conseil="Un EAN ne devrait jamais changer pour un même article.",
                exemples=exemples(a, change[change].index, ["ean"] + COLONNES_CONTEXTE, config, com),
            ))
    if "marque" in communs.columns and "marque_prec" in communs.columns:
        change = communs["marque"].map(cle_texte) != communs["marque_prec"].map(cle_texte)
        if change.any():
            com = "Marque précédente : " + communs.loc[change, "marque_prec"]
            res.append(Anomalie(
                "EVOL_MARQUE", "majeur", "Évolution", f"{int(change.sum())} article(s) ayant changé de marque",
                int(change.sum()),
                exemples=exemples(a, change[change].index, COLONNES_CONTEXTE, config, com),
            ))
    for col in config["colonnes_prix"]:
        if col not in communs.columns or f"{col}_prec" not in communs.columns:
            continue
        avant, apres = en_nombre(communs[f"{col}_prec"]), en_nombre(communs[col])
        variation = 100 * (apres - avant) / avant.where(avant > 0)
        forte = variation.abs() > seuils["variation_prix_pct"]
        if forte.any():
            com = ("Avant : " + avant[forte].round(2).astype(str) + " -> après : " + apres[forte].round(2).astype(str)
                   + " (" + variation[forte].round(0).astype(int).map("{:+d} %".format) + ")")
            res.append(Anomalie(
                f"EVOL_PRIX_{col.upper()}", "majeur", "Évolution",
                f"{int(forte.sum())} variation(s) de « {col} » supérieure(s) à {seuils['variation_prix_pct']} %",
                int(forte.sum()),
                conseil="Hausse tarifaire réelle ou erreur de saisie ?",
                exemples=exemples(a, forte[forte].index, COLONNES_CONTEXTE + [col], config, com),
            ))
    return res
