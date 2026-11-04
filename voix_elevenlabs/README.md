# Voix ElevenLabs (mini front)

Page web statique (HTML + CSS + JavaScript, sans dépendance ni compilation) qui liste les voix de votre
compte ElevenLabs et indique celles que **l'API vous laisse utiliser**.

## Synthèse vocale
En haut de la page : saisir le texte, choisir la voix (ou cliquer sur **Choisir** dans une fiche) et le
modèle, puis **Générer l'audio**. Chaque audio s'écoute dans la page et se télécharge en MP3.

Modèles proposés : ceux qui parlent français, lus sur `/v1/models` (liste connue si la clé n'a pas
« Models : read ») :

| Modèle | Pour quoi | Caractères max / requête (gratuit) |
|---|---|---|
| Multilingual v2 (par défaut) | Le plus stable pour de longs textes | 10 000 |
| Eleven v4 / v4 Turbo | Dernière génération, la plus expressive | 10 000 |
| Eleven v3 / v3 Conversational | Très expressif, balises d'émotion `[rire]`… | 5 000 |
| Flash v2.5 / Turbo v2.5 | Rapides, moitié moins de crédits | 40 000 |

Réglages : stabilité, similarité, style et vitesse.

## Utilisation
Ouvrir `index.html` dans le navigateur (double-clic), saisir la clé API, cliquer sur **Charger les voix**.

- **Filtres** : recherche (nom, description, ID), langue, genre, et « Utilisables via l'API uniquement »
  (coché par défaut).
- **▶ Extrait** : écoute l'échantillon fourni par ElevenLabs (gratuit).
- **Choisir** : sélectionne la voix dans le panneau de synthèse. Après une génération, le statut est
  confirmé (« ✓ API vérifiée », ou « Abonnement requis » si l'API répond 402).
- **Copier l'ID** : pour réutiliser la voix ailleurs, par exemple dans le champ « …ou ID d'une autre voix »
  de l'appli `tts_elevenlabs`.

## Quelles voix sont « utilisables via l'API » ?
- voix **premade** et voix que vous avez créées ou clonées : oui ;
- voix ajoutées depuis la **Voice Library** (Yann, Antoine…) : seulement avec un abonnement payant ; en
  compte gratuit, l'API répond `402 Free users cannot use library voices via the API`.

La clé doit avoir la permission **Voices : read** (et **Text to Speech** pour la synthèse).

## Sécurité
La clé reste dans votre navigateur et n'est envoyée qu'à `api.elevenlabs.io`. Elle n'est mémorisée
(dans le `localStorage` du navigateur) que si vous cochez « Mémoriser sur ce navigateur ».
