# POC « Hey Atol » : ouvrir le chatbot à la voix

Page de démonstration autonome (HTML et JavaScript, sans dépendance) qui écoute le micro en continu et ouvre
le chat quand on dit « **Hey Atol** ».

## Lancer le test
- **Windows** : double-cliquer sur `lancer_poc.bat` (Python requis), la page s'ouvre sur http://localhost:8000.
- **Autre** : `python -m http.server 8000` dans ce dossier, puis ouvrir http://localhost:8000.

Navigateur : **Chrome ou Edge** (ordinateur ou Android). Firefox n'a pas de reconnaissance vocale et Safari/iOS est peu fiable.
Le micro n'est autorisé que sur `localhost` ou en HTTPS (pas en ouvrant le fichier directement).

## Ce qui est corrigé par rapport à une implémentation « naïve »
| Problème fréquent | Correction dans `wake-word.js` |
|---|---|
| Le navigateur écrit « hey atoll », « et à tôle », « hé atole »… et le test `includes("hey atol")` échoue | Texte normalisé (accents, ponctuation), liste de variantes, comparaison approximative avec garde-fous contre les faux positifs (« et à tout », « hé à toi », « les atolls »…) |
| Seule la 1re proposition du moteur est lue | Lecture des 5 alternatives proposées |
| Détection lente (attente de la fin de phrase) | Lecture des résultats provisoires : réaction dès que « hey atol » est prononcé |
| L'écoute s'arrête toute seule après un silence ou ~1 min (Chrome) | Relance automatique, avec temporisation progressive si le moteur échoue en boucle |
| Langue non précisée | `lang = "fr-FR"` |
| La question qui suit est perdue ou mélangée avec « hey atol » | La question est lue dans la même session : « Hey Atol, quels sont vos horaires ? » d'une traite ou avec une pause |
| Double déclenchement | Anti-rebond de 2,5 s |

Le **journal** de la page affiche ce que le navigateur comprend réellement, ainsi que les erreurs expliquées
(micro refusé, service bloqué par le réseau de l'entreprise…). C'est l'outil de diagnostic principal.

## Intégration dans le site
```html
<script src="wake-word.js"></script>
<script>
  const ecouteur = WakeWord.creerEcouteur({
    onReveil: () => ouvrirLeChat(),
    onQuestion: (texte) => envoyerAuChatbot(texte),
  });
  boutonMicro.onclick = () => ecouteur.demarrer(); // le démarrage doit suivre un clic
</script>
```

## Tester la détection sans micro
`node test-wake-word.js`. La page propose aussi un champ « Tester la détection au clavier ».
