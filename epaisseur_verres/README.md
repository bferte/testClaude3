# Calibre & Épaisseur — aide à la vente et au conseil technique en magasin d'optique

Estime l'épaisseur au bord (et au centre) des deux verres **taillés dans la monture choisie**, à partir de :

- l'**ordonnance** OD/OG (sphère, cylindre, axe TABO) ;
- l'**indice / matériau** (1.50, Trivex 1.53, polycarbonate 1.59, 1.60, 1.67, 1.74) ;
- la **géométrie** du verre (sphérique ou asphérique, base avant automatique ou imposée, centre mini) et le
  **précalibrage** (oui : bord mini tenu sur la forme ; non : tenu sur tout le palet rond, Ø auto ou imposé) ;
- la **monture** : forme type (ronde, rectangle, carrée, pantos, aviateur, papillon) ou **tracé réel OMA/VCA**
  importé du traceur, calibre A × B, pont, type de montage (cerclé, nylor, percé → bord mini) ;
- en option pour les montures **cerclées** : matière du cercle (plastique ≈ 4,5 mm, métal ≈ 2,5 mm de
  profondeur, modifiable) et position du **biseau**, en % de l'épaisseur du bord depuis l'avant ou en mm depuis
  la face avant → débord du verre **devant et derrière le cercle** sur tout le contour ;
- la **prise de mesure** : demi-écarts pupillaires et hauteurs OD/OG (décentrement du centre optique).

Résultats : vue de face des verres colorée par épaisseur, **vue 3D** orientable (verres + cercle, épaisseurs
réelles ou exagérées), bord le plus épais et sa position (temporal, bas…),
centre, poids estimé, découpes horizontale et verticale de chaque verre avec le cercle, zoom du bord en haut, en bas, côté nasal
et côté temporal (débord devant/derrière le cercle) et biseau conseillé pour que rien ne dépasse devant, décentrement, diamètre de palet minimal, **comparatif de tous les
indices** et phrase d'argumentaire prête à dire au client (« 30 % plus fin, 6 g de moins »).

## Utilisation

Ouvrir `index.html` dans un navigateur (double-clic, aucune installation, fonctionne hors ligne hormis les
polices). Aucune donnée ne quitte le poste.

## Charte graphique

Couleurs, polices et logo se règlent sans toucher au code : voir [`chartes/LISEZMOI.md`](chartes/LISEZMOI.md).
`chartes/atol.css` est un gabarit à compléter avec les valeurs officielles du kit de marque.

La vue 3D utilise three.js (chargé depuis cdnjs) : une connexion internet est nécessaire pour l'afficher.

## Modèle de calcul (`calcul.js`)

- Face avant sphérique (asphérique : conique qui aplatit un positif / cambre un négatif vers le bord), base
  exprimée à l'indice d'outil 1.53, choisie par défaut selon la règle de Vogel.
- Face arrière torique (surface biconique) calculée pour donner la puissance frontale arrière dans chaque
  méridien, avec correction d'épaisseur (lentille épaisse).
- Épaisseur en tout point = centre + flèche arrière − flèche avant, évaluée autour du centre optique décentré.
- Épaisseur centre = max(centre mini du matériau, valeur garantissant le bord mini sur **la forme**)
  → surfaçage précalibré sur la forme. Sans précalibrage, le bord mini (0,8 mm) doit aussi être tenu sur le
  pourtour du palet rond centré sur le centre optique (plus petit Ø usuel 55–80 couvrant la forme, ou imposé).
- Cerclage : le sommet du biseau est logé dans la rainure, supposée au milieu de la profondeur du cercle ;
  débord devant = biseau − profondeur/2, débord derrière = bord − biseau − profondeur/2.
- Poids = intégration de l'épaisseur sur la surface de la forme × densité du matériau.

Limites : unifocaux uniquement (pas de progressifs ni prismes prescrits / prisme d'allègement), biseau et
rainure non modélisés, designs asphériques réels propres à chaque fabricant. Les écarts attendus avec un
calcul laboratoire sont de quelques dixièmes de millimètre.

## Tests

```bash
node --test epaisseur_verres/calcul.test.js
```
