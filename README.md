# Contrôle qualité des catalogues fournisseurs (POC)

Outil local pour analyser un catalogue fournisseur (CSV, Excel multi-onglets ou fichier ECHO) **avant** son intégration dans le système d'information :
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

Pour essayer : utiliser les fichiers du dossier `exemples/` :
- `catalogue_actuel.csv` / `catalogue_precedent.csv` : catalogue optique à plat ;
- `audition_actuel.xlsx` / `audition_precedent.xlsx` : classeur audition multi-onglets
  (Audioprothèses, Accessoires, Couleurs, Associations) au format fournisseur ;
- `audition_echo_actuel.csv` / `audition_echo_precedent.csv` : le même catalogue au format ECHO
  (enregistrements typés 20 / 81 / 23 / 80 / 8…).

### Sans interface
Glisser-déposer un fichier CSV ou Excel sur **`controler.bat`** : les rapports `<fichier>_controle.html` et
`.xlsx` sont créés à côté du CSV et le rapport HTML s'ouvre.

## Adapter les règles
Les règles sont dans des **profils** (`config/profils/*.yaml`, modifiables avec le Bloc-notes), un par famille
de catalogues. Le profil est choisi automatiquement d'après les colonnes et onglets du fichier, ou forcé dans
l'interface (`--profil` en ligne de commande) :
- `optique_mode.yaml` : catalogue CSV à plat (référence, EAN, marque, couleur, taille, prix) ;
- `audition.yaml` : catalogue audition, en export Excel (en-tête sur 2 lignes, listes de valeurs lues dans
  l'en-tête) ou en fichier ECHO (positions décrites dans `config/formats/echo_audition.yaml`) ; référentiel
  Couleurs, Associations, suppressions déclarées par `Action = 2`. Calibré sur deux vrais catalogues réputés
  corrects (Excel et ECHO) : 97/100, sans anomalie critique (voir [docs/PROPOSITION.md](docs/PROPOSITION.md)).

Un profil décrit les colonnes attendues et leurs noms possibles chez les fournisseurs, les champs obligatoires
(éventuellement par onglet), les identifiants uniques, les listes de valeurs, les règles entre colonnes
(ex. date de fin ≥ date de début), les seuils de détection, la pondération du score et le modèle d'IA.
Pour une nouvelle famille de catalogues : copier un profil, changer son `nom`, l'adapter.

## Pour les développeurs

```bash
pip install -r requirements-dev.txt
python -m pytest                     # tests
streamlit run app.py                 # interface
python -m catalogue_qc.cli exemples/catalogue_actuel.csv \
    --precedent exemples/catalogue_precedent.csv --html rapport.html --excel rapport.xlsx [--ia]
python exemples/generer_exemples.py            # régénère les catalogues optique d'exemple
python exemples/generer_exemple_audition.py    # régénère les classeurs audition d'exemple
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
