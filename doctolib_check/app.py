"""Interface web locale (Streamlit) - lancer avec lancer.bat ou : streamlit run app.py"""
from __future__ import annotations

import argparse
import asyncio
import io
import re
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from verifier_doctolib import (
    INDETERMINE,
    NON_RESERVABLE,
    RESERVABLE,
    Resultat,
    Sauvegarde,
    colonne_url,
    compter,
    ecrire_excel,
    extraire_urls,
    lire_tableau,
    verifier,
)

if sys.platform == "win32":  # Playwright lance Chromium en sous-processus : boucle Proactor requise
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

DOSSIER_RESULTATS = Path(__file__).with_name("resultats")

st.set_page_config(page_title="Contrôle Doctolib", page_icon="🩺", layout="wide")
etat = st.session_state


def octets_excel(df: pd.DataFrame) -> bytes:
    tampon = io.BytesIO()
    df.to_excel(tampon, index=False)
    return tampon.getvalue()


def afficher_resultats(df: pd.DataFrame, nom: str) -> None:
    non_reservables = df[df["Statut"] == NON_RESERVABLE].reset_index(drop=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("URL contrôlées", len(df))
    c2.metric("Réservables", int((df["Statut"] == RESERVABLE).sum()))
    c3.metric("Non réservables", len(non_reservables))
    c4.metric("En erreur", int((df["Statut"] == INDETERMINE).sum()))

    d1, d2 = st.columns(2)
    d1.download_button("⬇ Résultats complets (.xlsx)", octets_excel(df), f"{nom}_resultats.xlsx",
                       width="stretch")
    d2.download_button("⬇ Non réservables uniquement (.xlsx)", octets_excel(non_reservables),
                       f"{nom}_resultats_non_reservables.xlsx", type="primary", width="stretch")

    filtre = st.radio("Afficher", ["Tous", NON_RESERVABLE, RESERVABLE, INDETERMINE], horizontal=True)
    vue = df if filtre == "Tous" else df[df["Statut"] == filtre]
    st.dataframe(vue, width="stretch", hide_index=True,
                 column_config={"URL": st.column_config.LinkColumn("URL")})


# ----------------------------------------------------------------- Barre latérale : réglages
with st.sidebar:
    st.header("Réglages")
    onglets = st.slider("Onglets en parallèle", 1, 10, 4,
                        help="Plus d'onglets = plus rapide, mais plus de charge et plus de risque de captcha.")
    timeout = st.number_input("Délai max de chargement (s)", 5, 120, 30)
    attente = st.number_input("Attente après chargement (s)", 0.0, 15.0, 2.0, step=0.5,
                              help="Laisse le temps au contenu JavaScript de s'afficher.")
    pause = st.number_input("Pause entre deux URL (s)", 0.0, 10.0, 1.0, step=0.5)
    essais = st.number_input("Essais par URL en cas d'erreur", 1, 5, 3)
    sans_images = st.checkbox("Ne pas charger les images (plus rapide)", value=True)
    chrome = st.checkbox("Utiliser Google Chrome installé",
                         help="Si Chromium n'a pas pu être installé (poste d'entreprise).")
    visible = st.checkbox("Afficher le navigateur")
    st.caption("Si beaucoup d'URL finissent en « captcha » : 2 onglets et 3 s de pause.")

# ----------------------------------------------------------------- Page principale
st.title("🩺 Contrôle des fiches Doctolib")
st.write("Déposez la liste des URL (CSV ou Excel). Chaque fiche est ouverte et la mention "
         "**« n'est pas réservable en ligne »** y est recherchée.")

fichier = st.file_uploader("Fichier des URL", type=["csv", "txt", "xlsx", "xls"])
if fichier is None:
    st.info("Glissez-déposez un fichier ci-dessus : une colonne contient les URL Doctolib.")
    st.stop()

try:
    tableau = lire_tableau(fichier, fichier.name)
except Exception as e:  # noqa: BLE001
    st.error(f"Lecture impossible : {e}")
    st.stop()

colonnes = list(tableau.columns)
devinee = colonne_url(tableau)
colonne = st.selectbox("Colonne des URL", colonnes, index=colonnes.index(devinee) if devinee in colonnes else 0)
urls = extraire_urls(tableau, colonne)
if not urls:
    st.warning("Aucune URL trouvée dans cette colonne.")
    st.stop()

nom = re.sub(r"[^\w-]+", "_", Path(fichier.name).stem)
sortie = DOSSIER_RESULTATS / f"{nom}_resultats.xlsx"
sauvegarde = Sauvegarde(sortie, frequence=10)
deja = Sauvegarde(sortie, 10).reprendre()

st.write(f"**{len(urls)} URL** à contrôler.")
limite = st.number_input("Ne traiter que les N premières (0 = toutes)", 0, len(urls), 0,
                         help="Pour un essai rapide avant de tout lancer.")
reprendre = False
if deja:
    reprendre = st.checkbox(f"Reprendre le traitement précédent de ce fichier ({deja} URL déjà faites)", value=True)

if st.button("▶ Lancer le contrôle", type="primary"):
    DOSSIER_RESULTATS.mkdir(exist_ok=True)
    a_controler = urls[:limite] if limite else urls
    if reprendre:
        sauvegarde.reprendre()
    sauvegarde.demarrer(reprendre)
    a_traiter = [u for u in a_controler if u not in sauvegarde.resultats]

    args = argparse.Namespace(onglets=onglets, timeout=timeout, attente=attente, pause=pause, essais=int(essais),
                              sans_images=sans_images, chrome=chrome, visible=visible, executable=None)
    barre = st.progress(0.0, text="Démarrage du navigateur…")
    compteurs = st.empty()
    debut = time.monotonic()
    faits = 0

    def notifier(res: Resultat) -> None:
        global faits
        faits += 1
        ecoule = time.monotonic() - debut
        reste = ecoule / faits * (len(a_traiter) - faits)
        barre.progress(faits / len(a_traiter),
                       text=f"{faits} / {len(a_traiter)} — reste environ {reste / 60:.0f} min")
        compteurs.caption(f"Non réservables : {compter(sauvegarde, NON_RESERVABLE)} · "
                          f"En erreur : {compter(sauvegarde, INDETERMINE)}")

    if a_traiter:
        st.caption("Ne fermez pas cette page pendant le contrôle. En cas d'arrêt, les résultats déjà obtenus "
                   "sont conservés : redéposez le même fichier et cochez « Reprendre ».")
        try:
            asyncio.run(verifier(a_traiter, args, sauvegarde, notifier))
        except Exception as e:  # noqa: BLE001
            st.error(f"Le contrôle s'est arrêté : {e}")
            if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
                st.info("Chromium n'est pas installé : lancez `python -m playwright install chromium`, "
                        "ou cochez « Utiliser Google Chrome installé ».")
    barre.progress(1.0, text="Terminé")

    df = sauvegarde.exporter(ordre=urls)
    ecrire_excel(df[df["Statut"] == NON_RESERVABLE].reset_index(drop=True),
                 sortie.with_name(f"{nom}_resultats_non_reservables.xlsx"))
    etat["resultats"] = (df, nom)

if "resultats" in etat and etat["resultats"][1] == nom:
    st.divider()
    afficher_resultats(*etat["resultats"])
    st.caption(f"Copie enregistrée dans {DOSSIER_RESULTATS}")
