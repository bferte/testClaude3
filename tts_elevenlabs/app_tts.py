"""Petite appli text to speech ElevenLabs - lancer avec lancer_tts.bat ou : streamlit run app_tts.py"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from elevenlabs_client import (FORMATS_SORTIE, LIMITE_CARACTERES, ClientElevenLabs,
                               ErreurElevenLabs, MODELES_STANDARD, VOIX_STANDARD,
                               Voix, cle_par_defaut)

st.set_page_config(page_title="Text to speech ElevenLabs", page_icon="🔊")
etat = st.session_state
etat.setdefault("historique", [])


def _ou_liste_standard(appel, standard):
    """Liste du compte, ou liste standard si la clé n'a pas la permission de lecture (401/403)."""
    try:
        return appel(), False
    except ErreurElevenLabs as exc:
        if exc.statut in (401, 403) and "permission" in str(exc).lower():
            return list(standard), True
        raise


@st.cache_data(ttl=600, show_spinner=False)
def charger_catalogue(cle: str):
    client = ClientElevenLabs(cle)
    voix, voix_std = _ou_liste_standard(client.voix, VOIX_STANDARD)
    modeles, modeles_std = _ou_liste_standard(client.modeles, MODELES_STANDARD)
    return voix, modeles, voix_std or modeles_std


# ----------------------------------------------------------------- Barre latérale
with st.sidebar:
    st.header("Connexion")
    cle = st.text_input("Clé API ElevenLabs", value=cle_par_defaut(), type="password",
                        help="Profil ElevenLabs > API Keys. Peut aussi être fournie par la variable "
                             "d'environnement ELEVENLABS_API_KEY. Elle n'est jamais enregistrée.")
    if not cle:
        st.info("Saisissez votre clé API pour commencer.")
        st.stop()
    try:
        voix, modeles, listes_standard = charger_catalogue(cle)
    except ErreurElevenLabs as exc:
        st.error(str(exc))
        st.stop()
    if listes_standard:
        st.info("Clé à permissions restreintes : voix et modèles standard proposés. "
                "Ajoutez « Voices : read » à la clé pour voir les voix de votre compte.")
    else:
        st.success(f"Connecté : {len(voix)} voix disponibles.")

    st.header("Réglages")
    if not voix:
        st.warning("Aucune voix sur ce compte.")
        st.stop()
    voix_choisie = st.selectbox("Voix", voix, format_func=lambda v: v.libelle)
    id_perso = st.text_input("…ou ID d'une autre voix", help="ID copié depuis la Voice Library d'ElevenLabs.")
    if id_perso.strip():
        voix_choisie = Voix(id_perso.strip(), id_perso.strip())
    ids_modeles = [m.id for m in modeles] or ["eleven_multilingual_v2"]
    noms_modeles = {m.id: m.nom for m in modeles}
    defaut = ids_modeles.index("eleven_multilingual_v2") if "eleven_multilingual_v2" in ids_modeles else 0
    modele = st.selectbox("Modèle", ids_modeles, index=defaut, format_func=lambda i: noms_modeles.get(i, i))
    nom_format = st.selectbox("Format", list(FORMATS_SORTIE))
    with st.expander("Paramètres de voix"):
        stabilite = st.slider("Stabilité", 0.0, 1.0, 0.5, 0.05)
        similarite = st.slider("Similarité", 0.0, 1.0, 0.75, 0.05)
        style = st.slider("Style", 0.0, 1.0, 0.0, 0.05)
        vitesse = st.slider("Vitesse", 0.7, 1.2, 1.0, 0.05)

# ----------------------------------------------------------------- Zone principale
st.title("🔊 Text to speech")
texte = st.text_area("Texte à lire", height=200, max_chars=LIMITE_CARACTERES,
                     placeholder="Bonjour ! Tapez ici le texte à transformer en voix.")

if st.button("Générer l'audio", type="primary", disabled=not texte.strip()):
    code_format, mime, extension = FORMATS_SORTIE[nom_format]
    with st.spinner("Synthèse en cours..."):
        try:
            audio = ClientElevenLabs(cle).synthetiser(
                texte, voix_choisie.id, modele, code_format,
                stabilite=stabilite, similarite=similarite, style=style, vitesse=vitesse)
        except ErreurElevenLabs as exc:
            st.error(str(exc))
        else:
            etat["historique"].insert(0, {
                "heure": datetime.now().strftime("%H:%M:%S"), "voix": voix_choisie.nom,
                "texte": texte.strip(), "audio": audio, "mime": mime, "extension": extension})

for i, item in enumerate(etat["historique"]):
    with st.container(border=True):
        apercu = item["texte"] if len(item["texte"]) <= 120 else item["texte"][:120] + "…"
        st.markdown(f"**{item['heure']} · {item['voix']}** — {apercu}")
        if item["extension"] == "mp3":
            st.audio(item["audio"], format=item["mime"])
        else:
            st.caption("Format PCM brut : à télécharger (pas de lecture directe dans le navigateur).")
        st.download_button("Télécharger", item["audio"], key=f"dl{i}",
                           file_name=f"tts_{item['heure'].replace(':', '')}.{item['extension']}",
                           mime=item["mime"])
