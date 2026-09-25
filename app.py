"""Interface web locale (Streamlit) - lancer avec lancer.bat ou : streamlit run app.py"""
from __future__ import annotations

import streamlit as st

from catalogue_qc.analyse import analyser
from catalogue_qc.chargement import lire_classeur
from catalogue_qc.ia_locale import ClientOllama, IAIndisponible
from catalogue_qc.modele import LIBELLES_SEVERITE, charger_config, charger_profils
from catalogue_qc.rapport import tableau_synthese, vers_excel, vers_html

st.set_page_config(page_title="Contrôle catalogue fournisseur", page_icon="🔎", layout="wide")
ICONES = {"critique": "🔴", "majeur": "🟠", "mineur": "🟡", "info": "🔵"}

profils = charger_profils()
config = charger_config()
etat = st.session_state
if "resultat" in etat:
    config = etat["config"]
etat.setdefault("ia", {})

# ----------------------------------------------------------------- Barre latérale
with st.sidebar:
    st.header("Assistant IA local")
    client = None
    if config.get("ia", {}).get("active", True):
        client = ClientOllama(config)
        modeles = client.modeles_disponibles()
        if modeles:
            defaut = next((i for i, m in enumerate(modeles) if m.startswith(client.modele)), 0)
            client.modele = st.selectbox("Modèle", modeles, index=defaut)
            st.success("Ollama est actif. Les données restent sur ce poste.")
        else:
            client = None
            st.info("IA non disponible : installez Ollama puis `ollama pull mistral`. "
                    "Les contrôles fonctionnent sans IA.")
    st.divider()
    st.header("Règles de contrôle")
    choix_profil = st.selectbox("Profil", ["Automatique"] + list(profils),
                                help="Automatique : le profil est choisi d'après les colonnes et onglets du fichier.")
    st.caption("Profils modifiables avec le Bloc-notes : dossier `config/profils`.")

# ----------------------------------------------------------------- Import
st.title("🔎 Contrôle qualité des catalogues fournisseurs")
c1, c2 = st.columns(2)
f_actuel = c1.file_uploader("Catalogue à contrôler (CSV ou Excel)", type=["csv", "txt", "xlsx", "xlsm"])
f_prec = c2.file_uploader("Version précédente (optionnel, pour comparer)", type=["csv", "txt", "xlsx", "xlsm"])

if st.button("Lancer l'analyse", type="primary", disabled=f_actuel is None):
    with st.spinner("Analyse en cours..."):
        try:
            impose = profils.get(choix_profil)
            actuel, config = lire_classeur(f_actuel.getvalue(), impose, f_actuel.name)
            prec = lire_classeur(f_prec.getvalue(), config, f_prec.name)[0] if f_prec else None
            etat["resultat"] = analyser(actuel, config, prec)
            etat["config"] = config
            etat["ia"] = {}
        except Exception as exc:  # message lisible pour un utilisateur métier
            st.error(f"Impossible de lire le fichier : {exc}")

res = etat.get("resultat")
if res is None:
    st.info("Déposez un fichier CSV puis cliquez sur « Lancer l'analyse ». "
            "Des fichiers d'exemple sont disponibles dans le dossier `exemples`.")
    st.stop()

# ----------------------------------------------------------------- Tableau de bord
m = st.columns(5)
m[0].metric("Qualité du catalogue", f"{res.score}/100")
for col, sev in zip(m[1:], ["critique", "majeur", "mineur", "info"]):
    col.metric(f"{ICONES[sev]} {LIBELLES_SEVERITE[sev]}", res.nb(sev))
afficher = st.error if res.nb("critique") else st.success if res.score >= 85 else st.warning
afficher(f"**{res.verdict}** — {res.stats['lignes']} lignes analysées (profil « {res.classeur.profil} »)"
         + (f", comparées à « {res.precedent.nom_fichier} »" if res.precedent else ""))

d1, d2, _ = st.columns([1, 1, 3])
d1.download_button("📊 Rapport Excel", vers_excel(res), file_name=f"controle_{res.nom_fichier}.xlsx")
d2.download_button("📄 Rapport HTML", vers_html(res, etat["ia"].get("resume")),
                   file_name=f"controle_{res.nom_fichier}.html", mime="text/html")

onglets = st.tabs(["Synthèse", "Détail des anomalies", "Assistant IA", "Fichier"])

with onglets[0]:
    for sev in ["critique", "majeur", "mineur", "info"]:
        anomalies = res.par_severite(sev)
        if anomalies:
            st.subheader(f"{ICONES[sev]} {LIBELLES_SEVERITE[sev]}")
            st.markdown("\n".join(f"- {a.titre}" for a in anomalies))
    if not res.anomalies:
        st.success("Aucune anomalie détectée.")

with onglets[1]:
    if res.anomalies:
        choix = st.selectbox("Anomalie", range(len(res.anomalies)),
                             format_func=lambda i: f"{ICONES[res.anomalies[i].severite]} {res.anomalies[i].titre}")
        a = res.anomalies[choix]
        st.caption(f"Catégorie : {a.categorie} · Code : {a.code} · Lignes touchées : {a.lignes_touchees}")
        if a.conseil:
            st.info(a.conseil)
        if not a.exemples.empty:
            st.dataframe(a.exemples, width="stretch", hide_index=True)
        st.divider()
        st.dataframe(tableau_synthese(res), width="stretch", hide_index=True)

with onglets[2]:
    if client is None:
        st.info("Assistant IA indisponible (voir barre latérale).")
    else:
        st.caption("L'IA reformule et propose ; elle ne modifie ni le score ni le fichier. "
                   "Réponses à valider (quelques dizaines de secondes par demande).")
        b1, b2, b3 = st.columns(3)
        try:
            if b1.button("📝 Résumer et expliquer les risques"):
                with st.spinner("L'IA rédige la synthèse..."):
                    etat["ia"]["resume"] = client.resumer(res)
            cibles = [a for a in res.anomalies if not a.exemples.empty and a.severite != "info"]
            if cibles:
                idx = b2.selectbox("Anomalie à corriger", range(len(cibles)), format_func=lambda i: cibles[i].titre,
                                   label_visibility="collapsed")
                if b2.button("🛠️ Proposer des corrections"):
                    with st.spinner("L'IA analyse les lignes..."):
                        etat["ia"]["corrections"] = client.proposer_corrections(cibles[idx])
            tableau = b3.selectbox("Onglet", list(res.classeur.tableaux), label_visibility="collapsed")
            if b3.button("🧠 Chercher des incohérences de sens"):
                with st.spinner("L'IA lit un échantillon du catalogue..."):
                    etat["ia"]["semantique"] = client.incoherences_semantiques(res.classeur.tableaux[tableau])
        except IAIndisponible as exc:
            st.error(str(exc))
        for cle, titre in [("resume", "Synthèse et risques"), ("corrections", "Corrections proposées"),
                           ("semantique", "Incohérences de sens (échantillon)")]:
            if cle in etat["ia"]:
                st.subheader(titre)
                st.markdown(etat["ia"][cle])

with onglets[3]:
    fmt = ("Format : **Excel**" if res.stats["encodage"] == "Excel"
           else f"Encodage détecté : **{res.stats['encodage']}** · séparateur : **{res.stats['separateur']!r}**")
    st.write(f"{fmt} · "
             f"{res.stats['nb_references'] or '?'} références · {res.stats['nb_marques'] or '?'} marques")
    st.write("Correspondance des colonnes :",
             {canon: origine for canon, origine in res.stats["correspondance"].items()})
    if res.stats["referentiels"]:
        st.write("Onglets de référence :", res.stats["referentiels"])
    onglet = st.selectbox("Tableau", list(res.classeur.tableaux),
                          format_func=lambda n: f"{n} ({len(res.classeur.tableaux[n].df)} lignes)")
    cat = res.classeur.tableaux[onglet]
    if cat.enumerations:
        with st.expander(f"{len(cat.enumerations)} liste(s) de valeurs autorisées lues dans l'en-tête"):
            st.json({c: v for c, v in cat.enumerations.items()}, expanded=False)
    st.dataframe(cat.df.head(500), width="stretch")
