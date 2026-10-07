Les attributs ajoutés sont sous la forme data-\*

# Attributs de screen

Les attributs `data-screen` sont ajoutés à chaque étape du test :

- `data-screen="introduction"`
- `data-screen="questions"`
- `data-screen="vocal-test"`
- `data-screen="tonal-test"`
- `data-screen="result"`

# Attributs de button

Chaque button a un attribut `data-button`.

- `data-button="start-test"`
- `data-button="custom-test"`
- `data-button="yes"`
- `data-button="no"`
- `data-button="find-center"`
- `data-button="call-me"`
- `data-button="ask-call"`
- `data-button="new-test"`

# Particularités

- `data-question` : attribut ajouté à chaque question de la page `QuestionsStep`

# Accessibilité

- `data-button="dyslexic"`
- `data-button="inversed-contrast"`
- `data-button="large-fonts"`

# Implémentation de Google Tag Manager

Google Tag Manager est implémenté dans deux contextes différents :

## Layout Web

Dans le layout principal (`src/app/(web)/layout.tsx`), GTM est configuré avec le contexte 'web' :

```typescript
dataLayer={{
    context: 'web'
}}
```

## Page Session

Dans la page de session (`src/app/session/[session_id]/page.tsx`), GTM est configuré avec des informations spécifiques à la session :

```typescript
dataLayer={{
    context: 'shop',
    shop_id: sessionData.shop_id,
    user_id: sessionData.user_id
}}
```
