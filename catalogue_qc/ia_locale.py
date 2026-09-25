"""Assistant IA local via Ollama (https://ollama.com).

Garanties de confidentialité :
- seules les URL locales (localhost / 127.0.0.1) sont acceptées ;
- les variables de proxy système sont ignorées (trust_env=False) : aucune donnée
  ne peut transiter par un proxy d'entreprise ou Internet.

L'IA ne décide de rien : elle reformule, explique et propose. Les contrôles
déterministes restent la source de vérité du score.
"""
from __future__ import annotations

from urllib.parse import urlparse

import requests

from .modele import LIBELLES_SEVERITE, Anomalie, Catalogue, ResultatAnalyse

HOTES_LOCAUX = {"localhost", "127.0.0.1", "::1"}

SYSTEME = (
    "Tu es un expert en qualité des données produit (PIM/ERP) dans le commerce de détail. "
    "Tu analyses des catalogues fournisseurs avant leur intégration dans le système d'information. "
    "Réponds en français, de façon concise et structurée, pour un public métier non technique. "
    "N'invente aucune donnée : appuie-toi uniquement sur les éléments fournis. "
    "Si une information manque pour conclure, dis-le."
)


class IAIndisponible(RuntimeError):
    pass


class ClientOllama:
    def __init__(self, config: dict):
        ia = config.get("ia", {})
        self.url = ia.get("url", "http://localhost:11434").rstrip("/")
        self.modele = ia.get("modele", "mistral")
        self.temperature = ia.get("temperature", 0.2)
        self.timeout = ia.get("timeout_s", 300)
        self.lignes_echantillon = ia.get("lignes_echantillon", 40)
        if urlparse(self.url).hostname not in HOTES_LOCAUX:
            raise ValueError(f"URL IA refusée ({self.url}) : seule une IA locale est autorisée.")
        self.session = requests.Session()
        self.session.trust_env = False

    def modeles_disponibles(self) -> list[str]:
        try:
            r = self.session.get(f"{self.url}/api/tags", timeout=3)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except requests.RequestException:
            return []

    def disponible(self) -> bool:
        return bool(self.modeles_disponibles())

    def demander(self, consigne: str) -> str:
        try:
            r = self.session.post(f"{self.url}/api/chat", timeout=self.timeout, json={
                "model": self.modele,
                "stream": False,
                "options": {"temperature": self.temperature},
                "messages": [{"role": "system", "content": SYSTEME}, {"role": "user", "content": consigne}],
            })
            r.raise_for_status()
        except requests.RequestException as exc:
            raise IAIndisponible(
                f"Ollama injoignable ou modèle « {self.modele} » absent ({exc}). "
                f"Lancer Ollama puis : ollama pull {self.modele}"
            ) from exc
        return r.json()["message"]["content"].strip()

    # ------------------------------------------------------------------
    # Cas d'usage
    # ------------------------------------------------------------------
    def resumer(self, res: ResultatAnalyse) -> str:
        """Synthèse managériale + risques d'intégration + plan d'action priorisé."""
        return self.demander(
            "Voici le résultat des contrôles automatiques d'un catalogue fournisseur.\n\n"
            f"{contexte_anomalies(res)}\n\n"
            "Rédige :\n"
            "1. SYNTHÈSE (3 à 5 phrases) : le catalogue est-il intégrable en l'état ?\n"
            "2. RISQUES D'INTÉGRATION : pour chaque anomalie critique ou majeure, la conséquence concrète "
            "si on intègre sans corriger (rejet, doublon de fiche, prix faux en magasin, perte d'historique...).\n"
            "3. ACTIONS PRIORITAIRES : liste numérotée, en distinguant ce que l'on peut corriger en interne "
            "et ce qu'il faut demander au fournisseur.\n"
            "4. MESSAGE AU FOURNISSEUR : un court e-mail poli demandant les corrections nécessaires."
        )

    def proposer_corrections(self, anomalie: Anomalie, max_lignes: int = 25) -> str:
        extrait = anomalie.exemples.head(max_lignes).to_csv(sep=";", index=False)
        return self.demander(
            f"Anomalie détectée : {anomalie.titre}\n"
            f"Sévérité : {LIBELLES_SEVERITE[anomalie.severite]}\nConseil de la règle : {anomalie.conseil}\n\n"
            f"Lignes concernées (CSV) :\n{extrait}\n"
            "Pour chaque ligne, propose une correction sous forme de tableau Markdown avec les colonnes : "
            "ligne | colonne | valeur actuelle | valeur proposée | confiance (haute/moyenne/faible) | justification. "
            "Si aucune correction fiable n'est possible (ex. donnée à redemander au fournisseur), indique-le "
            "avec la confiance « faible »."
        )

    def incoherences_semantiques(self, cat: Catalogue) -> str:
        """Recherche d'incohérences de sens que les règles ne voient pas."""
        n = min(self.lignes_echantillon, len(cat.df))
        echantillon = cat.df.sample(n, random_state=1).reset_index().to_csv(sep=";", index=False)
        return self.demander(
            f"Voici un échantillon de {n} lignes d'un catalogue fournisseur (colonne « ligne » = numéro de ligne).\n\n"
            f"{echantillon}\n"
            "Les contrôles classiques (champs vides, doublons, EAN, prix) ont déjà été faits. "
            "Cherche uniquement des incohérences de SENS, par exemple : libellé qui contredit la couleur, "
            "la marque ou la catégorie ; taille improbable pour le type de produit ; libellé tronqué, "
            "en majuscules/minuscules incohérentes ou dans une autre langue ; catégorie mal affectée ; "
            "prix incohérent avec le positionnement de la marque.\n"
            "Réponds par une liste : numéro de ligne, problème, correction suggérée. "
            "S'il n'y a rien de probant, réponds « Aucune incohérence évidente »."
        )


def contexte_anomalies(res: ResultatAnalyse, nb_exemples: int = 3) -> str:
    """Résumé compact des anomalies (le modèle ne reçoit jamais le fichier complet)."""
    lignes = [
        f"Fichier : {res.catalogue.nom_fichier}, {res.stats['lignes']} lignes, "
        f"{res.stats.get('nb_references') or '?'} références, {res.stats.get('nb_marques') or '?'} marques.",
        f"Comparé à la version précédente : {'oui' if res.precedent else 'non'}.",
        f"Score qualité : {res.score}/100. Verdict des règles : {res.verdict}.",
        "",
        "Anomalies :",
    ]
    for a in res.anomalies:
        lignes.append(f"- [{LIBELLES_SEVERITE[a.severite]}] {a.titre}")
        if not a.exemples.empty and "commentaire" in a.exemples.columns:
            for c in a.exemples["commentaire"].dropna().astype(str).unique()[:nb_exemples]:
                lignes.append(f"    ex. {c}")
    return "\n".join(lignes)
