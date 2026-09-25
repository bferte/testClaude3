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
 │        config/regles.yaml │ (règles modifiables par le métier)   │
 │                           ▼ (optionnel)                          │
 │            Ollama  http://localhost:11434  (Mistral, Llama…)     │
 └──────────────────────────────────────────────────────────────────┘
```

**Principes structurants**

1. **Les règles décident, l'IA explique.** Le score et le verdict sont produits uniquement par des contrôles
   déterministes, reproductibles et auditables. L'IA intervient en aval sur un résumé des anomalies :
   elle rédige, explique et propose, mais ne modifie rien.
2. **Configuration hors code.** Colonnes attendues, synonymes d'en-têtes, champs obligatoires, clé
   d'unicité, seuils et pondération du score sont dans `config/regles.yaml`, modifiable avec le Bloc-notes.
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
| **0. Cadrage** | Récupérer 3 à 5 catalogues réels (dont des cas ayant fait échouer une intégration), lister les colonnes et règles SI | 2-3 j | `regles.yaml` réaliste |
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
  le synonyme est ajouté à `regles.yaml`) ;
- embeddings locaux (`nomic-embed-text` via Ollama) pour rapprocher les libellés d'un référentiel interne ;
- classification automatique des produits dans la nomenclature interne.

**Grille d'évaluation proposée** : sur 10 catalogues, noter pour chaque sortie IA la justesse (0-2), l'utilité
(0-2) et le temps de réponse ; comparer 2 modèles (ex. `mistral` et `qwen2.5:7b`).

## 6. Structure du projet

```
├── app.py                    Interface web locale (Streamlit)
├── lancer.bat                Double-clic : installe au premier lancement puis ouvre l'application
├── controler.bat             Glisser-déposer d'un CSV : génère les rapports HTML + Excel
├── config/regles.yaml        Règles métier et seuils (modifiable sans programmer)
├── catalogue_qc/
│   ├── chargement.py         Encodage, séparateur, synonymes d'en-têtes
│   ├── controles.py          Contrôles déterministes
│   ├── detection.py          Détection "intelligente" (similarité, formats, statistiques)
│   ├── comparaison.py        Comparaison avec la version précédente
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
