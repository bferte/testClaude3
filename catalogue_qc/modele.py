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

DOSSIER_PROFILS = Path(__file__).resolve().parent.parent / "config" / "profils"


def charger_config(chemin: str | Path | None = None) -> dict:
    """Charge un profil de règles ; sans argument, le profil par défaut."""
    if chemin is None:
        profils = charger_profils()
        return next((p for p in profils.values() if p.get("par_defaut")), next(iter(profils.values())))
    with open(chemin, encoding="utf-8") as f:
        return yaml.safe_load(f)


def charger_profils(dossier: Path = DOSSIER_PROFILS) -> dict[str, dict]:
    """Tous les profils de config/profils/*.yaml, indexés par leur nom affiché."""
    profils = {}
    for chemin in sorted(dossier.glob("*.yaml")):
        config = charger_config(chemin)
        profils[config.get("nom", chemin.stem)] = config
    return profils


@dataclass
class Catalogue:
    """Un tableau d'articles (fichier CSV ou onglet Excel), colonnes renommées en noms canoniques."""

    df: pd.DataFrame
    nom_fichier: str
    encodage: str
    separateur: str
    correspondance: dict[str, str]  # nom canonique -> en-tête d'origine
    colonnes_inattendues: list[str]
    lignes_mal_formees: list[str] = field(default_factory=list)
    onglet: str | None = None
    # Listes de valeurs autorisées lues dans l'en-tête du fichier : colonne -> {code: libellé}
    enumerations: dict[str, dict[str, str]] = field(default_factory=dict)
    # Colonnes au format « CODE - Libellé » annoncé dans l'en-tête
    formats_code_libelle: list[str] = field(default_factory=list)

    def a(self, colonne: str) -> bool:
        return colonne in self.df.columns

    @property
    def nom(self) -> str:
        return self.onglet or self.nom_fichier


@dataclass
class Classeur:
    """Un fichier fournisseur complet : un ou plusieurs tableaux d'articles + référentiels."""

    nom_fichier: str
    tableaux: dict[str, Catalogue]
    referentiels: dict[str, pd.DataFrame] = field(default_factory=dict)
    profil: str = ""

    @property
    def principal(self) -> Catalogue:
        return max(self.tableaux.values(), key=lambda c: len(c.df))

    @property
    def nb_lignes(self) -> int:
        return sum(len(c.df) for c in self.tableaux.values())


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
    onglet: str | None = None

    def __post_init__(self):
        if self.severite not in SEVERITES:
            raise ValueError(f"Sévérité inconnue : {self.severite}")
        if not self.lignes_touchees:
            self.lignes_touchees = self.nb


@dataclass
class ResultatAnalyse:
    classeur: Classeur
    precedent: Classeur | None
    anomalies: list[Anomalie]
    score: int
    verdict: str
    stats: dict

    @property
    def nom_fichier(self) -> str:
        return self.classeur.nom_fichier

    def par_severite(self, severite: str) -> list[Anomalie]:
        return [a for a in self.anomalies if a.severite == severite]

    def nb(self, severite: str) -> int:
        return len(self.par_severite(severite))

    def synthese_texte(self) -> str:
        onglets = ""
        if len(self.classeur.tableaux) > 1:
            onglets = " : " + ", ".join(f"{n} {len(c.df)}" for n, c in self.classeur.tableaux.items())
        lignes = [
            f"Catalogue : {self.nom_fichier} ({self.stats['lignes']} lignes{onglets})",
            f"Profil de règles : {self.classeur.profil}",
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
