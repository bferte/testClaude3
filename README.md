# Contrôle qualité des catalogues fournisseurs (POC)

Outil local pour analyser un catalogue fournisseur CSV **avant** son intégration dans le système d'information :
champs manquants, doublons, EAN invalides, prix incohérents, marques mal orthographiées, références recodifiées,
différences avec la version précédente… Il produit un **score qualité sur 100**, un verdict et un rapport
Excel / HTML. Une IA locale (facultative) rédige la synthèse et propose des corrections.

**Aucune donnée ne quitte le poste** : l'application n'écoute que sur `localhost`, et l'IA n'accepte qu'un
serveur local.

➡️ Architecture, choix techniques, étapes et analyse du ROI de l'IA : [docs/PROPOSITION.md](docs/PROPOSITION.md)

## Utilisation (Windows)

### Prérequis (une seule fois)
1. Installer **Python 3.11 ou plus récent** depuis https://www.python.org/downloads/
   (cocher *« Add python.exe to PATH »*).
2. *(Facultatif, pour l'IA)* Installer **Ollama** depuis https://ollama.com/download puis, dans une invite
   de commandes : `ollama pull mistral`

### Interface graphique
Double-cliquer sur **`lancer.bat`**. Le premier lancement installe les composants (quelques minutes),
puis l'application s'ouvre dans le navigateur :
1. déposer le catalogue à contrôler, et éventuellement la version précédente ;
2. cliquer sur **Lancer l'analyse** ;
3. consulter le score, les anomalies et les lignes concernées ; télécharger le rapport Excel ou HTML ;
4. onglet **Assistant IA** : synthèse des risques, propositions de corrections, recherche d'incohérences.

Pour essayer : utiliser les fichiers du dossier `exemples/`.

### Sans interface
Glisser-déposer un fichier CSV sur **`controler.bat`** : les rapports `<fichier>_controle.html` et
`.xlsx` sont créés à côté du CSV et le rapport HTML s'ouvre.

## Adapter les règles
Tout se règle dans **`config/regles.yaml`** (Bloc-notes) : colonnes attendues et leurs noms possibles chez
les fournisseurs, champs obligatoires, clé d'unicité d'un article, dépendances (un code couleur = un libellé),
seuils de détection, pondération du score, modèle d'IA.

## Pour les développeurs

```bash
pip install -r requirements-dev.txt
python -m pytest                     # tests
streamlit run app.py                 # interface
python -m catalogue_qc.cli exemples/catalogue_actuel.csv \
    --precedent exemples/catalogue_precedent.csv --html rapport.html --excel rapport.xlsx [--ia]
python exemples/generer_exemples.py  # régénère les catalogues d'exemple
```

Code retour de la ligne de commande : `0` intégrable, `1` à vérifier, `2` bloquant.

Exemple de sortie sur les fichiers d'exemple :

```
Qualité du catalogue : 35/100  ->  BLOQUANT - corrections obligatoires avant intégration
6 anomalie(s) critique(s), 15 majeure(s), 8 mineure(s), 1 information(s)

Critique :
- 4 ligne(s) sans référence (identifiant manquant)
- 3 EAN en doublon (partagés par plusieurs articles)
- 3 EAN corrompu(s) par Excel (notation scientifique, ex. 3,80100E+12)
...
Majeur :
- 147 article(s) recodifié(s) : même EAN, nouvelle référence
- 39 article(s) supprimé(s) depuis la version précédente (2.2 %)
- Changement de format des références (PERSOL : AA-9999 (100%) -> AA9999 (100%))
...
Mineur :
- 2 marque(s) avec orthographe incohérente
...
```
