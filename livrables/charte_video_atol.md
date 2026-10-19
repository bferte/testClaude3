# Charte vidéo ATOL — présentation d'outils (motion design)

Référence : vidéo « PAF — Plan Annuel de Formation » v4 (`livrables/PAF_ATOL_motion_v4.mp4`).
Code de l'animation réutilisable : `livrables/source/` (page HTML animée, rendue image par image dans Chromium, puis encodée avec ffmpeg).

---

## 1. Format
- 1920×1080, 30 i/s, MP4 H.264 + AAC.
- Durée : 60 à 90 s.
- Aucun sommaire, aucune numérotation « 1., 2. » : on raconte avec des titres courts et animés.

## 2. Couleurs
| Rôle | Couleur |
|---|---|
| Intro, drop et outro (logo) | bleu nuit `#1B2D50` |
| Scènes foncées | bleu ATOL `#13386C` |
| Dernière ligne des titres, contours de mise en valeur | bleu moyen `#87B1E5` |
| Sous-textes sur fond foncé, formes décoratives sur fond clair | bleu pâle `#C4E2F9` |
| Scènes claires (produit) | blanc cassé `#F7F5F2` |
| Phrases sur fond clair | gris bleuté `#5C6E87` |
| Cadre des téléphones | `#0F1B33` |

- Les fonds alternent foncé / clair d'une scène à l'autre : bleu ATOL, puis blanc cassé, puis bleu ATOL…
- Seule exception tolérée : la première scène après le logo peut être foncée elle aussi.
- Ne pas utiliser le bleu pâle en fond sous un titre : le bleu moyen n'y serait pas lisible.
- Formes de fond : grands cercles pleins et anneaux fins, très peu opaques, qui dérivent lentement.

## 3. Typographie
- Police : Poppins.
  - Bold 700 pour les titres.
  - Light 300 pour les sous-titres et les capitales espacées.
  - Regular 400 pour les phrases.
- Titres :
  - très gros, de 90 à 170 px, réduits automatiquement pour tenir dans la colonne ;
  - interlettrage serré (−3 px) ;
  - 1 à 3 lignes, la dernière en bleu moyen ;
  - un titre d'une seule ligne est entièrement en bleu moyen.
- Ponctuation : chaque ligne finit par un point (« Vos équipes. »).
- Phrase explicative : environ 29 px, interligne 1,48, largeur environ 620 px.
- Nom de l'outil sous le logo : en CAPITALES, Light, interlettrage 14 px, en bleu pâle.

## 4. Structure
| Bloc | Durée | Contenu |
|---|---|---|
| Intro | 0 → 9,5 s | Un point blanc pulse au centre. Puis la phrase d'accroche en 2 lignes, « [Nom], / *[promesse].* ». Puis 5 captures de l'outil en cascade qui foncent vers la caméra. |
| Drop | 9,5 s, 2 mesures | Flash blanc. Logo ATOL blanc avec un léger rebond. « [NOM COMPLET DE L'OUTIL] » en capitales espacées. Fond bleu nuit. |
| Scènes fonctionnalités | 5 à 8 mesures chacune (9 à 15 s) | Titre à gauche, phrase dessous, extrait vidéo ou capture à droite dans une carte blanche. |
| Bénéfices | 4 mesures | 3 lignes centrées, du type « Plus simple. / Plus rapide. / *Plus ciblé.* ». |
| Outro | environ 4,7 s | Flash, logo ATOL et nom de l'outil, fondu au noir. |

Règles de mise en page des scènes :
- Colonne de texte à gauche (x = 110 px, largeur environ 690 px), carte à droite (environ 990 px de large).
- Une capture très large et très basse (un bandeau) se place sous le texte, sur toute la largeur.
- Deux petites cartes (par exemple deux encadrés) s'empilent l'une sous l'autre à droite et entrent en décalé de 0,35 s.

## 5. Rythme et animation
- Rythme posé : on laisse le temps de lire chaque phrase et de voir chaque fonctionnalité.
- Changements de scène : toujours sur un début de mesure, jamais sur chaque temps. Transition : la nouvelle scène monte depuis le bas en 0,55 s et se pose sur la mesure.
- Seulement 2 impacts forts : le drop et le logo final. Aucun « bump » ni zoom sur les temps.
- Texte :
  - la phrase explicative est visible dès le début de la scène (montée de 40 px en fondu, 0,8 s) ;
  - les mots du titre arrivent un par un, en glissant de bas en haut dans un masque (easing expo, 0,6 s), espacés de 0,5 s.
- Cartes :
  - blanches, coins arrondis de 24 px, ombre douce ;
  - entrée par un glissement de 140 px avec une rotation 3D (−16° en Y, 5° en X) qui se redresse en 1,2 s ;
  - puis zoom très lent, +3,5 % sur toute la scène.
- Mise en valeur : contour bleu moyen de 5 px, coins arrondis de 16 px, halo léger, qui apparaît en fondu (0,6 s) vers la fin de la scène, une fois l'action visible.

## 6. Captures et extraits vidéo
- Montrer la partie utile (fenêtre, panneau, tableau) en entier, sans jamais rogner ses bords. Garder le ratio de l'image et ne pas trop zoomer.
- Retirer de l'image la barre de navigation du haut et le menu latéral, sauf dans les captures de l'intro.
- Retirer les chargements, les écrans gris ou vides et les attentes du type « Enregistrement… ».
- Exclure les filigranes et les consoles de développement.
- Vitesse : réelle, ou accélérée modérément (×1 à ×1,4) ; on n'accélère que les temps morts.
- Vidéos mobiles : dans un téléphone (cadre `#0F1B33`, coins arrondis), avec un second téléphone flou derrière.
- Le texte doit rester fidèle à ce que montre l'écran. Si une fonction est inactive dans l'enregistrement, la phrase ne la promet pas.

## 7. Musique
- Analyser le tempo (environ 129 BPM ; une mesure = 4 temps, environ 1,86 s) et repérer la montée.
- Faire démarrer le morceau en cours de route pour que sa montée tombe exactement sur le drop (9,5 s).
- Musique continue, sans aucune coupure ni raccord : pas de saut vers la fin du morceau, ça s'entend trop.
- Le logo final tombe sur une frappe forte, sur un début de mesure. Ensuite, fondu musical sur les 4 dernières secondes, en même temps que le fondu au noir.

## 8. Livrables et validation
1. **Avant le rendu** : le texte de chaque scène (titre, phrase, extrait utilisé avec son minutage), à valider.
2. Le MP4 final.
3. Une page d'artefact avec le lecteur vidéo et le tableau des textes.
4. Le fichier MP4 envoyé en pièce jointe dans la conversation, pour le télécharger.

---

## 9. Prompt type (à copier, puis remplir les crochets)

```
Crée une vidéo motion design de présentation de l'outil [NOM COURT] ([NOM COMPLET]) pour le réseau ATOL.
Elle doit respecter la charte vidéo ATOL décrite dans livrables/charte_video_atol.md
(branche claude/eloquent-clarke-v2n2uw du dépôt bferte/testClaude3) : même DA, même ambiance,
même rythme que la vidéo PAF v4. Réutilise le code d'animation de livrables/source/.

## Sources fournies
- Enregistrements d'écran en PJ : [liste des fichiers]
- Captures d'écran en PJ : [liste, ou « aucune »]
- Musique : [fichier en PJ, ou « la même que la vidéo PAF »]
- Logo ATOL blanc en PJ

## Accroche d'intro (2 lignes)
« [Nom], / [promesse courte] »

## Nom affiché sous le logo
« [NOM COMPLET EN CAPITALES] »

## Fonctionnalités à présenter (dans l'ordre)
1. Titre : « [Ligne 1.] / [Ligne 2.] / [Ligne 3.] »
   Phrase : « [phrase explicative, une à deux lignes] »
   Source : [fichier] de [mm:ss] à [mm:ss]   (ou : capture [fichier])
   Mettre en valeur : [bouton / zone à entourer]
2. …
3. …

## Bénéfices de fin (3 lignes)
« [Plus ….] / [Plus ….] / [Plus ….] »

## Contraintes particulières
- Durée cible : [60–90 s]
- [Autres demandes]

## Livrables
- D'abord le texte de chaque scène, à valider avant le rendu final.
- Puis le MP4, une page d'artefact avec le lecteur et les textes,
  et le MP4 en pièce jointe pour le télécharger.
```
