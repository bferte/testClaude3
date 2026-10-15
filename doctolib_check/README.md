# Contrôle des fiches magasins Doctolib

Script qui ouvre chaque URL Doctolib d'un fichier Excel et détecte si la fiche affiche
**« n'est pas réservable en ligne »**.

## 1. Installation (une seule fois)

```bash
# Dépendances Python
pip install -r requirements.txt
#   (équivalent : pip install playwright pandas openpyxl tqdm)

# Navigateur Chromium utilisé par Playwright
python -m playwright install chromium
```

> Poste d'entreprise où le téléchargement de Chromium est bloqué : sauter la 2ᵉ commande et ajouter
> `--chrome` à l'exécution pour utiliser le Google Chrome déjà installé.

## 2. Fichier d'entrée

Un fichier Excel avec une colonne **`URL`** (les autres colonnes sont ignorées).
Exemple fourni : `urls_magasins_exemple.xlsx` (régénérable avec `python generer_exemple.py`).

| Code magasin | URL |
|---|---|
| MAG001 | https://www.doctolib.fr/opticien/paris/optique-exemple-paris-11 |
| MAG002 | https://www.doctolib.fr/opticien/lyon/optique-exemple-lyon-centre |

Si la colonne porte un autre nom : `--colonne "Lien Doctolib"`. Autre onglet : `--onglet "Feuil2"`.
Les doublons et cellules vides sont ignorés.

## 3. Exécution

```bash
# Essai sur 10 URL, navigateur visible pour vérifier
python verifier_doctolib.py mes_urls.xlsx --limite 10 --visible

# Traitement complet
python verifier_doctolib.py mes_urls.xlsx

# Après une interruption (Ctrl+C, coupure…) : ne refait que les URL manquantes ou en erreur
python verifier_doctolib.py mes_urls.xlsx --reprendre
```

Sous Windows : glisser-déposer le fichier Excel sur **`verifier.bat`**.

## 4. Résultats

| Fichier | Contenu |
|---|---|
| `mes_urls_resultats.xlsx` | toutes les URL : URL, Nom du magasin, Statut, Texte détecté, Erreur éventuelle |
| `mes_urls_resultats_non_reservables.xlsx` | uniquement les fiches « Non réservable » |
| `mes_urls_resultats.encours.csv` | journal écrit après **chaque** URL (sert à `--reprendre`) |

Statuts : **Réservable**, **Non réservable**, ou **Indéterminé** quand la page n'a pas pu être lue
(erreur réseau, 404, captcha…) : la colonne *Erreur éventuelle* en donne la raison.
Le fichier Excel est mis à jour toutes les 10 URL (`--frequence-sauvegarde`) ; s'il est ouvert dans
Excel à ce moment-là, les résultats sont écrits dans un fichier `~tmp_…` à côté.

## 5. Réglages

| Option | Défaut | Rôle |
|---|---|---|
| `--onglets N` | 4 | onglets ouverts en parallèle (limite la charge machine) |
| `--timeout S` | 30 | délai max de chargement d'une page |
| `--attente S` | 2 | attente après chargement complet (contenu JavaScript tardif) |
| `--pause S` | 1 | pause moyenne entre deux URL d'un même onglet |
| `--essais N` | 3 | tentatives par URL en cas d'erreur |
| `--sans-images` | – | ne charge ni images ni polices (plus rapide) |
| `--sortie F` | `<entrée>_resultats.xlsx` | fichier de résultats |

Ordre de grandeur : avec 4 onglets et les réglages par défaut, ~800 URL en 15 à 25 minutes.

**Anti-robot** : Doctolib peut afficher un captcha si les requêtes sont trop rapides ; ces URL sont
signalées « Page de blocage anti-robot ». Dans ce cas, réduire `--onglets` (2) et augmenter `--pause` (3),
puis relancer avec `--reprendre`.

## Fonctionnement

1. chargement de la page (`domcontentloaded`), puis attente que le réseau soit inactif (`networkidle`) ;
2. acceptation du bandeau cookies s'il apparaît, puis attente `--attente` ;
3. lecture du texte **visible** de la page et recherche de « n'est pas réservable en ligne »
   (insensible à la casse, apostrophe droite ou typographique) ;
4. nom du magasin : titre `<h1>` de la fiche, à défaut le titre de la page.
