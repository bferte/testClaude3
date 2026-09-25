"""Détection "intelligente" sans IA générative : similarité, formats, statistiques."""
from __future__ import annotations

from collections import Counter

import pandas as pd
from rapidfuzz import fuzz, process

from .controles import COLONNES_CONTEXTE, exemples
from .modele import Anomalie, Catalogue
from .outils import cle_reference, cle_texte, en_nombre, nettoyer, signature, zscore_robuste


def _regrouper(cles: list[str], seuil: int) -> list[set[str]]:
    """Regroupe des chaînes proches (union-find sur la matrice de similarité)."""
    parent = {c: c for c in cles}

    def racine(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    longues = [c for c in cles if len(c) >= 4]
    if len(longues) > 1:
        matrice = process.cdist(longues, longues, scorer=fuzz.ratio, score_cutoff=seuil, workers=-1)
        for i, j in zip(*matrice.nonzero()):
            if i < j:
                parent[racine(longues[i])] = racine(longues[j])
    groupes: dict[str, set[str]] = {}
    for c in cles:
        groupes.setdefault(racine(c), set()).add(c)
    return list(groupes.values())


def marques_incoherentes(cat: Catalogue, config: dict) -> list[Anomalie]:
    """RAYBAN / RAY BAN / Ray-Ban / RAY-BANN -> une seule marque probable."""
    if not cat.a("marque"):
        return []
    marques = nettoyer(cat.df["marque"])
    marques = marques[marques != ""]
    ecritures = Counter(marques)
    par_cle: dict[str, Counter] = {}
    for ecriture, n in ecritures.items():
        par_cle.setdefault(cle_texte(ecriture), Counter())[ecriture] = n

    groupes = _regrouper(list(par_cle), config["seuils"]["similarite_marques"])
    lignes, commentaires, n_groupes = [], {}, 0
    for groupe in groupes:
        variantes = Counter()
        for cle in groupe:
            variantes.update(par_cle[cle])
        if len(variantes) < 2:
            continue
        n_groupes += 1
        reference = variantes.most_common(1)[0][0]
        detail = ", ".join(f"{v} ({n})" for v, n in variantes.most_common())
        for v in variantes:
            if v != reference:
                idx = marques[marques == v].index
                lignes.extend(idx)
                for i in idx:
                    commentaires[i] = f"Remplacer par « {reference} » ? Variantes : {detail}"
    if not n_groupes:
        return []
    return [Anomalie(
        "MARQUE_VARIANTES", "mineur", "Détection intelligente",
        f"{n_groupes} marque(s) avec orthographe incohérente", n_groupes, lignes_touchees=len(lignes),
        conseil="Harmoniser sur l'écriture du référentiel marques (la plus fréquente est proposée).",
        exemples=exemples(cat.df, lignes, ["marque"] + COLONNES_CONTEXTE, config, pd.Series(commentaires)),
    )]


def references_quasi_identiques(cat: Catalogue, config: dict) -> list[Anomalie]:
    """RB-1234 / RB1234 / rb 1234 / RB-12O4 : probablement la même référence mal saisie."""
    if not cat.a("reference"):
        return []
    refs = nettoyer(cat.df["reference"])
    refs = refs[refs != ""]
    distinctes = pd.Series(refs.unique())
    cles = distinctes.map(cle_reference)
    conflits = distinctes[cles.duplicated(keep=False)]
    if conflits.empty:
        return []
    groupe = conflits.groupby(cles[conflits.index]).agg(lambda s: " | ".join(sorted(s)))
    masque = refs.isin(conflits)
    commentaire = refs[masque].map(lambda r: "Écritures proches : " + groupe[cle_reference(r)])
    return [Anomalie(
        "REF_QUASI_IDENTIQUES", "majeur", "Détection intelligente",
        f"{len(groupe)} groupe(s) de références quasi identiques (séparateur, casse, O/0, I/1)",
        len(groupe), lignes_touchees=int(masque.sum()),
        conseil="Erreur de frappe probable : deux fiches produit seraient créées pour le même article.",
        exemples=exemples(cat.df, refs[masque].sort_values().index, COLONNES_CONTEXTE, config, commentaire),
    )]


def formats_atypiques(cat: Catalogue, config: dict) -> list[Anomalie]:
    """Repère les codes qui ne suivent pas le format dominant (ex. 'AA-9999'), par marque."""
    res = []
    part_min = config["seuils"]["format_part_dominante"]
    for col in config.get("controle_format") or []:
        if not cat.a(col):
            continue
        valeurs = nettoyer(cat.df[col])
        valeurs = valeurs[valeurs != ""]
        sig = valeurs.map(signature)
        groupes = nettoyer(cat.df.loc[valeurs.index, "marque"]).map(cle_texte) if cat.a("marque") and col == "reference" \
            else pd.Series("", index=valeurs.index)
        atypiques, commentaires = [], {}
        for _, idx in sig.groupby(groupes).groups.items():
            s = sig[idx]
            if len(s) < 20:
                continue
            parts = s.value_counts(normalize=True)
            dominants = parts[parts >= 0.10]
            if dominants.sum() < part_min:
                continue  # pas de format dominant clair : on ne juge pas
            hors = s[~s.isin(dominants.index)]
            atypiques.extend(hors.index)
            attendu = " ou ".join(dominants.index[:3])
            for i in hors.index:
                commentaires[i] = f"Format {sig[i]} ; attendu : {attendu}"
        if atypiques:
            res.append(Anomalie(
                f"FORMAT_{col.upper()}", "mineur", "Détection intelligente",
                f"{len(atypiques)} valeur(s) de « {col} » au format inhabituel", len(atypiques),
                conseil="Erreur de saisie ou nouvelle codification du fournisseur ?",
                exemples=exemples(cat.df, atypiques, [col] + COLONNES_CONTEXTE, config, pd.Series(commentaires)),
            ))
    return res


def valeurs_aberrantes(cat: Catalogue, config: dict) -> list[Anomalie]:
    """Prix statistiquement anormaux (par marque) et erreurs d'unité (x100, x1000)."""
    res = []
    seuil = config["seuils"]["zscore_aberrant"]
    facteur = config["seuils"]["facteur_erreur_unite"]
    groupe = pd.Series("", index=cat.df.index)
    for col in config.get("groupement_prix") or ["marque"]:
        if cat.a(col):
            groupe = groupe + "|" + nettoyer(cat.df[col]).map(cle_texte)

    series = {c: en_nombre(cat.df[c]) for c in config["colonnes_prix"] if cat.a(c)}
    if "prix_achat" in series and "prix_vente" in series:
        series["coefficient"] = (series["prix_vente"] / series["prix_achat"]).where(series["prix_achat"] > 0)

    for nom, val in series.items():
        val = val[val > 0]
        if len(val) < 20:
            continue
        # Par marque si l'effectif est suffisant, sinon sur l'ensemble du catalogue
        taille_groupe = groupe[val.index].map(groupe[val.index].value_counts())
        cle = groupe[val.index].where(taille_groupe >= 15, "__global__")
        z = val.groupby(cle).transform(zscore_robuste)
        mediane = val.groupby(cle).transform("median")
        ratio = val / mediane
        aberrant = z.abs() > seuil
        # Erreur d'unité : le prix corrigé d'un facteur 10/100/1000 retombe dans la fourchette normale du groupe
        q1, q3 = val.groupby(cle).transform(lambda s: s.quantile(0.25)), val.groupby(cle).transform(lambda s: s.quantile(0.75))
        corrigeable = pd.Series(False, index=val.index)
        for k in (10, 100, 1000):
            for v in (val / k, val * k):
                corrigeable |= (v >= q1 / 1.5) & (v <= q3 * 1.5)
        unite = aberrant & corrigeable & ((ratio >= facteur) | (ratio <= 1 / facteur)) & (nom != "coefficient")
        stat = aberrant & ~unite
        commentaire = (f"{nom} = " + val.round(2).astype(str) + " ; médiane du groupe = "
                       + mediane.round(2).astype(str) + " (x" + ratio.round(1).astype(str) + ")")
        cols = COLONNES_CONTEXTE + ["prix_achat", "prix_vente"]
        if unite.any():
            res.append(Anomalie(
                f"ERREUR_UNITE_{nom.upper()}", "majeur", "Détection intelligente",
                f"{int(unite.sum())} « {nom} » hors d'échelle (erreur d'unité probable : centimes, x100...)",
                int(unite.sum()),
                conseil="Vérifier la virgule / l'unité : un prix d'intégration faux est visible du client.",
                exemples=exemples(cat.df, unite[unite].index, cols, config, commentaire),
            ))
        if stat.any():
            libelle = "coefficient de marge" if nom == "coefficient" else f"« {nom} »"
            res.append(Anomalie(
                f"ABERRANT_{nom.upper()}", "mineur", "Détection intelligente",
                f"{int(stat.sum())} {libelle} statistiquement atypique(s)", int(stat.sum()),
                conseil="Pas forcément une erreur (produit premium, fin de série) : contrôle visuel conseillé.",
                exemples=exemples(cat.df, stat[stat].index, cols, config, commentaire),
            ))
    return res


def doublons_probables(cat: Catalogue, config: dict) -> list[Anomalie]:
    """Même produit (marque + libellé + couleur + taille) sous des références différentes."""
    cols = [c for c in ("marque", "libelle", "couleur", "taille") if cat.a(c)]
    if not cat.a("reference") or len(cols) < 2 or "libelle" not in cols:
        return []
    df = cat.df.apply(lambda s: s.str.strip())
    df = df[(df["reference"] != "") & (df["libelle"] != "")]
    if df.empty:
        return []
    signature_produit = df[cols[0]].map(cle_texte)
    for c in cols[1:]:
        signature_produit = signature_produit + "|" + df[c].map(cle_texte)
    nb_refs = df.groupby(signature_produit)["reference"].transform("nunique")
    masque = nb_refs > 1
    if not masque.any():
        return []
    refs = df[masque].groupby(signature_produit[masque])["reference"].agg(lambda s: " | ".join(sorted(s.unique())))
    commentaire = signature_produit[masque].map(lambda s: "Références : " + refs[s])
    return [Anomalie(
        "DOUBLON_PROBABLE", "mineur", "Détection intelligente",
        f"{len(refs)} produit(s) identique(s) sous plusieurs références ({' + '.join(cols)})",
        len(refs), lignes_touchees=int(masque.sum()),
        conseil="Doublon de fiche produit probable, ou libellé trop générique.",
        exemples=exemples(cat.df, df[masque].sort_values(cols).index, COLONNES_CONTEXTE, config, commentaire),
    )]


TOUS = [marques_incoherentes, references_quasi_identiques, formats_atypiques, valeurs_aberrantes, doublons_probables]
