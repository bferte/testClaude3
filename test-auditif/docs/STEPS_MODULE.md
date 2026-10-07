# Système de Steps

Ce document décrit le système de steps utilisé dans l'application pour gérer le flux de test auditif.

## Vue d'ensemble

Le système de steps est une architecture modulaire qui permet de gérer les différentes étapes du test auditif. Chaque étape est un composant indépendant qui peut être configuré et personnalisé.

## Types d'étapes disponibles

### 1. Introduction (`IntroductionStep`)

- Première étape du test
- Permet de personnaliser le type de test (complet, tonal, vocal)
- Configuration du contexte (boutique ou en ligne)
- Collecte des informations de base (genre, année de naissance)

```typescript
const introductionStep: IntroductionStep = {
  type: "introduction",
  customizable: true,
  defaultType: "complete",
  wording: "shop",
  agentInformation: {
    // Informations de l'agent si nécessaire
  },
};
```

### 2. Questions (`QuestionsStep`)

- Étape de questions préliminaires
- Support des images pour chaque question
- Réponses binaires (oui/non)

```typescript
const questionsStep: QuestionsStep = {
  type: "questions",
  config: {
    questions: [
      {
        id: "q1",
        content: "Question 1",
        image: "/images/q1.jpg",
      },
    ],
  },
};
```

### 3. Test Tonal (`TonalStep`)

- Test des fréquences auditives
- Configuration des fréquences à tester
- Mesure des seuils auditifs

```typescript
const tonalStep: TonalStep = {
  type: "tonal",
  config: {
    frequencies: [250, 500, 1000, 2000, 4000, 8000],
  },
};
```

### 4. Test Vocal (`VocalStep`)

- Test de la compréhension vocale
- Configuration du nombre d'étapes
- Mesure de la compréhension à différents niveaux

```typescript
const vocalStep: VocalStep = {
  type: "vocal",
  config: {
    steps: 5,
  },
};
```

### 5. Informations Personnelles (`PersonalInformationsStep`)

- Collecte des informations du patient
- Champs obligatoires : prénom, nom, email, téléphone

### 6. Résultats (`ResultStep`)

- Affichage des résultats du test
- Option pour afficher un formulaire de contact

## Structure des données

Les résultats du test sont structurés dans un objet `ResultData` qui contient :

```typescript
type ResultData = {
  introduction: {
    gender: "female" | "male";
    birthyear: number;
  };
  questions: {
    id: string;
    result: boolean;
  }[];
  tonal: {
    frequency: number;
    result: {
      volume: number;
      result: boolean;
    }[];
  }[];
  personalInformations: {
    firstname: string;
    lastname: string;
    email: string;
    phone: string;
  };
  vocal: {
    rnb: number;
    result: boolean;
  }[];
};
```

## Bonnes pratiques

1. **Configuration des étapes**

   - Toujours définir un type unique pour chaque étape
   - Fournir toutes les configurations requises
   - Valider les données avant de passer à l'étape suivante

2. **Gestion des données**

   - Sauvegarder les résultats intermédiaires
   - Valider les données avant de les utiliser
   - Gérer les cas d'erreur

3. **Navigation**
   - Permettre la navigation entre les étapes
   - Gérer le retour en arrière si nécessaire
   - Sauvegarder l'état de progression

## Limitations

- Les étapes doivent être exécutées dans l'ordre
- Les données des étapes précédentes ne sont pas modifiables
- La configuration des étapes est statique après l'initialisation
