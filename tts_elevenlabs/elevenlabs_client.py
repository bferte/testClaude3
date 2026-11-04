"""Client minimal de l'API ElevenLabs (text to speech).

Authentification : en-tête ``xi-api-key`` (https://elevenlabs.io/docs/api-reference/authentication).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import requests

URL_API = "https://api.elevenlabs.io"
FORMATS_SORTIE = {
    "MP3 44,1 kHz 128 kb/s": ("mp3_44100_128", "audio/mpeg", "mp3"),
    "MP3 22,05 kHz 32 kb/s (léger)": ("mp3_22050_32", "audio/mpeg", "mp3"),
    "PCM 16 kHz (WAV brut)": ("pcm_16000", "audio/L16", "pcm"),
}
LIMITE_CARACTERES = 5000


class ErreurElevenLabs(Exception):
    """Erreur renvoyée par l'API (clé invalide, quota dépassé, etc.)."""


@dataclass
class Voix:
    id: str
    nom: str
    categorie: str = ""
    langue: str = ""

    @property
    def libelle(self) -> str:
        details = ", ".join(x for x in (self.langue, self.categorie) if x)
        return f"{self.nom} ({details})" if details else self.nom


@dataclass
class Modele:
    id: str
    nom: str


def cle_par_defaut() -> str:
    return os.environ.get("ELEVENLABS_API_KEY", "")


class ClientElevenLabs:
    def __init__(self, cle_api: str, session: requests.Session | None = None, delai: float = 60):
        if not cle_api or not cle_api.strip():
            raise ErreurElevenLabs("Clé API manquante.")
        self.session = session or requests.Session()
        self.session.headers.update({"xi-api-key": cle_api.strip()})
        self.delai = delai

    # ------------------------------------------------------------------ outils
    def _requete(self, methode: str, chemin: str, **kwargs) -> requests.Response:
        try:
            reponse = self.session.request(methode, URL_API + chemin, timeout=self.delai, **kwargs)
        except requests.RequestException as exc:
            raise ErreurElevenLabs(f"Impossible de joindre ElevenLabs : {exc}") from exc
        if not reponse.ok:
            raise ErreurElevenLabs(_message_erreur(reponse))
        return reponse

    # --------------------------------------------------------------- endpoints
    def voix(self) -> list[Voix]:
        donnees = self._requete("GET", "/v1/voices").json()
        resultat = []
        for v in donnees.get("voices", []):
            labels = v.get("labels") or {}
            resultat.append(Voix(id=v["voice_id"], nom=v.get("name", v["voice_id"]),
                                 categorie=v.get("category", "") or "",
                                 langue=labels.get("language", "") or labels.get("accent", "") or ""))
        return sorted(resultat, key=lambda v: v.nom.lower())

    def modeles(self) -> list[Modele]:
        donnees = self._requete("GET", "/v1/models").json()
        return [Modele(id=m["model_id"], nom=m.get("name", m["model_id"]))
                for m in donnees if m.get("can_do_text_to_speech", True)]

    def synthetiser(self, texte: str, voix_id: str, modele_id: str = "eleven_multilingual_v2",
                    format_sortie: str = "mp3_44100_128", stabilite: float = 0.5,
                    similarite: float = 0.75, style: float = 0.0, vitesse: float = 1.0) -> bytes:
        texte = (texte or "").strip()
        if not texte:
            raise ErreurElevenLabs("Le texte est vide.")
        if len(texte) > LIMITE_CARACTERES:
            raise ErreurElevenLabs(f"Texte trop long ({len(texte)} caractères, maximum {LIMITE_CARACTERES}).")
        corps = {
            "text": texte,
            "model_id": modele_id,
            "voice_settings": {"stability": stabilite, "similarity_boost": similarite,
                               "style": style, "speed": vitesse},
        }
        reponse = self._requete("POST", f"/v1/text-to-speech/{voix_id}",
                                params={"output_format": format_sortie}, json=corps,
                                headers={"Accept": "audio/*"})
        return reponse.content


def _message_erreur(reponse: requests.Response) -> str:
    detail = ""
    try:
        contenu = reponse.json().get("detail", "")
        detail = contenu.get("message", str(contenu)) if isinstance(contenu, dict) else str(contenu)
    except ValueError:
        detail = reponse.text[:300]
    if reponse.status_code == 401:
        return f"Clé API refusée (401). {detail}".strip()
    if reponse.status_code == 429:
        return f"Trop de requêtes ou quota atteint (429). {detail}".strip()
    return f"Erreur ElevenLabs {reponse.status_code}. {detail}".strip()
