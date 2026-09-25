# POC – Contrôle qualité des catalogues fournisseurs

Ce document répond au cadrage du POC. Le prototype décrit ici est dans ce dépôt et fonctionne.

---

## 1. Architecture technique

```
             Poste Windows de l'utilisateur (aucun flux sortant)
 ┌──────────────────────────────────────────────────────────────────┐
 │  Navigateur ──► http://localhost:8501  (interface Streamlit)     │
 │                    │                                             │
 │                    ▼                                             │
 │  ┌─────────────────────────── catalogue_qc (Python) ──────────┐  │
 │  │ 1. Chargement   encodage, séparateur, synonymes d'en-têtes │  │
 │  │ 2. Contrôles    règles déterministes (structure, EAN…)     │  │
 │  │ 3. Détection    similarité, formats, statistiques robustes │  │
 │  │ 4. Comparaison  version N vs N-1 (ajouts, recodification…) │  │
 │  │ 5. Score        pondération par sévérité et volume         │  │
 │  │ 6. Rapports     Excel détaillé + HTML autonome             │  │
 │  └────────────────────────┬──────────────────────────────────┘  │
 │   config/profils/*.yaml   │ (règles modifiables par le métier)   │
 │                           ▼ (optionnel)                          │
 │            Ollama  http://localhost:11434  (Mistral, Llama…)     │
 └──────────────────────────────────────────────────────────────────┘
```

**Principes structurants**

1. **Les règles décident, l'IA explique.** Le score et le verdict sont produits uniquement par des contrôles
   déterministes, reproductibles et auditables. L'IA intervient en aval sur un résumé des anomalies :
   elle rédige, explique et propose, mais ne modifie rien.
2. **Configuration hors code.** Colonnes attendues, synonymes d'en-têtes, champs obligatoires, clé
   d'unicité, seuils et pondération du score sont dans un **profil** (`config/profils/*.yaml`), modifiable avec le Bloc-notes. Un profil par famille de catalogues (optique CSV, audition Excel…), choisi automatiquement selon les colonnes et onglets du fichier.
3. **Un moteur, deux interfaces.** La même fonction `analyser()` sert l'interface web (utilisateurs métier)
   et la ligne de commande (automatisation, traitement par lot, futur branchement dans une chaîne d'intégration).
4. **Tout reste local.** Interface liée à `localhost` uniquement, télémétrie Streamlit désactivée, client IA
   qui refuse toute URL non locale et ignore les proxys système.

## 2. Technologies recommandées

| Besoin | Choix | Pourquoi |
|---|---|---|
| Langage | **Python 3.11+** | Standard de la donnée, facile à maintenir, gratuit |
| Traitement des données | **pandas** | ~50 000 lignes analysées en 3-4 secondes sur un PC standard |
| Similarité de chaînes | **RapidFuzz** | Levenshtein très rapide (C++), pour les marques et les références |
| Interface | **Streamlit** | Application web locale en ~150 lignes, sans compétence front-end |
| Rapports | **openpyxl** (Excel) + HTML autonome | Formats que le métier sait ouvrir et diffuser |
| Configuration | **YAML** | Lisible et modifiable par un non-développeur |
| IA locale | **Ollama** + **Mistral 7B** ou **Qwen 2.5 7B** / **Llama 3.1 8B** | Installation Windows en 1 clic, API HTTP locale, très bon français (Mistral, Qwen) |
| Tests | **pytest** | Non-régression des règles |

**Matériel pour l'IA** : un modèle 7-8B quantifié (Q4) nécessite ~5 Go de RAM libre. Sur un PC portable sans
carte graphique, comptez 20 s à 2 min par réponse. Avec 16 Go de RAM c'est confortable ; un GPU NVIDIA 8 Go
rend les réponses quasi instantanées. Les contrôles, eux, n'ont aucun besoin particulier.

**Alternatives écartées pour le POC** : Power BI / Power Query (règles de similarité et comparaison de versions
laborieuses), Great Expectations (puissant mais trop technique pour le métier), application Electron/.NET
(coût de développement disproportionné pour un POC).

**Industrialisation ultérieure** : empaquetage en `.exe` (PyInstaller) ou déploiement sur un petit serveur
interne (Streamlit derrière l'authentification de l'entreprise) avec un serveur Ollama mutualisé.

## 3. Découpage en étapes

| Étape | Contenu | Durée indicative | Livrable |
|---|---|---|---|
| **0. Cadrage** | Récupérer 3 à 5 catalogues réels (dont des cas ayant fait échouer une intégration), lister les colonnes et règles SI | 2-3 j | profil réaliste |
| **1. Socle** ✅ | Lecture robuste des CSV, contrôles déterministes, score, rapport Excel/HTML | 1 sem. | Ligne de commande |
| **2. Interface** ✅ | Streamlit, tableau de bord, détail des anomalies, lanceur Windows | 3-4 j | `lancer.bat` |
| **3. Comparaison N/N-1** ✅ | Ajouts, suppressions, recodifications, variations de prix, changement de format | 3-4 j | Onglet « Évolution » |
| **4. Détection intelligente** ✅ | Marques proches, références quasi identiques, formats atypiques, prix aberrants | 1 sem. | Anomalies « Détection intelligente » |
| **5. IA locale** ✅ (à évaluer) | Synthèse, risques, corrections proposées, incohérences sémantiques | 1 sem. | Onglet « Assistant IA » |
| **6. Évaluation** | Faire tourner sur 10+ catalogues réels ; mesurer faux positifs / faux négatifs et temps gagné ; ajuster les seuils | 1-2 sem. | Bilan go / no-go |
| **7. Pistes post-POC** | Référentiels internes (marques, couleurs, tailles), historique des analyses par fournisseur, export des corrections, intégration dans la chaîne d'import | — | Feuille de route |

Les étapes marquées ✅ sont couvertes par le prototype ; les étapes 0 et 6 demandent vos données réelles.

## 4. Contrôles à implémenter dès le premier POC (tous présents dans le prototype)

Classés par rapport « bénéfice / effort » décroissant :

| Priorité | Contrôle | Sévérité | Ce qu'il évite |
|---|---|---|---|
| ★★★ | Colonnes obligatoires absentes, lignes mal formées | Critique | Rejet complet du fichier |
| ★★★ | Identifiant (référence, EAN) ou prix manquant | Critique | Rejet de lignes, fiches incomplètes |
| ★★★ | EAN en doublon entre articles différents | Critique | Écrasement d'un produit par un autre |
| ★★★ | Même article (réf + couleur + taille) avec des données différentes | Critique | Impossible de savoir quelle ligne croire |
| ★★★ | **EAN abîmés par Excel** (`3,80100E+12`) | Critique | Cas très fréquent et invisible à l'œil |
| ★★★ | Prix non numériques, nuls ou négatifs | Critique | Rejet, prix à 0 en magasin |
| ★★☆ | EAN invalide (longueur, clé de contrôle) | Majeur | Code-barre illisible en caisse |
| ★★☆ | Prix de vente < prix d'achat | Majeur | Colonnes inversées |
| ★★☆ | **Erreur d'unité** : prix ×100 (centimes) par rapport aux articles de la même marque | Majeur | Prix délirant publié |
| ★★☆ | Dépendances : 1 référence = 1 marque, 1 code couleur = 1 libellé | Majeur | Référentiels incohérents |
| ★★☆ | Lignes en double exact | Majeur | Doublons de fiches |
| ★★☆ | **N vs N-1** : articles supprimés / ajoutés, variations de prix > 30 %, EAN modifié | Majeur / Critique | Déréférencements non voulus, erreurs tarifaires |
| ★★☆ | **Recodification** : même EAN mais nouvelle référence ; changement de format (`PO-1234` → `PO1234`) | Majeur | Perte d'historique ventes/stock, doublons |
| ★★☆ | Références quasi identiques (`CA-1020` / `CA-1O20`, casse, tirets) | Majeur | Deux fiches pour un même produit |
| ★☆☆ | Marques écrites différemment (`RAY-BAN`, `RAY BAN`, `Rayban`, `RAY-BANN`) avec correction proposée | Mineur | Filtres et statistiques faussés |
| ★☆☆ | Formats de code atypiques par marque (`AA-9999` attendu, `AA-9A99` trouvé) | Mineur | Fautes de frappe |
| ★☆☆ | Prix / coefficient de marge statistiquement atypiques (z-score robuste par marque) | Mineur | Erreurs de saisie plus subtiles |
| ★☆☆ | Même produit (marque + libellé + couleur + taille) sous plusieurs références | Mineur | Doublons de fiches |
| ★☆☆ | Colonnes inattendues, espaces parasites, caractères mal encodés, champs facultatifs vides | Mineur | Bruit, problèmes d'affichage |

**Choix de conception notables**

- *Fautes de frappe sur les références* : on ne compare **pas** toutes les références entre elles par distance
  d'édition, car les codes fournisseurs sont souvent séquentiels (`RB-1234`, `RB-1235` sont deux produits
  légitimes). On détecte plutôt les confusions typiques (O/0, I/1, séparateurs, casse), les formats atypiques
  et, avec la version précédente, les références qui ont « glissé » (même EAN ou même écriture normalisée).
- *Valeurs aberrantes* : médiane et écart absolu médian (MAD) en échelle logarithmique, **par marque** — un prix
  de 300 € est normal chez Gucci et suspect chez Polaroid. Plus robuste qu'une moyenne / écart-type.
- *Score* : `100 − Σ pénalités`, chaque anomalie pesant `base + % de lignes touchées × facteur`, avec un
  plafond par sévérité. Toute anomalie critique rend le verdict **BLOQUANT** quel que soit le score.

## 5. Fonctionnalités IA au meilleur retour sur investissement

Classement issu de la conception du prototype (à confirmer sur vos données à l'étape 6) :

| Rang | Usage | ROI | Justification |
|---|---|---|---|
| 1 | **Synthèse + risques + plan d'action + e-mail au fournisseur** | ★★★ | Le résultat des règles est déjà fiable : l'IA n'a qu'à le reformuler. Faible risque d'erreur, gain de temps immédiat (rédaction du retour fournisseur). |
| 2 | **Propositions de corrections** sur les anomalies « textuelles » (marques, libellés, codes couleur, casse) | ★★☆ | Utile quand la bonne valeur est déductible (harmonisation, faute de frappe). Chaque proposition est accompagnée d'un niveau de confiance et reste à valider. Inutile pour un EAN ou un prix manquant (donnée à redemander). |
| 3 | **Incohérences sémantiques** sur un échantillon (libellé « noir » avec couleur « rouge », catégorie mal affectée, taille improbable) | ★☆☆ à ★★☆ | C'est ce que les règles ne savent pas faire, mais un modèle 7B local est lent et imprécis sur de gros volumes : à utiliser sur un échantillon, comme sonde exploratoire. Les incohérences récurrentes trouvées doivent ensuite être **transformées en règles**. |
| — | À éviter : laisser l'IA calculer le score, détecter les doublons ou corriger le fichier automatiquement | ✗ | Non reproductible, non auditable, et bien moins fiable que pandas pour compter. |

**Pistes IA pour la suite** (hors POC) :
- mapping automatique des en-têtes inconnus vers les colonnes attendues (le LLM propose, l'utilisateur valide,
  le synonyme est ajouté au profil) ;
- embeddings locaux (`nomic-embed-text` via Ollama) pour rapprocher les libellés d'un référentiel interne ;
- classification automatique des produits dans la nomenclature interne.

**Grille d'évaluation proposée** : sur 10 catalogues, noter pour chaque sortie IA la justesse (0-2), l'utilité
(0-2) et le temps de réponse ; comparer 2 modèles (ex. `mistral` et `qwen2.5:7b`).

## 6. Structure du projet

```
├── app.py                    Interface web locale (Streamlit)
├── lancer.bat                Double-clic : installe au premier lancement puis ouvre l'application
├── controler.bat             Glisser-déposer d'un CSV : génère les rapports HTML + Excel
├── config/profils/           Un profil de règles par famille de catalogues (optique_mode.yaml, audition.yaml)
├── catalogue_qc/
│   ├── chargement.py         CSV / Excel multi-onglets, en-tête sur 2 lignes, listes de valeurs, choix du profil
│   ├── controles.py          Contrôles déterministes
│   ├── detection.py          Détection "intelligente" (similarité, formats, statistiques)
│   ├── comparaison.py        Comparaison avec la version précédente
│   ├── referentiels.py       Contrôles entre onglets (couleurs, associations, codes uniques)
│   ├── analyse.py            Orchestration, score, verdict
│   ├── rapport.py            Exports Excel et HTML
│   ├── ia_locale.py          Client Ollama (local uniquement) et prompts
│   ├── modele.py             Structures de données
│   ├── outils.py             Normalisation, EAN, signatures de format, z-score robuste
│   └── cli.py                Ligne de commande
├── exemples/                 Deux catalogues fictifs avec anomalies injectées + générateur
└── tests/                    Tests automatisés (pytest)
```

**Ajouter un contrôle** : écrire une fonction `(catalogue, config) -> list[Anomalie]` et l'ajouter à la liste
`CONTROLES` dans `analyse.py`. Elle apparaît automatiquement dans le score, l'interface et les rapports.

## 7. Calibrage sur un vrai catalogue Audition (juin 2026)

Un export fournisseur réel, réputé correct, a servi à calibrer le profil `audition.yaml` : classeur Excel de
6 onglets (Audioprothèses 1 631 lignes, Embouts 14, Accessoires audio 670, Piles 1, Couleurs 52,
Associations 59 378). Le fichier n'est pas versionné ; un exemple fictif au même format est fourni
(`exemples/audition_*.xlsx`).

**Ce que le format apporte** : les listes de valeurs autorisées sont écrites dans l'en-tête des colonnes
(`Bluetooth / Non : 0 / Oui : 1`, `Type / BTE : Derrière l'oreille / RIC : …`). L'outil les lit et contrôle
automatiquement plus de 40 colonnes codifiées, sans rien configurer. S'y ajoutent les contrôles entre onglets :
codes couleur présents dans le référentiel Couleurs, liens de l'onglet Associations vers des articles existants
et non supprimés, unicité des codes entre onglets, suppressions déclarées (`Action = 2`) ou non déclarées.

**Faux positifs éliminés pendant le calibrage** (le premier passage donnait 50/100) :

| Constat sur le fichier réel | Réglage |
|---|---|
| `Vente = 0` sur 347 appareils (prix public non communiqué) → aurait déclenché « PV < PA » | `zero_equivaut_vide` sur `prix_vente` |
| `0` utilisé comme « non renseigné » hors liste (ex. *Unité de quantité*) | `valeurs_neutres: ["0"]` |
| Colonnes facultatives entièrement vides dans un onglet (couleur d'un embout) | ignorées ; partiellement vides = information |
| Couleur, gamme, classe de remboursement exigées sur tous les onglets | obligation limitée à `onglets: [Audioprothèses]` |
| Codes fabricant non EAN (`732-07-303-03`) contrôlés comme EAN | contrôle GTIN uniquement sur les codes à 8/12-14 chiffres |
| Tiroirs à pile (4,20 €) vs chargeurs (199 €) signalés « erreur d'unité » | prix comparés par marque **et** type ; « erreur d'unité » seulement si le prix ×/÷ 10/100/1000 retombe dans la fourchette du groupe |
| Doubles espaces internes dans les libellés | seuls les espaces en début/fin sont signalés |

**Résultat : 97/100 – INTÉGRABLE**, 0 critique. Restent, à confirmer par le métier :
- *Majeur* : 4 accessoires avec un prix d'achat de 0 € (bouchons de couleur, tube) — gratuits ou oubli ?
- *Mineur* : 21 prix statistiquement atypiques (ex. filtres par 100 à 74 € quand la médiane est à 5,80 €) ;
  1 produit sous deux références avec un libellé identique (`COLOUR PLUG SET, 1 PCS`).
- *Info* : 522 appareils sans accessoire associé ; 7 appareils sans date de début de validité.

Test de non-régression : `CATALOGUE_AUDITION_REEL=chemin/fichier.xlsx python -m pytest` vérifie qu'un
catalogue correct reste sans anomalie critique et au-dessus de 90/100.

## 8. Format ECHO (CSV à enregistrements typés)

Le même catalogue existe au format **ECHO** : un CSV sans en-tête où chaque ligne commence par un code
d'enregistrement (`00` entête, `01` fabricant, `03` marques, `20` modèle d'audioprothèse, `81` déclinaison
couleur avec EAN et code commande, `21` piles, `22` embouts, `23` accessoires, `80` couleurs, `8` associations).

- Les positions des champs sont décrites dans `config/formats/echo_audition.yaml`, en reprenant les noms des
  colonnes de l'export Excel. Le profil *Audition* s'applique donc sans changement ; le format est détecté
  automatiquement (première ligne `00`, présence d'enregistrements `20` et `81`).
- Cette correspondance a été **établie en croisant** le fichier ECHO et l'export Excel du même catalogue :
  les 2 316 articles reconstitués (modèle `20` + déclinaisons `81`) sont identiques à l'export Excel, valeur
  par valeur. Les positions notées « (?) » étaient vides dans le fichier et restent à confirmer.
- Le fichier ECHO ne décrit pas ses listes de valeurs : celles de l'export Excel ont été reprises dans le
  profil (`listes_valeurs`), par onglet.
- Contrôles propres au format : type d'enregistrement inconnu, enregistrement tronqué, déclinaison `81`
  sans modèle `20`, modèle sans déclinaison, code marque absent des enregistrements `03`.

**Résultat sur le fichier réel : 97/100 – INTÉGRABLE**, mêmes constats que l'export Excel.

**Écarts constatés entre les deux exports du même catalogue** (utile pour choisir le format à intégrer) :

| Sujet | Export Excel | Fichier ECHO |
|---|---|---|
| Associations appareil ↔ accessoire | par déclinaison couleur : 9 339 couples modèle–accessoire | par modèle : 3 773 couples, soit en pratique les accessoires **communs à toutes les couleurs** (155 modèles sur 166). Les accessoires propres à une couleur sont perdus. |
| Type de bouchons d'oreilles (Embouts) | renseigné (`2`) | vide |
| Caractéristiques essentielles, date de création | au niveau de la déclinaison | au niveau du modèle |
| Date de modification | date seule | date et heure |

Test de non-régression : `CATALOGUE_ECHO_REEL=chemin/fichier.csv python -m pytest`.
