# Architecture de l'Application

Ce document décrit l'architecture globale de l'application de test auditif.

## Vue d'ensemble

L'application est construite avec Next.js et utilise une architecture modulaire avec les composants suivants :

- Frontend React avec Next.js
- API Routes pour le backend
- Système de session JWT
- Système de steps modulaire
- Système audio Web Audio API

## Structure du projet

```
src/
├── app/                    # Pages et routes Next.js
│   ├── [shop_id]/         # Routes dynamiques pour les boutiques
│   ├── cgu/               # Conditions générales d'utilisation
│   ├── session/           # Gestion des sessions
│   ├── test/              # Page de test
│   └── layout.tsx         # Layout principal
├── libs/                   # Bibliothèques utilitaires
├── steps/                  # Système de steps
├── ui/                     # Composants UI réutilisables
└── utils/                  # Utilitaires
```

## Technologies principales

### Frontend

- Next.js 14
- React
- TypeScript
- SCSS Modules
- Web Audio API

### Backend

- API Routes Next.js
- JWT pour l'authentification
- Base de données (à spécifier)

## Fonctionnalités principales

### 1. Système de Steps

- Gestion des étapes du test
- Navigation entre les étapes
- Sauvegarde des résultats

### 2. Système Audio

- Lecture des sons tonaux
- Lecture des sons vocaux
- Contrôle du volume par canal

### 3. Système de Session

- Authentification JWT
- Gestion des accès boutique/en ligne
- Sécurisation des routes

### 4. Interface utilisateur

- Design responsive
- Composants réutilisables
- Gestion des états

## Bonnes pratiques

1. **Architecture**

   - Séparation claire des responsabilités
   - Composants modulaires
   - Réutilisation du code

2. **Performance**

   - Optimisation des images
   - Chargement différé des composants
   - Mise en cache des données

3. **Sécurité**

   - Validation des données
   - Protection des routes
   - Gestion sécurisée des sessions

4. **Maintenance**
   - Documentation claire
   - Tests unitaires
   - Code typé avec TypeScript

## Déploiement

L'application est déployée avec Docker et utilise :

- Node.js comme runtime
- Nginx comme serveur web
- Variables d'environnement pour la configuration

## Variables d'environnement

```env
# Session
SESSION_TOKEN_SECRET=

# Base de données
DATABASE_URL=

# Configuration
NEXT_PUBLIC_API_URL=
```

## Limitations

- Nécessite un navigateur moderne pour l'API Web Audio
- Dépend d'une connexion internet stable
- Limité aux formats audio supportés par le navigateur
