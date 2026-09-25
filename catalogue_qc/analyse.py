"""Point d'entrée unique : enchaîne chargement, contrôles, comparaison et score."""
from __future__ import annotations

import pandas as pd

from . import comparaison, controles, detection
from .modele import SEVERITES, Anomalie, Catalogue, ResultatAnalyse
from .outils import nettoyer

CONTROLES = [
    controles.controle_structure,
    controles.controle_completude,
    controles.controle_unicite,
    controles.controle_validite,
    controles.controle_coherence,
    *detection.TOUS,
]


def calculer_score(anomalies: list[Anomalie], nb_lignes: int, config: dict) -> int:
    """100 moins une pénalité par anomalie, pondérée par la sévérité et la part de lignes touchées."""
    penalite = 0.0
    for a in anomalies:
        regle = config["score"][a.severite]
        part = min(a.lignes_touchees / max(nb_lignes, 1), 1.0)
        penalite += min(regle["base"] + part * 100 * regle["facteur"], regle["plafond"])
    return max(0, round(100 - penalite))


def verdict(score: int, anomalies: list[Anomalie]) -> str:
    if any(a.severite == "critique" for a in anomalies):
        return "BLOQUANT - corrections obligatoires avant intégration"
    if score >= 85:
        return "INTÉGRABLE"
    return "À VÉRIFIER - intégration possible après revue des anomalies majeures"


def _retirer_lignes_vides(cat: Catalogue, config: dict) -> list[Anomalie]:
    vides = cat.df.apply(nettoyer).eq("").all(axis=1)
    if not vides.any():
        return []
    cat.df = cat.df[~vides]
    return [Anomalie("LIGNES_VIDES", "mineur", "Structure", f"{int(vides.sum())} ligne(s) entièrement vide(s) (ignorées)",
                     int(vides.sum()), exemples=pd.DataFrame({"ligne": vides[vides].index[: config["seuils"]["exemples_max"]]}))]


def analyser(catalogue: Catalogue, config: dict, precedent: Catalogue | None = None) -> ResultatAnalyse:
    nb_lignes_brut = len(catalogue.df)
    anomalies = _retirer_lignes_vides(catalogue, config)
    if precedent is not None:
        _retirer_lignes_vides(precedent, config)

    for controle in CONTROLES:
        anomalies += controle(catalogue, config)
    if precedent is not None:
        anomalies += comparaison.comparer(catalogue, precedent, config)

    anomalies.sort(key=lambda a: (SEVERITES.index(a.severite), -a.nb))
    score = calculer_score(anomalies, len(catalogue.df), config)
    stats = {
        "lignes": nb_lignes_brut,
        "colonnes": len(catalogue.df.columns),
        "lignes_precedent": len(precedent.df) if precedent is not None else None,
        "encodage": catalogue.encodage,
        "separateur": catalogue.separateur,
        "correspondance": catalogue.correspondance,
        "nb_references": int(nettoyer(catalogue.df["reference"]).replace("", pd.NA).nunique())
        if catalogue.a("reference") else None,
        "nb_marques": int(nettoyer(catalogue.df["marque"]).replace("", pd.NA).nunique())
        if catalogue.a("marque") else None,
    }
    return ResultatAnalyse(catalogue, precedent, anomalies, score, verdict(score, anomalies), stats)
