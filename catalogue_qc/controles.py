"""Contrôles déterministes (règles métier classiques)."""
from __future__ import annotations

import pandas as pd

from .modele import Anomalie, Catalogue
from .outils import RE_NOTATION_SCIENTIFIQUE, cle_texte, ean_valide, en_nombre, nettoyer

COLONNES_CONTEXTE = ["reference", "ean", "marque", "libelle", "couleur", "taille"]


def exemples(df: pd.DataFrame, index, colonnes, config: dict, commentaire=None) -> pd.DataFrame:
    """Extrait de lignes concernées, avec leur numéro de ligne dans le fichier."""
    cols = [c for c in dict.fromkeys(colonnes) if c in df.columns]
    sous = df.loc[index, cols]
    if commentaire is not None:
        sous = sous.assign(commentaire=commentaire if isinstance(commentaire, str) else commentaire.loc[sous.index])
    return sous.head(config["seuils"]["exemples_max"]).reset_index()


def colonnes_cle(cat: Catalogue, config: dict) -> list[str]:
    if not cat.a("reference"):
        return []
    return [c for c in config["cle_unique"] if cat.a(c)]


def cle_article(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    if df.empty:
        return pd.Series("", index=df.index, dtype=str)
    cle = df[cols[0]].str.strip()
    for c in cols[1:]:
        cle = cle + " / " + df[c].str.strip()
    return cle


# ---------------------------------------------------------------------------
def controle_structure(cat: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    if cat.df.empty:
        res.append(Anomalie("VIDE", "critique", "Structure", "Le fichier ne contient aucune ligne de données", 1))

    for sev in ("critique", "majeur"):
        absentes = [
            c for c, r in config["colonnes"].items()
            if str(r.get("obligatoire", "non")) == sev and not cat.a(c)
        ]
        if absentes:
            res.append(Anomalie(
                "COL_ABSENTE", sev, "Structure",
                f"{len(absentes)} colonne(s) obligatoire(s) absente(s) : {', '.join(absentes)}",
                len(absentes),
                conseil="Vérifier l'en-tête du fichier ou ajouter le nom utilisé par le fournisseur "
                        "dans les synonymes (config/regles.yaml).",
                lignes_touchees=len(cat.df),
            ))

    if cat.colonnes_inattendues:
        res.append(Anomalie(
            "COL_INATTENDUE", "mineur", "Structure",
            f"{len(cat.colonnes_inattendues)} colonne(s) inattendue(s) : {', '.join(cat.colonnes_inattendues)}",
            len(cat.colonnes_inattendues),
            conseil="Colonne non prévue : nouvelle information du fournisseur, renommage d'une colonne "
                    "existante, ou donnée interne à retirer ?",
            lignes_touchees=0,
        ))

    if cat.lignes_mal_formees:
        res.append(Anomalie(
            "LIGNE_MAL_FORMEE", "critique", "Structure",
            f"{len(cat.lignes_mal_formees)} ligne(s) avec un nombre de colonnes incorrect (ignorées)",
            len(cat.lignes_mal_formees),
            conseil="Souvent causé par un séparateur (;) présent dans un libellé ou un retour à la ligne.",
            exemples=pd.DataFrame({"contenu": cat.lignes_mal_formees[: config["seuils"]["exemples_max"]]}),
        ))
    return res


def controle_completude(cat: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    df = cat.df
    for col, regle in config["colonnes"].items():
        if not cat.a(col):
            continue
        vide = nettoyer(df[col]) == ""
        n = int(vide.sum())
        if not n:
            continue
        sev = str(regle.get("obligatoire", "non"))
        if sev == "non":
            sev = "mineur"
        titre = (f"{n} ligne(s) sans référence (identifiant manquant)" if col == "reference"
                 else f"{n} ligne(s) sans valeur pour « {col} »")
        res.append(Anomalie(
            f"VIDE_{col.upper()}", sev, "Complétude", titre, n,
            conseil="Champ obligatoire pour l'intégration." if sev != "mineur"
                    else "Champ facultatif : à compléter si possible.",
            exemples=exemples(df, vide[vide].index, COLONNES_CONTEXTE + [col], config),
        ))
    return res


def controle_unicite(cat: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    df = cat.df.apply(lambda s: s.str.strip())

    # 1. Lignes strictement identiques
    dup_exact = df.duplicated(keep="first")
    if dup_exact.any():
        n = int(dup_exact.sum())
        res.append(Anomalie(
            "DOUBLON_EXACT", "majeur", "Unicité", f"{n} ligne(s) en double exact", n,
            conseil="Supprimer les lignes répétées.",
            exemples=exemples(df, df.duplicated(keep=False)[lambda s: s].index, COLONNES_CONTEXTE, config),
        ))
    uniques = df[~dup_exact]

    # 2. Même article (clé unique) avec des données différentes
    cols = colonnes_cle(cat, config)
    if cols:
        avec_ref = uniques[uniques["reference"] != ""]
        cle = cle_article(avec_ref, cols)
        conflit = cle.duplicated(keep=False)
        if conflit.any():
            groupes = avec_ref[conflit].groupby(cle[conflit])
            differences = {}
            for _, g in groupes:
                diff = [c for c in g.columns if g[c].nunique() > 1]
                for i in g.index:
                    differences[i] = "Diffère sur : " + ", ".join(diff)
            n = groupes.ngroups
            res.append(Anomalie(
                "CLE_CONFLIT", "critique", "Unicité",
                f"{n} article(s) ({' + '.join(cols)}) présent(s) plusieurs fois avec des données différentes",
                n, lignes_touchees=int(conflit.sum()),
                conseil="Impossible de savoir quelle ligne est la bonne : à arbitrer avec le fournisseur.",
                exemples=exemples(avec_ref, conflit[conflit].index, cols + COLONNES_CONTEXTE + config["colonnes_prix"],
                                  config, pd.Series(differences)),
            ))

    # 3. EAN partagés par plusieurs articles
    if cat.a("ean"):
        avec_ean = uniques[uniques["ean"] != ""]
        cle = cle_article(avec_ean, cols) if cols else avec_ean.index.astype(str).to_series(index=avec_ean.index)
        nb_articles = cle.groupby(avec_ean["ean"]).nunique()
        ean_dup = nb_articles[nb_articles > 1].index
        if len(ean_dup):
            masque = avec_ean["ean"].isin(ean_dup)
            res.append(Anomalie(
                "EAN_DOUBLON", "critique", "Unicité", f"{len(ean_dup)} EAN en doublon (partagés par plusieurs articles)",
                len(ean_dup), lignes_touchees=int(masque.sum()),
                conseil="Un EAN identifie un seul article : l'intégration sera rejetée ou écrasera un produit.",
                exemples=exemples(avec_ean.sort_values("ean"), avec_ean[masque].sort_values("ean").index,
                                  ["ean"] + COLONNES_CONTEXTE, config),
            ))
    return res


def controle_validite(cat: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    df = cat.df

    if cat.a("ean"):
        ean = nettoyer(df["ean"])
        renseigne = ean != ""
        scientifique = renseigne & ean.str.match(RE_NOTATION_SCIENTIFIQUE)
        if scientifique.any():
            n = int(scientifique.sum())
            res.append(Anomalie(
                "EAN_SCIENTIFIQUE", "critique", "Validité",
                f"{n} EAN corrompu(s) par Excel (notation scientifique, ex. {ean[scientifique].iloc[0]})", n,
                conseil="Le fichier a été ouvert/enregistré dans Excel : les chiffres de l'EAN sont perdus. "
                        "Redemander le fichier source au fournisseur.",
                exemples=exemples(df, scientifique[scientifique].index, ["ean"] + COLONNES_CONTEXTE, config),
            ))
        invalide = renseigne & ~scientifique & ~ean.map(ean_valide).astype(bool)
        if invalide.any():
            n = int(invalide.sum())
            res.append(Anomalie(
                "EAN_INVALIDE", "majeur", "Validité", f"{n} EAN invalide(s) (longueur ou clé de contrôle)", n,
                conseil="Erreur de saisie probable ou zéro initial perdu.",
                exemples=exemples(df, invalide[invalide].index, ["ean"] + COLONNES_CONTEXTE, config),
            ))

    for col in config["colonnes_prix"]:
        if not cat.a(col):
            continue
        brut = nettoyer(df[col])
        val = en_nombre(df[col])
        non_num = (brut != "") & val.isna()
        if non_num.any():
            n = int(non_num.sum())
            res.append(Anomalie(
                f"PRIX_NON_NUM_{col.upper()}", "critique", "Validité", f"{n} valeur(s) non numérique(s) dans « {col} »", n,
                exemples=exemples(df, non_num[non_num].index, COLONNES_CONTEXTE + [col], config),
            ))
        negatif = val <= 0
        if negatif.any():
            n = int(negatif.sum())
            res.append(Anomalie(
                f"PRIX_NUL_{col.upper()}", "critique", "Validité", f"{n} prix nul(s) ou négatif(s) dans « {col} »", n,
                exemples=exemples(df, negatif[negatif].index, COLONNES_CONTEXTE + [col], config),
            ))

    texte = df.astype(str)
    espaces = texte.apply(lambda s: s.ne(s.str.strip()) | s.str.contains("  ", regex=False))
    if espaces.any().any():
        lignes = espaces.any(axis=1)
        n = int(espaces.sum().sum())
        cols_touchees = espaces.columns[espaces.any()].tolist()
        res.append(Anomalie(
            "ESPACES", "mineur", "Validité",
            f"{n} valeur(s) avec espaces parasites (colonnes : {', '.join(cols_touchees)})", n,
            lignes_touchees=int(lignes.sum()),
            conseil="Sans conséquence si l'outil d'intégration nettoie les espaces, sinon source de faux doublons.",
            exemples=exemples(df, lignes[lignes].index, COLONNES_CONTEXTE + cols_touchees, config),
        ))

    encodage = texte.apply(lambda s: s.str.contains(r"Ã.|�|â€", regex=True))
    if encodage.any().any():
        lignes = encodage.any(axis=1)
        res.append(Anomalie(
            "ENCODAGE", "majeur", "Validité", f"{int(lignes.sum())} ligne(s) avec caractères mal encodés (ex. « Ã© »)",
            int(lignes.sum()),
            conseil="Le fichier a été converti avec un mauvais encodage (UTF-8 / Windows-1252).",
            exemples=exemples(df, lignes[lignes].index, COLONNES_CONTEXTE, config),
        ))
    return res


def controle_coherence(cat: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    df = cat.df

    if cat.a("prix_achat") and cat.a("prix_vente"):
        pa, pv = en_nombre(df["prix_achat"]), en_nombre(df["prix_vente"])
        inverse = (pv > 0) & (pa > 0) & (pv < pa)
        if inverse.any():
            n = int(inverse.sum())
            res.append(Anomalie(
                "PV_INF_PA", "majeur", "Cohérence", f"{n} article(s) avec un prix de vente inférieur au prix d'achat", n,
                conseil="Inversion de colonnes ou erreur de saisie probable.",
                exemples=exemples(df, inverse[inverse].index, COLONNES_CONTEXTE + ["prix_achat", "prix_vente"], config),
            ))

    for a, b in config.get("dependances") or []:
        if not (cat.a(a) and cat.a(b)):
            continue
        sous = df[[a, b]].apply(lambda s: s.str.strip())
        sous = sous[(sous[a] != "") & (sous[b] != "")]
        # Comparaison tolérante (casse, accents, séparateurs) : les variantes d'écriture
        # sont déjà signalées par la détection des marques incohérentes.
        nb = sous[b].map(cle_texte).groupby(sous[a]).nunique()
        incoherents = nb[nb > 1].index
        if len(incoherents):
            masque = sous[a].isin(incoherents)
            valeurs = sous[masque].groupby(a)[b].agg(lambda s: " | ".join(sorted(s.unique())))
            commentaire = sous.loc[masque, a].map(lambda v: f"{b} : {valeurs[v]}")
            res.append(Anomalie(
                f"DEPENDANCE_{a.upper()}_{b.upper()}", "majeur", "Cohérence",
                f"{len(incoherents)} « {a} » associé(s) à plusieurs « {b} » différents",
                len(incoherents), lignes_touchees=int(masque.sum()),
                conseil=f"Chaque « {a} » devrait correspondre à un seul « {b} ».",
                exemples=exemples(df, sous[masque].sort_values(a).index, [a, b] + COLONNES_CONTEXTE, config, commentaire),
            ))
    return res
