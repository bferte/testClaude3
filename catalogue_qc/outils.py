"""Fonctions utilitaires de normalisation et de calcul."""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

RE_NOTATION_SCIENTIFIQUE = re.compile(r"^\d+([.,]\d+)?E\+?\d+$", re.IGNORECASE)


def nettoyer(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def en_nombre(s: pd.Series) -> pd.Series:
    """Convertit '12,50 €' / '1 234.5' en nombre ; NaN si impossible."""
    t = (
        nettoyer(s)
        .str.replace(" ", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(t, errors="coerce")


def en_date(s: pd.Series) -> pd.Series:
    """Accepte AAAA-MM-JJ [hh:mm:ss] et JJ/MM/AAAA ; NaT si illisible."""
    t = nettoyer(s)
    iso = pd.to_datetime(t, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y"):
        iso = iso.fillna(pd.to_datetime(t, format=fmt, errors="coerce"))
    return iso


def sans_accents(texte: str) -> str:
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()


def cle_texte(texte: str) -> str:
    """'Ray-Ban ' -> 'RAYBAN' : sert à regrouper des variantes d'écriture."""
    return re.sub(r"[^A-Z0-9]", "", sans_accents(str(texte)).upper())


def cle_reference(ref: str) -> str:
    """Clé tolérante aux confusions de saisie : casse, séparateurs, O/0, I/1."""
    return cle_texte(ref).replace("O", "0").replace("I", "1")


def signature(valeur: str) -> str:
    """'RB-1234x' -> 'AA-9999A' : décrit le format d'un code."""
    v = sans_accents(str(valeur).strip().upper())
    return re.sub(r"[0-9]", "9", re.sub(r"[A-Z]", "A", v))


def ean_valide(code: str) -> bool:
    """Contrôle longueur (8/12/13/14) et clé de contrôle GTIN."""
    if not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return False
    chiffres = [int(c) for c in code]
    corps = chiffres[:-1][::-1]
    total = sum(d * 3 if i % 2 == 0 else d for i, d in enumerate(corps))
    return (10 - total % 10) % 10 == chiffres[-1]


def zscore_robuste(valeurs: pd.Series) -> pd.Series:
    """Z-score basé sur la médiane (insensible aux valeurs extrêmes), en échelle log."""
    v = np.log10(valeurs.where(valeurs > 0))
    med = v.median()
    mad = (v - med).abs().median()
    if not mad or np.isnan(mad):
        mad = (v - med).abs().mean() or 1.0
    return 0.6745 * (v - med) / mad
