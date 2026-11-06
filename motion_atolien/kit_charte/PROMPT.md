# Prompt : vidéo motion design à la charte « Le nouvel Atolien »

À copier dans une nouvelle conversation, avec les fichiers listés dans la section « Fichiers à joindre » plus bas. Remplacer tout ce qui est entre [crochets].

---

```
Crée une vidéo motion design de présentation de [NOM DU SUJET / DE L'OUTIL] pour le réseau ATOL (800 magasins d'optique et d'audition).
Elle doit reprendre exactement la charte, le rythme et les règles d'animation de la vidéo « Le nouvel Atolien » (version dynamique) : la planche de référence et les images jointes montrent le résultat attendu.

## Livrable
- MP4 1920×1080, 30 i/s, H.264 + AAC, durée [60 à 80 s].
- [Option : une version verticale 9:16 de la même vidéo.]
- Me donner aussi le texte de chaque scène pour validation avant le rendu final.

## Méthode de fabrication (celle qui a servi pour l'Atolien)
- Une page HTML 1920×1080 où toute l'animation est une fonction du temps : render(t) calcule l'état de chaque élément à l'instant t (pas d'animation CSS ni d'horloge), avec des fonctions d'easing (expo-out, cubic in-out, back léger) et des ressorts amortis calculés de façon déterministe.
- Les extraits vidéo sont découpés en images (ffmpeg) et dessinés image par image dans des <canvas> : jamais de balise <video> pendant la capture.
- Capture image par image avec Playwright (Chromium headless), puis assemblage avec ffmpeg et ajout de la musique.
- Avant le rendu complet : sortir une image par scène, la regarder, et corriger tout texte coupé, élément qui déborde ou image recadrée.

## Charte graphique
- Police : Poppins. Bold 700 pour les titres, Light 300 pour les sous-titres, Regular 400 pour les phrases.
- Couleurs :
  - bleu nuit #1B2D50 (ouverture, final, scènes « fortes »)
  - bleu ATOL #13386C (scènes foncées)
  - bleu moyen #87B1E5 (2e ligne de titre, mot accentué)
  - bleu pâle #C4E2F9 (fond clair, texte secondaire sur fond foncé)
  - blanc cassé #F7F5F2 (fond clair des scènes produit)
  - gris bleuté #5C6E87 (phrases sur fond clair)
- Alterner fonds foncés et fonds clairs d'une scène à l'autre.
- Titres très gros : 90 à 170 px, interlettrage serré (-2 à -4 px), sur 2 ou 3 lignes. La dernière ligne en bleu moyen.
- Sous chaque titre, une phrase explicative de 1 à 3 lignes (31 à 34 px).
- Captures et extraits d'écran dans des cartes blanches : coins arrondis 22-26 px, ombre douce et large.
- Écrans mobiles dans un téléphone (cadre #0F1B33, coins très arrondis), avec un second téléphone flou et décalé derrière pour la profondeur.
- Ouverture et final : logo ATOL blanc sur fond bleu nuit avec les grandes formes arrondies de la charte (image fournie).
- Mettre en valeur une zone d'une capture avec un contour arrondi bleu moyen qui apparaît en fondu.

## Structure
1. Ouverture : flash blanc et logo ATOL qui s'installe avec un léger rebond, sous-titre « [NOM DU SUJET] » en capitales très espacées, sur le premier temps fort de la musique.
2. Phrase d'accroche (environ 2 s) : « [Accroche ligne 1] » / « [Accroche ligne 2] » qui montent puis sortent vers le haut.
3. Une scène par fonctionnalité (6 à 12 s chacune) : titre court + phrase explicative visibles DÈS LE DÉBUT de la scène, et à côté l'extrait vidéo ou la capture qui montre la fonctionnalité.
4. Final : trois lignes de bénéfices qui montent l'une après l'autre (« [Bénéfice 1.] [Bénéfice 2.] [Bénéfice 3.] »), puis flash, logo ATOL + « [Nom du sujet] », et fondu au noir.

## Rythme et animation (retours déjà validés sur l'Atolien)
- Rythme posé : on doit avoir le temps de lire et de voir chaque fonctionnalité.
- Les changements de scène tombent sur des débuts de mesure, toutes les 2 mesures ou plus. Jamais un changement à chaque temps.
- AUCUN « bump » ou zoom à chaque temps. Seulement 2 impacts forts : l'ouverture (logo) et le logo final.
- Textes : chaque ligne glisse de bas en haut dans un masque (easing expo, 0,6 s), les lignes arrivent l'une après l'autre (0,3 à 1 s d'écart). Le masque doit cacher complètement le texte avant son entrée (aucun reste de lettre visible).
- Cartes et fenêtres : elles bougent dès la première image de leur scène, partent complètement hors de l'écran et apparaissent en fondu pendant qu'elles glissent. Jamais un bout de fenêtre immobile visible avant l'animation.
- Pendant la scène, zoom très lent (+2 à 4 %) ; légère perspective 3D à l'entrée qui se redresse.
- Pas de restes de la scène précédente au début d'une scène.

## Extraits vidéo (important)
- Montrer la partie utile (fenêtre, panneau, liste) EN ENTIER : ne jamais rogner les bords, ne pas trop zoomer.
- Retirer les images de chargement, d'écran grisé ou vides.
- Exclure du cadre les filigranes (ex. « clideo.com ») et les consoles de développement.
- Vitesse réelle ou accélération modérée (×1 à ×1,6) ; accélérer davantage seulement les temps morts (attente d'une réponse, chargement).
- Si une capture est petite (moins de 600 px de large), le signaler : elle sera floue une fois agrandie.

## Musique
- Utiliser la musique fournie EN CONTINU, sans aucune coupure ni raccord à l'intérieur du morceau.
- Analyser le tempo et repérer le premier temps fort : la vidéo commence dessus avec le logo.
- Caler les changements de scène sur les débuts de mesure et le logo final sur une reprise forte du morceau.
- Terminer par un fondu de 3 s si le morceau continue après la fin de la vidéo.

## Contenu du sujet
- Public : [collaborateurs en magasin / opticiens / audioprothésistes / clients].
- Message à retenir : [une phrase].
- Fonctionnalités à présenter, dans l'ordre :
  1. [Titre court] — [phrase explicative] — source : [fichier vidéo + minutage, ou capture]
  2. [...]
  3. [...]
- Textes à ne pas modifier : [...]
- Éléments à ne jamais montrer : [vrais numéros, noms de personnes, chiffres internes...]
```

---

## Fichiers à joindre

### Charte (à réutiliser tels quels pour chaque vidéo)
| Fichier | D'où le sortir |
|---|---|
| Logo ATOL **blanc** (PNG transparent) | PPT « Refonte de l'Atolien », diapositive 1, ou le kit de marque |
| Logo ATOL **bleu** (PNG transparent) | même PPT, ou le kit de marque |
| Fond d'ouverture bleu nuit avec les formes arrondies (PNG 1920×1080) | PPT, diapositive 1 (image de fond) |
| Mascotte robot ATOL (PNG, si le sujet parle de l'IA) | capture du chatbot Atolien ou le fichier source de la mascotte |
| Police Poppins (Regular, Light, Bold) | Google Fonts |
| Musique : `nastelbom-corporate-upbeat` (MP3) | même fichier que pour l'Atolien, pour la cohérence |
| Références de style : `references/planche_style.jpg` et les 10 images du dossier `references/` | ce dossier |
| Vidéo de référence : `nouvel_atolien_dynamique.mp4` | dossier `motion_atolien/` |

### Spécifique au sujet (à demander au métier)
- Le PPT ou le document qui présente le sujet (textes, ordre des fonctionnalités).
- Un enregistrement d'écran par fonctionnalité, sans filigrane, en bonne résolution (page zoomée si le texte est petit) ; pour le mobile, enregistré directement sur le téléphone.
- Les captures d'écran fixes utiles (pages, écrans d'accueil).
- Les textes validés : accroche, titres, phrases, bénéfices, phrase finale.
- La liste de ce qui ne doit pas apparaître à l'écran.
