# Utilitaire classNameModule

> **IMPORTANT**: Cette méthode doit TOUJOURS être utilisée pour importer et appliquer les styles SCSS dans le projet.

## Importation

```js
import classNameModule from "@classname";
import styles from "./Component.module.scss";
const className = classNameModule(styles);
```

## Syntaxes

```jsx
// Classe simple
<div {...className("Container")} />

// Classes conditionnelles
<div {...className("Button", { active: isActive, disabled: true })} />

// Avec valeurs
<div {...className("Card", { type: "large" })} />

// Classes globales (non transformées par CSS Modules)
<div {...className("Component", ":global-class")} />

// Combinaisons
<div {...className("Card", { highlighted: true }, `:${externalClassName}`)} />
```

## Comportement

- `"NomClasse"` → Recherche et applique le hash CSS Module
- `{ condition: true }` → Ajoute la classe `condition` si true
- `{ type: "valeur" }` → Ajoute la classe `type-valeur`
- `":classe-globale"` → Ajoute la classe littérale sans transformation
