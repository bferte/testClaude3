# Test Auditif ATOL

Application web permettant de réaliser un test auditif en ligne développée pour les opticiens ATOL.

## 📋 Description

Cette application permet aux utilisateurs de réaliser un test auditif avec deux modes d'utilisation :

1. **En magasin ATOL** : L'opticien configure la tablette et la présente au client pour réaliser le test
2. **En ligne** : Le client peut réaliser le test directement via le site web officiel ATOL

Le contenu du test diffère selon le mode d'utilisation :

- **Version Web** : Inclut un test tonal (sans test vocal)
- **Version Magasin** : Inclut un test vocal (sans test tonal)

Les étapes principales du test comprennent :

- Un questionnaire préliminaire sur les habitudes d'écoute
- Un test tonal ou vocal selon le contexte d'utilisation
- Un formulaire de collecte d'informations pour le suivi

Les résultats sont enregistrés et peuvent être consultés par les opticiens ATOL pour proposer des solutions adaptées aux clients.

## 🚀 Installation

### Prérequis

- Node.js 18+
- PNPM 9+
- MariaDB

### Mise en place

1. Cloner le dépôt

> **Note**: La connexion au VPN d'Atol est requise pour accéder au dépôt GitLab.

```bash
git clone git@gitlab.atol.fr:dfa/test-auditif.git
cd test-auditif
```

2. Installer les dépendances

```bash
pnpm install
```

3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Puis modifiez le fichier `.env` avec vos paramètres spécifiques.

4. Lancer l'application en développement

```bash
pnpm dev
```

## 🛠️ Technologies utilisées

- [Next.js 15](https://nextjs.org/) - Framework React avec rendu hybride
- [React 19](https://reactjs.org/) - Bibliothèque UI
- [TypeScript](https://www.typescriptlang.org/) - Typage statique
- [SASS](https://sass-lang.com/) - Préprocesseur CSS
- [MariaDB](https://mariadb.org/) - Base de données relationnelle

## 📁 Structure du projet

```
/
├── public/             # Fichiers statiques (images, sons...)
├── src/
│   ├── app/            # Pages et layouts Next.js
│   ├── db/             # Configuration et requêtes de base de données
│   ├── steps/          # Composants pour chaque étape du test
│   ├── ui/             # Composants d'interface réutilisables
│   └── utils/          # Fonctions utilitaires
├── docker/             # Configuration Docker
└── .env                # Variables d'environnement
```

## 🤖 Assistance IA

Le projet intègre des règles spécifiques pour CursorAI, permettant une manipulation facilitée du code via l'intelligence artificielle. Ces règles comprennent :

- Documentation des utilitaires spécifiques au projet (voir `DOC.md`)
- Conventions de nommage et de structure uniformisées
- Patterns de code documentés pour une meilleure compréhension par l'IA

Cette configuration permet d'accélérer le développement et la maintenance grâce à l'assistance IA directement dans l'IDE.

## 📜 Scripts disponibles

- `pnpm dev` - Lance le serveur de développement
- `pnpm build` - Génère la version de production
- `pnpm start` - Lance l'application compilée
- `pnpm lint` - Vérifie le code avec ESLint

## 🚢 Déploiement

L'application peut être déployée via Docker ou directement sur un serveur Node.js.

### Déploiement avec Docker

```bash
docker build -t test-auditif .
docker run -p 3000:3000 test-auditif
```

La configuration CI/CD via GitLab est disponible dans le fichier `.gitlab-ci.yml`.

## 🔒 Variables d'environnement

| Variable     | Description                    | Exemple                                 |
| ------------ | ------------------------------ | --------------------------------------- |
| DATABASE_URL | URL de connexion à la BDD      | `mariadb://user:pass@localhost:3306/db` |
| LOCALE       | Mode local (désactive GTM)     | `true`                                  |
| API_KEY      | Clé API pour services externes | `votre-clé-api`                         |

## 👥 Accessibilité

L'application intègre des fonctionnalités d'accessibilité pour permettre une utilisation par un large public. Utilisez le bouton d'accessibilité en haut à droite pour adapter l'interface à vos besoins.

## 📞 Support et Contact

Pour toute question ou support concernant cette application, veuillez contacter **Briac Ferté**, responsable du projet qui en a la connaissance complète.
