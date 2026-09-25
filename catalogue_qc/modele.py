"""Structures de données partagées par tous les modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

SEVERITES = ["critique", "majeur", "mineur", "info"]
LIBELLES_SEVERITE = {
    "critique": "Critique",
    "majeur": "Majeur",
    "mineur": "Mineur",
    "info": "Information",
}

CONFIG_PAR_DEFAUT = Path(__file__).resolve().parent.parent / "config" / "regles.yaml"


def charger_config(chemin: str | Path | None = None) -> dict:
    with open(chemin or CONFIG_PAR_DEFAUT, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Catalogue:
    """Un fichier CSV chargé, avec ses colonnes renommées en noms canoniques."""

    df: pd.DataFrame
    nom_fichier: str
    encodage: str
    separateur: str
    correspondance: dict[str, str]  # nom canonique -> en-tête d'origine
    colonnes_inattendues: list[str]
    lignes_mal_formees: list[str] = field(default_factory=list)

    def a(self, colonne: str) -> bool:
        return colonne in self.df.columns


@dataclass
class Anomalie:
    code: str
    severite: str
    categorie: str
    titre: str
    nb: int
    conseil: str = ""
    lignes_touchees: int = 0
    exemples: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        if self.severite not in SEVERITES:
            raise ValueError(f"Sévérité inconnue : {self.severite}")
        if not self.lignes_touchees:
            self.lignes_touchees = self.nb


@dataclass
class ResultatAnalyse:
    catalogue: Catalogue
    precedent: Catalogue | None
    anomalies: list[Anomalie]
    score: int
    verdict: str
    stats: dict

    def par_severite(self, severite: str) -> list[Anomalie]:
        return [a for a in self.anomalies if a.severite == severite]

    def nb(self, severite: str) -> int:
        return len(self.par_severite(severite))

    def synthese_texte(self) -> str:
        lignes = [
            f"Catalogue : {self.catalogue.nom_fichier} ({self.stats['lignes']} lignes)",
        ]
        if self.precedent is not None:
            lignes.append(f"Comparé à : {self.precedent.nom_fichier} ({self.stats['lignes_precedent']} lignes)")
        lignes += [
            "",
            f"Qualité du catalogue : {self.score}/100  ->  {self.verdict}",
            f"{self.nb('critique')} anomalie(s) critique(s), {self.nb('majeur')} majeure(s), "
            f"{self.nb('mineur')} mineure(s), {self.nb('info')} information(s)",
        ]
        for sev in SEVERITES:
            anomalies = self.par_severite(sev)
            if anomalies:
                lignes += ["", f"{LIBELLES_SEVERITE[sev]} :"]
                lignes += [f"- {a.titre}" for a in anomalies]
        return "\n".join(lignes)
