"""Lecture robuste des CSV fournisseurs : encodage, séparateur, en-têtes."""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from pathlib import Path

import pandas as pd

from .modele import Catalogue

ENCODAGES = ["utf-8-sig", "cp1252", "latin-1"]
SEPARATEURS = [";", ",", "\t", "|"]


def normaliser_nom(nom: str) -> str:
    """'Libellé couleur ' -> 'libelle_couleur'."""
    nom = unicodedata.normalize("NFKD", str(nom)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", nom.strip().lower()).strip("_")


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


def _table_synonymes(config: dict) -> dict[str, str]:
    table = {}
    for canonique, regle in config["colonnes"].items():
        table[normaliser_nom(canonique)] = canonique
        for syn in regle.get("synonymes", []) or []:
            table.setdefault(normaliser_nom(syn), canonique)
    return table


def lire_csv(source, config: dict, nom_fichier: str | None = None) -> Catalogue:
    """`source` : chemin, bytes ou objet fichier (ex. upload Streamlit)."""
    if isinstance(source, (str, Path)):
        nom_fichier = nom_fichier or Path(source).name
        contenu = Path(source).read_bytes()
    elif isinstance(source, bytes):
        contenu = source
    else:
        contenu = source.read()
        nom_fichier = nom_fichier or getattr(source, "name", "catalogue.csv")

    texte, encodage = _decoder(contenu)
    separateur = _detecter_separateur(texte)

    lignes_mal_formees: list[str] = []

    def _ligne_invalide(champs: list[str]):
        lignes_mal_formees.append(separateur.join(champs))
        return None

    df = pd.read_csv(
        io.StringIO(texte),
        sep=separateur,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        engine="python",
        on_bad_lines=_ligne_invalide,
    )

    synonymes = _table_synonymes(config)
    ignorees = {normaliser_nom(c) for c in config.get("colonnes_ignorees") or []}
    renommage, correspondance, inattendues = {}, {}, []
    for col in df.columns:
        canonique = synonymes.get(normaliser_nom(col))
        if canonique and canonique not in correspondance:
            renommage[col] = canonique
            correspondance[canonique] = col
        elif normaliser_nom(col) not in ignorees:
            inattendues.append(col)
    df = df.rename(columns=renommage)
    # Numéro de ligne tel que vu dans Excel (en-tête = ligne 1)
    df.index = pd.RangeIndex(2, len(df) + 2, name="ligne")

    return Catalogue(
        df=df,
        nom_fichier=nom_fichier or "catalogue.csv",
        encodage=encodage,
        separateur=separateur,
        correspondance=correspondance,
        colonnes_inattendues=inattendues,
        lignes_mal_formees=lignes_mal_formees,
    )
