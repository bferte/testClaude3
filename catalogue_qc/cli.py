"""Utilisation en ligne de commande (automatisation, traitement par lot).

Exemple :
    python -m catalogue_qc.cli exemples/catalogue_actuel.csv --precedent exemples/catalogue_precedent.csv \
        --html rapport.html --excel rapport.xlsx --ia
Code retour : 0 = intégrable, 1 = à vérifier, 2 = bloquant (utilisable dans un script).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyse import analyser
from .chargement import lire_csv
from .ia_locale import ClientOllama, IAIndisponible
from .modele import charger_config
from .rapport import vers_excel, vers_html


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Contrôle qualité d'un catalogue fournisseur CSV")
    p.add_argument("actuel", help="Catalogue à contrôler (CSV)")
    p.add_argument("--precedent", help="Version précédente du catalogue (CSV)")
    p.add_argument("--config", help="Fichier de règles (défaut : config/regles.yaml)")
    p.add_argument("--html", help="Chemin du rapport HTML à générer")
    p.add_argument("--excel", help="Chemin du rapport Excel à générer")
    p.add_argument("--ia", action="store_true", help="Ajouter une synthèse rédigée par l'IA locale (Ollama)")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    config = charger_config(args.config)
    res = analyser(
        lire_csv(args.actuel, config), config,
        lire_csv(args.precedent, config) if args.precedent else None,
    )
    print(res.synthese_texte())

    texte_ia = None
    if args.ia:
        try:
            print("\nAnalyse IA en cours (peut prendre 1 à 2 minutes)...")
            texte_ia = ClientOllama(config).resumer(res)
            print("\n=== Analyse IA ===\n" + texte_ia)
        except IAIndisponible as exc:
            print(f"\n[IA] {exc}")

    if args.html:
        Path(args.html).write_text(vers_html(res, texte_ia), encoding="utf-8")
        print(f"\nRapport HTML : {args.html}")
    if args.excel:
        Path(args.excel).write_bytes(vers_excel(res))
        print(f"Rapport Excel : {args.excel}")

    if res.nb("critique"):
        return 2
    return 0 if res.score >= 85 else 1


if __name__ == "__main__":
    sys.exit(main())
