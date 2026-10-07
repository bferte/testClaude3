# Système de Session

Ce document décrit le système de gestion des sessions utilisé dans l'application pour sécuriser l'accès aux tests auditifs.

## Vue d'ensemble

Le système de session utilise des JWT (JSON Web Tokens) pour gérer l'authentification et l'autorisation des utilisateurs. Il permet de :

- Générer des tokens de session sécurisés
- Vérifier la validité des tokens
- Gérer les différents types d'accès (boutique ou en ligne)

## Configuration

### Variables d'environnement requises

```env
SESSION_TOKEN_SECRET=votre_secret_ici
```

## Fonctionnalités

### Génération de token

```typescript
const token = await generateSessionToken({
  type: "shop", // ou "online"
  user_id: "user123",
  shop_id: "shop456",
});
```

Le token généré :

- Contient un ID unique
- Est signé avec l'algorithme HS256
- Expire après 24 heures
- Inclut les informations de l'utilisateur et du contexte

### Vérification de token

```typescript
const payload = await verifySessionToken(token);
if (payload) {
  // Token valide
  const { type, user_id, shop_id } = payload;
} else {
  // Token invalide ou expiré
}
```

Le payload retourné contient :

- `type`: "shop" ou "online"
- `user_id`: Identifiant unique de l'utilisateur
- `shop_id`: Identifiant de la boutique (si applicable)

## Bonnes pratiques

1. **Sécurité**

   - Toujours utiliser HTTPS
   - Ne jamais stocker le secret dans le code source
   - Vérifier les tokens à chaque requête

2. **Gestion des erreurs**

   - Gérer les cas où le secret n'est pas configuré
   - Gérer les tokens expirés
   - Gérer les tokens invalides

3. **Performance**
   - Mettre en cache les résultats de vérification si nécessaire
   - Limiter la fréquence des vérifications

## Limitations

- Les tokens expirent après 24 heures
- Les tokens ne peuvent pas être révoqués individuellement
- Le système ne gère pas le refresh token
- Les données du token sont en lecture seule

## Exemple d'utilisation

```typescript
// Côté serveur
const token = await generateSessionToken({
  type: "shop",
  user_id: "user123",
  shop_id: "shop456",
});

// Côté client
const response = await fetch("/api/protected", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

// Vérification côté serveur
const payload = await verifySessionToken(token);
if (!payload) {
  throw new Error("Session invalide");
}
```
