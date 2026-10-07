# Système Audio

Ce document décrit le système audio utilisé dans l'application pour la gestion des sons vocaux et tonaux.

## Vue d'ensemble

Le système audio est basé sur l'API Web Audio et utilise un hook React personnalisé `useAudioSystem` pour gérer la lecture des sons. Il permet de :

- Jouer des sons sur différents canaux
- Contrôler le volume par canal
- Gérer la stéréo (gauche/droite)
- Supporter la lecture en boucle

## Configuration

### Structure des fichiers audio

Les fichiers audio doivent être placés dans le dossier `public/audio/` avec la structure suivante :

- `public/audio/tonal/` : Pour les sons tonaux
- `public/audio/vocal/` : Pour les sons vocaux

### Utilisation du hook useAudioSystem

```typescript
const { isReady, setup, play, stop, setCanalVolume, stopAll } = useAudioSystem({
  audios: [
    {
      id: "tonal-1",
      url: "/audio/tonal/sound1.mp3",
      canal: "tonal",
    },
    {
      id: "vocal-1",
      url: "/audio/vocal/sound1.mp3",
      canal: "vocal",
    },
  ],
  side: "both", // "left", "right" ou "both"
});
```

## Fonctionnalités

### Initialisation

```typescript
// Appeler setup() au démarrage de l'application
await setup();
```

### Lecture des sons

```typescript
// Jouer un son
await play("tonal-1");

// Jouer en boucle
await play("tonal-1", { loop: true });

// Arrêter un son
stop("tonal-1");

// Arrêter tous les sons
stopAll();
```

### Contrôle du volume

```typescript
// Contrôler le volume d'un canal (0 à 1)
setCanalVolume("tonal", 0.5);
setCanalVolume("vocal", 0.7);
```

## Bonnes pratiques

1. **Initialisation** : Toujours appeler `setup()` avant d'utiliser les fonctions de lecture
2. **Gestion des ressources** : Appeler `stopAll()` quand l'application est fermée
3. **Volume** : Les valeurs de volume sont quadratiques (0.5 = 25% du volume)
4. **Canal** : Utiliser des canaux distincts pour les sons tonaux et vocaux

## Limitations

- Le système utilise l'API Web Audio, qui nécessite une interaction utilisateur pour démarrer
- Les fichiers audio doivent être au format supporté par le navigateur (MP3, WAV, etc.)
- La latence peut varier selon le navigateur et le système
