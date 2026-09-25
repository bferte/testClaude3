"""Contrôles déterministes (règles métier classiques)."""
from __future__ import annotations

import re

import pandas as pd

from .modele import Anomalie, Catalogue
from .outils import RE_NOTATION_SCIENTIFIQUE, cle_texte, ean_valide, en_date, en_nombre, nettoyer, sans_accents

COLONNES_CONTEXTE = ["reference", "code_commande", "ean", "marque", "libelle", "couleur", "taille"]


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
            and (not r.get("onglets") or cat.onglet in r["onglets"])
        ]
        if absentes:
            res.append(Anomalie(
                "COL_ABSENTE", sev, "Structure",
                f"{len(absentes)} colonne(s) obligatoire(s) absente(s) : {', '.join(absentes)}",
                len(absentes),
                conseil="Vérifier l'en-tête du fichier ou ajouter le nom utilisé par le fournisseur "
                        "dans les synonymes du profil (dossier config/profils).",
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
        onglets = regle.get("onglets")
        if sev == "non" or (onglets and cat.onglet not in onglets):
            if vide.all():
                continue  # colonne facultative non utilisée dans ce tableau : normal
            sev = config.get("severite_facultatif_vide", "mineur")
        titre = (f"{n} ligne(s) sans référence (identifiant manquant)" if col == "reference"
                 else f"{n} ligne(s) sans valeur pour « {col} »")
        res.append(Anomalie(
            f"VIDE_{col.upper()}", sev, "Complétude", titre, n,
            conseil="Champ obligatoire pour l'intégration." if sev in ("critique", "majeur")
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

    # 3. Identifiants partagés par plusieurs articles (EAN, code commande...)
    for col in config.get("colonnes_uniques") or []:
        if not cat.a(col):
            continue
        renseigne = uniques[uniques[col] != ""]
        cle = cle_article(renseigne, cols) if cols else renseigne.index.astype(str).to_series(index=renseigne.index)
        nb_articles = cle.groupby(renseigne[col]).nunique()
        en_double = nb_articles[nb_articles > 1].index
        if len(en_double):
            masque = renseigne[col].isin(en_double)
            res.append(Anomalie(
                f"DOUBLON_{col.upper()}", "critique", "Unicité",
                f"{len(en_double)} « {col} » en doublon (partagés par plusieurs articles)",
                len(en_double), lignes_touchees=int(masque.sum()),
                conseil=f"Un « {col} » identifie un seul article : l'intégration sera rejetée ou écrasera un produit.",
                exemples=exemples(renseigne, renseigne[masque].sort_values(col).index,
                                  [col] + COLONNES_CONTEXTE, config),
            ))
    return res


def controle_validite(cat: Catalogue, config: dict) -> list[Anomalie]:
    res = []
    df = cat.df

    for regle in config.get("colonnes_gtin") or []:
        col = regle["colonne"]
        if not cat.a(col):
            continue
        ean = nettoyer(df[col])
        renseigne = ean != ""
        scientifique = renseigne & ean.str.match(RE_NOTATION_SCIENTIFIQUE)
        if scientifique.any():
            n = int(scientifique.sum())
            res.append(Anomalie(
                f"GTIN_SCIENTIFIQUE_{col.upper()}", "critique", "Validité",
                f"{n} « {col} » corrompu(s) par Excel (notation scientifique, ex. {ean[scientifique].iloc[0]})", n,
                conseil="Le fichier a été ouvert/enregistré dans Excel : les chiffres du code-barre sont perdus. "
                        "Redemander le fichier source au fournisseur.",
                exemples=exemples(df, scientifique[scientifique].index, [col] + COLONNES_CONTEXTE, config),
            ))
        a_controler = renseigne & ~scientifique
        if not regle.get("strict", True):
            a_controler &= ean.str.fullmatch(r"\d{8}|\d{12,14}")
        invalide = a_controler & ~ean.map(ean_valide).astype(bool)
        if invalide.any():
            n = int(invalide.sum())
            res.append(Anomalie(
                f"GTIN_INVALIDE_{col.upper()}", "majeur", "Validité",
                f"{n} « {col} » : code-barre EAN invalide (longueur ou clé de contrôle)", n,
                conseil="Erreur de saisie probable ou zéro initial perdu.",
                exemples=exemples(df, invalide[invalide].index, [col] + COLONNES_CONTEXTE, config),
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
                f"PRIX_NUL_{col.upper()}", config.get("severite_prix_nul", "critique"), "Validité", f"{n} prix nul(s) ou négatif(s) dans « {col} »", n,
                exemples=exemples(df, negatif[negatif].index, COLONNES_CONTEXTE + [col], config),
            ))

    for col in config.get("colonnes_dates") or []:
        if not cat.a(col):
            continue
        brut = nettoyer(df[col])
        invalide = (brut != "") & en_date(df[col]).isna()
        if invalide.any():
            n = int(invalide.sum())
            res.append(Anomalie(
                f"DATE_INVALIDE_{col.upper()}", "majeur", "Validité", f"{n} date(s) illisible(s) dans « {col} »", n,
                exemples=exemples(df, invalide[invalide].index, COLONNES_CONTEXTE + [col], config),
            ))

    texte = df.astype(str)
    espaces = texte.apply(lambda s: s.ne(s.str.strip()))
    if espaces.any().any():
        lignes = espaces.any(axis=1)
        n = int(espaces.sum().sum())
        cols_touchees = espaces.columns[espaces.any()].tolist()
        res.append(Anomalie(
            "ESPACES", "mineur", "Validité",
            f"{n} valeur(s) avec espaces en début ou fin (colonnes : {', '.join(cols_touchees)})", n,
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


def controle_valeurs_autorisees(cat: Catalogue, config: dict) -> list[Anomalie]:
    """Valeurs hors des listes autorisées (lues dans l'en-tête du fichier ou définies dans le profil)."""
    res = []
    regles = config.get("enumerations") or {}
    listes = {c: set(v) for c, v in cat.enumerations.items()} if regles.get("controle", True) else {}
    for col, valeurs in (config.get("valeurs_autorisees") or {}).items():
        listes[col] = {str(v) for v in valeurs}
    neutres = {str(v) for v in regles.get("valeurs_neutres") or []}

    for col, autorisees in listes.items():
        if not cat.a(col):
            continue
        val = nettoyer(cat.df[col])
        hors = (val != "") & ~val.isin(autorisees | neutres)
        if hors.any():
            n = int(hors.sum())
            valeurs = ", ".join(f"« {v} »" for v in val[hors].value_counts().index[:5])
            apercu = ", ".join(sorted(autorisees)[:12]) + (" ..." if len(autorisees) > 12 else "")
            res.append(Anomalie(
                f"VALEUR_HORS_LISTE_{normaliser_code(col)}", "majeur", "Validité",
                f"{n} valeur(s) non autorisée(s) dans « {col} » ({valeurs})", n,
                conseil=f"Valeurs attendues : {apercu}",
                exemples=exemples(cat.df, hors[hors].index, COLONNES_CONTEXTE + [col], config),
            ))

    for col in cat.formats_code_libelle:
        if not cat.a(col):
            continue
        val = nettoyer(cat.df[col])
        mauvais = (val != "") & ~val.str.match(r"^\S+ - \S")
        if mauvais.any():
            n = int(mauvais.sum())
            res.append(Anomalie(
                f"FORMAT_CODE_LIBELLE_{normaliser_code(col)}", "majeur", "Validité",
                f"{n} valeur(s) de « {col} » ne respectant pas le format « CODE - Libellé »", n,
                exemples=exemples(cat.df, mauvais[mauvais].index, COLONNES_CONTEXTE + [col], config),
            ))
    return res


OPERATEURS = {"<": "lt", "<=": "le", ">": "gt", ">=": "ge", "=": "eq", "!=": "ne"}


def controle_comparaisons(cat: Catalogue, config: dict) -> list[Anomalie]:
    """Règles « colonne A <opérateur> colonne B » déclarées dans le profil (nombres ou dates)."""
    res = []
    for regle in config.get("comparaisons") or []:
        g, d, op = regle["gauche"], regle["droite"], regle["operateur"]
        if not (cat.a(g) and cat.a(d)):
            continue
        a, b = en_nombre(cat.df[g]), en_nombre(cat.df[d])
        if a.notna().sum() == 0 or b.notna().sum() == 0:
            a, b = en_date(cat.df[g]), en_date(cat.df[d])
        comparables = a.notna() & b.notna()
        ko = comparables & ~getattr(a, OPERATEURS[op])(b)
        if ko.any():
            n = int(ko.sum())
            res.append(Anomalie(
                f"REGLE_{normaliser_code(g)}_{normaliser_code(d)}", regle.get("severite", "majeur"), "Cohérence",
                f"{n} ligne(s) : {regle.get('message', f'{g} {op} {d} non respecté')}", n,
                conseil=f"Règle attendue : {g} {op} {d}",
                exemples=exemples(cat.df, ko[ko].index, COLONNES_CONTEXTE + [g, d], config),
            ))
    return res


def controle_suppressions_declarees(cat: Catalogue, config: dict) -> list[Anomalie]:
    regle = config.get("action")
    if not regle or not cat.a(regle["colonne"]):
        return []
    supprimes = nettoyer(cat.df[regle["colonne"]]) == str(regle["suppression"])
    if not supprimes.any():
        return []
    n = int(supprimes.sum())
    return [Anomalie(
        "SUPPRESSIONS_DECLAREES", "info", "Évolution", f"{n} article(s) déclaré(s) supprimé(s) par le fournisseur", n,
        lignes_touchees=0,
        conseil="Vérifier le stock et les commandes en cours sur ces articles.",
        exemples=exemples(cat.df, supprimes[supprimes].index, COLONNES_CONTEXTE, config),
    )]


def normaliser_code(col: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", sans_accents(col).upper()).strip("_")
