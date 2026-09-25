"""Exports du rapport de contrôle : Excel (détail) et HTML (lecture / diffusion)."""
from __future__ import annotations

import html
import io
from datetime import datetime

import pandas as pd

from .modele import LIBELLES_SEVERITE, SEVERITES, ResultatAnalyse

COULEURS = {"critique": "#c62828", "majeur": "#ef6c00", "mineur": "#f9a825", "info": "#1565c0"}


def tableau_synthese(res: ResultatAnalyse) -> pd.DataFrame:
    return pd.DataFrame([{
        "Sévérité": LIBELLES_SEVERITE[a.severite],
        "Catégorie": a.categorie,
        "Anomalie": a.titre,
        "Nombre": a.nb,
        "Lignes touchées": a.lignes_touchees,
        "Conseil": a.conseil,
        "Code": a.code,
    } for a in res.anomalies])


def vers_excel(res: ResultatAnalyse) -> bytes:
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as xl:
        entete = pd.DataFrame({
            "Indicateur": ["Fichier", "Comparé à", "Date d'analyse", "Lignes", "Score qualité", "Verdict",
                           "Anomalies critiques", "Anomalies majeures", "Anomalies mineures"],
            "Valeur": [res.catalogue.nom_fichier, res.precedent.nom_fichier if res.precedent else "-",
                       datetime.now().strftime("%d/%m/%Y %H:%M"), res.stats["lignes"], f"{res.score}/100",
                       res.verdict, res.nb("critique"), res.nb("majeur"), res.nb("mineur")],
        })
        entete.to_excel(xl, sheet_name="Synthèse", index=False)
        tableau_synthese(res).to_excel(xl, sheet_name="Synthèse", index=False, startrow=len(entete) + 2)
        for i, a in enumerate(res.anomalies, 1):
            if not a.exemples.empty:
                a.exemples.to_excel(xl, sheet_name=f"{i:02d} {a.code}"[:31], index=False)
        for feuille in xl.book.worksheets:
            for colonne in feuille.columns:
                largeur = max(len(str(c.value or "")) for c in colonne[:200])
                feuille.column_dimensions[colonne[0].column_letter].width = min(max(10, largeur + 2), 80)
    return tampon.getvalue()


def vers_html(res: ResultatAnalyse, texte_ia: str | None = None) -> str:
    e = html.escape
    couleur_score = "#2e7d32" if res.score >= 85 else "#ef6c00" if res.score >= 60 else "#c62828"
    blocs = []
    for sev in SEVERITES:
        anomalies = res.par_severite(sev)
        if not anomalies:
            continue
        items = []
        for a in anomalies:
            detail = ""
            if not a.exemples.empty:
                detail = a.exemples.head(50).to_html(index=False, escape=True, classes="ex", border=0)
                if len(a.exemples) > 50:
                    detail += f"<p class='note'>… {len(a.exemples) - 50} autre(s) ligne(s) dans l'export Excel.</p>"
            items.append(
                f"<details><summary>{e(a.titre)} <span class='cat'>{e(a.categorie)}</span></summary>"
                f"{f'<p class=conseil>{e(a.conseil)}</p>' if a.conseil else ''}{detail}</details>"
            )
        blocs.append(f"<h2 style='color:{COULEURS[sev]}'>{LIBELLES_SEVERITE[sev]} ({len(anomalies)})</h2>{''.join(items)}")

    ia = ""
    if texte_ia:
        ia = f"<h2>Analyse de l'IA locale</h2><div class='ia'>{e(texte_ia)}</div>" \
             "<p class='note'>Texte généré automatiquement : à valider par un expert.</p>"
    comparaison = f" &middot; comparé à <b>{e(res.precedent.nom_fichier)}</b>" if res.precedent else ""
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Contrôle catalogue - {e(res.catalogue.nom_fichier)}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:24px auto;max-width:1200px;color:#222;padding:0 16px}}
.score{{font-size:48px;font-weight:700;color:{couleur_score}}}
.tuiles{{display:flex;gap:12px;flex-wrap:wrap}} .tuile{{border:1px solid #ddd;border-radius:8px;padding:10px 16px}}
details{{border:1px solid #e0e0e0;border-radius:6px;margin:6px 0;padding:6px 10px}}
summary{{cursor:pointer;font-weight:600}} .cat{{font-weight:400;color:#777;font-size:12px;margin-left:8px}}
.conseil{{color:#555;font-style:italic}} .note{{color:#777;font-size:12px}}
table.ex{{border-collapse:collapse;font-size:12px;margin:8px 0;display:block;overflow-x:auto}}
table.ex th,table.ex td{{border:1px solid #ddd;padding:3px 6px;text-align:left;white-space:nowrap}}
table.ex th{{background:#f5f5f5}} .ia{{white-space:pre-wrap;background:#f7f9fc;padding:12px;border-radius:6px}}
</style></head><body>
<h1>Rapport de contrôle du catalogue</h1>
<p><b>{e(res.catalogue.nom_fichier)}</b> ({res.stats['lignes']} lignes){comparaison}
&middot; {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
<div class="tuiles">
<div class="tuile">Qualité du catalogue<div class="score">{res.score}/100</div>{e(res.verdict)}</div>
{''.join(f"<div class='tuile'>{LIBELLES_SEVERITE[s]}<div class='score' style='color:{COULEURS[s]}'>{res.nb(s)}</div></div>" for s in SEVERITES[:3])}
</div>
{ia}
{''.join(blocs) or '<p>Aucune anomalie détectée.</p>'}
</body></html>"""
