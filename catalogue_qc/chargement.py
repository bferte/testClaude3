"""Lecture robuste des fichiers fournisseurs (CSV ou Excel multi-onglets).

Gère : encodage, séparateur, en-tête sur 1 ou 2 lignes (ligne de groupes
« Général / Technique / Commercial » au-dessus des noms de colonnes), listes de
valeurs autorisées écrites dans la cellule d'en-tête (« 1 : Digital / 2 : Analogue »),
synonymes d'en-têtes, et choix automatique du profil de règles.
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .modele import Catalogue, Classeur, charger_profils

ENCODAGES = ["utf-8-sig", "cp1252", "latin-1"]
SEPARATEURS = [";", ",", "\t", "|"]
MENTION_CODE_LIBELLE = "code - libellé"
RE_CODE_COURT = re.compile(r"^[A-Z0-9]{1,5}$")
RE_ENTIER_EXCEL = re.compile(r"^-?\d+\.0$")


def normaliser_nom(nom: str) -> str:
    """'Libellé couleur ' -> 'libelle_couleur'."""
    nom = unicodedata.normalize("NFKD", str(nom)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", nom.strip().lower()).strip("_")


@dataclass
class TableBrute:
    onglet: str | None
    df: pd.DataFrame
    enumerations: dict[str, dict[str, str]] = field(default_factory=dict)
    formats_code_libelle: list[str] = field(default_factory=list)
    encodage: str = ""
    separateur: str = ""
    lignes_mal_formees: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lecture physique
# ---------------------------------------------------------------------------
def _decoder(contenu: bytes) -> tuple[str, str]:
    for enc in ENCODAGES:
        try:
            return contenu.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError("Encodage du fichier non reconnu")


def _detecter_separateur(texte: str) -> str:
    echantillon = "\n".join(texte.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(echantillon, delimiters="".join(SEPARATEURS)).delimiter
    except csv.Error:
        premiere = texte.splitlines()[0] if texte else ""
        return max(SEPARATEURS, key=premiere.count)


def _moteur_excel() -> str:
    try:
        import python_calamine  # noqa: F401  (lecture ~3x plus rapide si installé)
        return "calamine"
    except ImportError:
        return "openpyxl"


def _code_et_libelle(ligne: str) -> tuple[str, str]:
    """'1 : Digital' -> ('1', 'Digital') ; 'Oui :  1' -> ('1', 'Oui') ; '312' -> ('312', '312')."""
    if ":" not in ligne:
        return ligne.strip(), ligne.strip()
    a, b = (s.strip() for s in ligne.split(":", 1))
    if not RE_CODE_COURT.match(a) and re.fullmatch(r"\w{1,4}", b):
        return b, a
    return a, b


def _structurer(brut: pd.DataFrame, onglet: str | None) -> TableBrute:
    """Repère la ligne d'en-tête, extrait noms de colonnes et listes de valeurs."""
    brut = brut.fillna("").astype(str)
    if brut.empty:
        return TableBrute(onglet, pd.DataFrame())
    ligne = 0
    if len(brut) >= 2 and brut.shape[1] > 1:
        if (brut.iloc[0] == "").mean() >= 0.5 and (brut.iloc[1] == "").mean() <= 0.1:
            ligne = 1  # ligne 0 = groupes de colonnes (Général, Technique...)
    groupes = brut.iloc[0].replace("", pd.NA).ffill().fillna("").tolist() if ligne else [""] * brut.shape[1]

    colonnes = []
    for i, (cellule, groupe) in enumerate(zip(brut.iloc[ligne], groupes)):
        morceaux = [m.strip() for m in cellule.splitlines() if m.strip()]
        colonnes.append((morceaux[0] if morceaux else f"colonne_{i + 1}", groupe, morceaux[1:]))

    doublons = Counter(nom for nom, _, _ in colonnes)
    par_groupe = Counter((nom, groupe) for nom, groupe, _ in colonnes)
    vus: Counter = Counter()
    noms, enumerations, formats = [], {}, []
    for nom, groupe, valeurs in colonnes:
        if doublons[nom] > 1:
            if groupe and par_groupe[(nom, groupe)] == 1:
                nom = f"{groupe} - {nom}"
            else:
                vus[nom] += 1
                nom = nom if vus[nom] == 1 else f"{nom} ({vus[nom]})"
        noms.append(nom)
        if [v.lower() for v in valeurs] == [MENTION_CODE_LIBELLE]:
            formats.append(nom)
        elif valeurs:
            enumerations[nom] = dict(_code_et_libelle(v) for v in valeurs)

    df = brut.iloc[ligne + 1:].copy()
    df.columns = noms
    df.index = pd.RangeIndex(ligne + 2, ligne + 2 + len(df), name="ligne")  # n° de ligne vu dans Excel
    return TableBrute(onglet, df, enumerations, formats)


def lire_tables(contenu: bytes, nom_fichier: str) -> list[TableBrute]:
    if contenu[:4] == b"PK\x03\x04" or nom_fichier.lower().endswith((".xlsx", ".xlsm")):
        feuilles = pd.read_excel(io.BytesIO(contenu), sheet_name=None, header=None, dtype=str, engine=_moteur_excel())
        tables = []
        for onglet, brut in feuilles.items():
            brut = brut.apply(lambda s: s.str.replace(RE_ENTIER_EXCEL, lambda m: m.group()[:-2], regex=True))
            table = _structurer(brut, onglet)
            table.encodage, table.separateur = "Excel", "-"
            tables.append(table)
        return tables

    texte, encodage = _decoder(contenu)
    separateur = _detecter_separateur(texte)
    mal_formees: list[str] = []

    def _ligne_invalide(champs: list[str]):
        mal_formees.append(separateur.join(champs))
        return None

    brut = pd.read_csv(io.StringIO(texte), sep=separateur, header=None, dtype=str, keep_default_na=False,
                       na_filter=False, engine="python", on_bad_lines=_ligne_invalide)
    table = _structurer(brut, None)
    table.encodage, table.separateur, table.lignes_mal_formees = encodage, separateur, mal_formees
    return [table]


# ---------------------------------------------------------------------------
# Application d'un profil de règles
# ---------------------------------------------------------------------------
def _table_synonymes(config: dict) -> dict[str, str]:
    table = {}
    for canonique, regle in config["colonnes"].items():
        table[normaliser_nom(canonique)] = canonique
        for syn in regle.get("synonymes", []) or []:
            table.setdefault(normaliser_nom(syn), canonique)
    return table


def score_profil(tables: list[TableBrute], config: dict) -> float:
    """Part des colonnes obligatoires du profil retrouvées dans le fichier (+ bonus onglets connus)."""
    synonymes = _table_synonymes(config)
    trouvees = {synonymes.get(normaliser_nom(c)) for t in tables for c in t.df.columns}
    obligatoires = [c for c, r in config["colonnes"].items() if str(r.get("obligatoire", "non")) != "non"]
    score = sum(c in trouvees for c in obligatoires) / max(len(obligatoires), 1)
    onglets_connus = {normaliser_nom(o) for o in config.get("onglets_articles") or []}
    if onglets_connus and any(normaliser_nom(t.onglet or "") in onglets_connus for t in tables):
        score += 0.5
    return score


def choisir_profil(tables: list[TableBrute], profils: dict[str, dict] | None = None) -> dict:
    profils = profils or charger_profils()
    return max(profils.values(), key=lambda p: (score_profil(tables, p), bool(p.get("par_defaut"))))


def _catalogue(table: TableBrute, config: dict, nom_fichier: str) -> Catalogue:
    synonymes = _table_synonymes(config)
    connues = {normaliser_nom(c) for c in config.get("colonnes_connues") or []}
    renommage, correspondance, inattendues = {}, {}, []
    for col in table.df.columns:
        canonique = synonymes.get(normaliser_nom(col))
        if canonique and canonique not in correspondance:
            renommage[col] = canonique
            correspondance[canonique] = col
        elif normaliser_nom(col) not in connues:
            inattendues.append(col)
    df = table.df.rename(columns=renommage)

    for col, regle in config["colonnes"].items():
        if regle.get("zero_equivaut_vide") and col in df.columns:
            valeur = pd.to_numeric(df[col].str.strip().str.replace(",", ".", regex=False), errors="coerce")
            df.loc[valeur == 0, col] = ""

    return Catalogue(
        df=df,
        nom_fichier=nom_fichier,
        encodage=table.encodage,
        separateur=table.separateur,
        correspondance=correspondance,
        colonnes_inattendues=inattendues,
        lignes_mal_formees=table.lignes_mal_formees,
        onglet=table.onglet,
        enumerations={renommage.get(c, c): v for c, v in table.enumerations.items()},
        formats_code_libelle=[renommage.get(c, c) for c in table.formats_code_libelle],
    )


def appliquer_profil(tables: list[TableBrute], config: dict, nom_fichier: str) -> Classeur:
    referentiels_cfg = {normaliser_nom(v["onglet"]): cle for cle, v in (config.get("referentiels") or {}).items()}
    ignores = {normaliser_nom(o) for o in config.get("onglets_ignores") or []}
    classeur = Classeur(nom_fichier=nom_fichier, tableaux={}, profil=config.get("nom", ""))
    for table in tables:
        cle = normaliser_nom(table.onglet or "")
        if table.df.columns.empty or (table.onglet and cle in ignores):
            continue
        if table.onglet and cle in referentiels_cfg:
            classeur.referentiels[referentiels_cfg[cle]] = table.df.rename(columns=normaliser_nom)
            continue
        catalogue = _catalogue(table, config, nom_fichier)
        classeur.tableaux[catalogue.nom] = catalogue
    return classeur


# ---------------------------------------------------------------------------
# Points d'entrée
# ---------------------------------------------------------------------------
def _contenu(source, nom_fichier: str | None) -> tuple[bytes, str]:
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes(), nom_fichier or Path(source).name
    if isinstance(source, bytes):
        return source, nom_fichier or "catalogue.csv"
    return source.read(), nom_fichier or getattr(source, "name", "catalogue.csv")


def lire_classeur(source, config: dict | None = None, nom_fichier: str | None = None) -> tuple[Classeur, dict]:
    """Lit un fichier ; sans `config`, le profil de règles est choisi automatiquement.

    Retourne le classeur et le profil utilisé.
    """
    contenu, nom = _contenu(source, nom_fichier)
    tables = lire_tables(contenu, nom)
    config = config or choisir_profil(tables)
    return appliquer_profil(tables, config, nom), config


def lire_csv(source, config: dict, nom_fichier: str | None = None) -> Catalogue:
    """Raccourci : premier tableau d'un fichier (usage simple / tests)."""
    classeur, _ = lire_classeur(source, config, nom_fichier)
    return next(iter(classeur.tableaux.values()))
