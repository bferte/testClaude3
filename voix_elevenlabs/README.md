# Voix ElevenLabs (mini front)

Page web statique (HTML + CSS + JavaScript, sans dépendance ni compilation) qui liste les voix de votre
compte ElevenLabs et indique celles que **l'API vous laisse utiliser**.

## Utilisation
Ouvrir `index.html` dans le navigateur (double-clic), saisir la clé API, cliquer sur **Charger les voix**.

- **Filtres** : recherche (nom, description, ID), langue, genre, et « Utilisables via l'API uniquement »
  (coché par défaut).
- **▶ Extrait** : écoute l'échantillon fourni par ElevenLabs (gratuit).
- **Tester** : synthétise la phrase de test avec la voix et le modèle choisis, puis la joue. Consomme
  quelques crédits. Le résultat confirme le statut de la voix (« ✓ API vérifiée », ou « Abonnement requis »
  si l'API répond 402).
- **Copier l'ID** : pour réutiliser la voix ailleurs, par exemple dans le champ « …ou ID d'une autre voix »
  de l'appli `tts_elevenlabs`.

## Quelles voix sont « utilisables via l'API » ?
- voix **premade** et voix que vous avez créées ou clonées : oui ;
- voix ajoutées depuis la **Voice Library** (Yann, Antoine…) : seulement avec un abonnement payant ; en
  compte gratuit, l'API répond `402 Free users cannot use library voices via the API`.

La clé doit avoir la permission **Voices : read** (et **Text to Speech** pour le bouton Tester).

## Sécurité
La clé reste dans votre navigateur et n'est envoyée qu'à `api.elevenlabs.io`. Elle n'est mémorisée
(dans le `localStorage` du navigateur) que si vous cochez « Mémoriser sur ce navigateur ».
