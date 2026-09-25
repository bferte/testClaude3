"""Point d'entrée unique : enchaîne contrôles par onglet, contrôles croisés, comparaison et score."""
from __future__ import annotations

import pandas as pd

from . import comparaison, controles, detection, referentiels
from .modele import SEVERITES, Anomalie, Catalogue, Classeur, ResultatAnalyse
from .outils import nettoyer

CONTROLES = [
    controles.controle_structure,
    controles.controle_completude,
    controles.controle_unicite,
    controles.controle_validite,
    controles.controle_valeurs_autorisees,
    controles.controle_coherence,
    controles.controle_comparaisons,
    controles.controle_suppressions_declarees,
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


def _en_classeur(source: Catalogue | Classeur | None, config: dict) -> Classeur | None:
    if source is None or isinstance(source, Classeur):
        return source
    return Classeur(source.nom_fichier, {source.nom: source}, profil=config.get("nom", ""))


def _situer(anomalies: list[Anomalie], onglet: str | None, multi: bool) -> list[Anomalie]:
    """Précise l'onglet concerné dans le titre quand le classeur en contient plusieurs."""
    for a in anomalies:
        a.onglet = a.onglet or onglet
        if multi and onglet and not a.titre.startswith("["):
            a.titre = f"[{onglet}] {a.titre}"
    return anomalies


def analyser(source: Catalogue | Classeur, config: dict, precedent: Catalogue | Classeur | None = None) -> ResultatAnalyse:
    classeur, prec = _en_classeur(source, config), _en_classeur(precedent, config)
    multi = len(classeur.tableaux) > 1
    nb_lignes_brut = classeur.nb_lignes

    anomalies: list[Anomalie] = []
    for nom, cat in classeur.tableaux.items():
        trouvees = _retirer_lignes_vides(cat, config)
        for controle in CONTROLES:
            trouvees += controle(cat, config)
        anomalies += _situer(trouvees, cat.onglet, multi)
    for controle in referentiels.TOUS:
        anomalies += controle(classeur, config)

    if prec is not None:
        for cat in prec.tableaux.values():
            _retirer_lignes_vides(cat, config)
        for nom, cat in classeur.tableaux.items():
            ancien = prec.tableaux.get(nom) or (next(iter(prec.tableaux.values())) if not multi else None)
            if ancien is not None:
                anomalies += _situer(comparaison.comparer(cat, ancien, config), cat.onglet, multi)
        disparus = [n for n in prec.tableaux if n not in classeur.tableaux and multi]
        if disparus:
            anomalies.append(Anomalie("EVOL_ONGLETS", "majeur", "Évolution",
                                      f"Onglet(s) absent(s) par rapport à la version précédente : {', '.join(disparus)}",
                                      len(disparus), lignes_touchees=0))

    anomalies.sort(key=lambda a: (SEVERITES.index(a.severite), -a.nb))
    score = calculer_score(anomalies, classeur.nb_lignes, config)

    def _distincts(col):
        valeurs = [nettoyer(c.df[col]) for c in classeur.tableaux.values() if c.a(col)]
        return int(pd.concat(valeurs).replace("", pd.NA).nunique()) if valeurs else None

    principal = classeur.principal
    stats = {
        "lignes": nb_lignes_brut,
        "lignes_par_onglet": {n: len(c.df) for n, c in classeur.tableaux.items()},
        "referentiels": {n: len(d) for n, d in classeur.referentiels.items()},
        "lignes_precedent": prec.nb_lignes if prec is not None else None,
        "encodage": principal.encodage,
        "separateur": principal.separateur,
        "correspondance": principal.correspondance,
        "nb_references": _distincts("reference"),
        "nb_marques": _distincts("marque"),
    }
    return ResultatAnalyse(classeur, prec, anomalies, score, verdict(score, anomalies), stats)
