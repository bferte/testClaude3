# Calibre & Épaisseur — aide à la vente et au conseil technique en magasin d'optique

Estime l'épaisseur au bord (et au centre) des deux verres **taillés dans la monture choisie**, à partir de :

- l'**ordonnance** OD/OG (sphère, cylindre, axe TABO) ;
- l'**indice / matériau** (1.50, Trivex 1.53, polycarbonate 1.59, 1.60, 1.67, 1.74) ;
- la **géométrie** du verre (sphérique ou asphérique, base avant automatique ou imposée, centre mini) ;
- la **monture** : forme type (ronde, rectangle, carrée, pantos, aviateur, papillon) ou **tracé réel OMA/VCA**
  importé du traceur, calibre A × B, pont, type de montage (cerclé, nylor, percé → bord mini) ;
- la **prise de mesure** : demi-écarts pupillaires et hauteurs OD/OG (décentrement du centre optique).

Résultats : vue de face des verres colorée par épaisseur, bord le plus épais et sa position (temporal, bas…),
centre, poids estimé, décentrement, diamètre de palet minimal, coupe horizontale, **comparatif de tous les
indices** et phrase d'argumentaire prête à dire au client (« 30 % plus fin, 6 g de moins »).

## Utilisation

Ouvrir `index.html` dans un navigateur (double-clic, aucune installation, fonctionne hors ligne hormis les
polices). Aucune donnée ne quitte le poste.

## Modèle de calcul (`calcul.js`)

- Face avant sphérique (asphérique : conique qui aplatit un positif / cambre un négatif vers le bord), base
  exprimée à l'indice d'outil 1.53, choisie par défaut selon la règle de Vogel.
- Face arrière torique (surface biconique) calculée pour donner la puissance frontale arrière dans chaque
  méridien, avec correction d'épaisseur (lentille épaisse).
- Épaisseur en tout point = centre + flèche arrière − flèche avant, évaluée autour du centre optique décentré.
- Épaisseur centre = max(centre mini du matériau, valeur garantissant le bord mini sur **la forme**)
  → surfaçage optimisé forme, comme le font les laboratoires.
- Poids = intégration de l'épaisseur sur la surface de la forme × densité du matériau.

Limites : unifocaux uniquement (pas de progressifs ni prismes prescrits / prisme d'allègement), biseau et
rainure non modélisés, designs asphériques réels propres à chaque fabricant. Les écarts attendus avec un
calcul laboratoire sont de quelques dixièmes de millimètre.

## Tests

```bash
node --test epaisseur_verres/calcul.test.js
```
