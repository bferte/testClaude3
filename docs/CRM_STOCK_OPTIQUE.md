# Idée : logiciel de gestion de stock pour un magasin d'optique

Prototype cliquable : [`prototype_stock/stock_optique.html`](../prototype_stock/stock_optique.html)
(ouvrir dans un navigateur ; données de démonstration générées dans la page, aucune donnée réelle).

## Les trois besoins de départ

| Besoin | Ce que fait le prototype |
|---|---|
| **Péremption des lentilles et consommables** | Chaque lot (produit, puissance, n° de lot, date, quantité, tiroir) est classé par date (FEFO : premier périmé, premier vendu). Alertes à 90 j, 30 j et périmé, avec une action proposée (mettre devant, vendre en premier, retirer). |
| **Rotation des montures** | Ancienneté de chaque pièce depuis son entrée, montures dormantes (> 12 mois) et critiques (> 24 mois), ancienneté moyenne par marque. |
| **Doublons / triples** | Regroupement par marque + modèle + coloris + calibre (ex. `52□18-145`) ; nombre de pièces en trop et valeur d'achat récupérable ; action proposée (garder 1 en présentation, retourner/transférer le reste). |
| **Vue 3D (option)** | Plan du magasin en 3D activable depuis le tableau de bord : murs, îlots, vitrine, armoire à lentilles. Chaque monture et chaque tiroir est coloré selon l'ancienneté, les doublons ou la péremption ; clic = fiche détaillée ; filtre « alertes seulement ». |

## Autres idées

- Rappels de renouvellement lentilles (date de fin de boîte calculée à la vente, SMS au client).
- Suivi des ordonnances et de leur validité.
- Réassort automatique par puissance courante selon les ventes des 90 derniers jours.
- Retours fournisseurs : conditions par marque (quotas, délais, échanges de collection).
- Contrôle des catalogues fournisseurs à l'import avec l'outil `catalogue_qc` de ce dépôt.
- Traçabilité des lots (lecture du Datamatrix : lot + péremption) et rappel de lot immédiat.
- Inventaire tournant au scanner ou au téléphone.
- SAV / réparations / garanties fabricant.
- Marge et rotation par marque pour les négociations.
- Tiers payant et mutuelles.
- Transferts entre magasins d'un même groupe.
- Implantation des présentoirs depuis la vue 3D et mesure de l'effet sur les ventes.

## Feuille de route proposée

1. **Socle** : import du stock depuis l'export du logiciel métier (CSV/Excel), péremptions, doublons, dormantes, tableau de bord, export Excel.
2. **Stock vivant** : scan EAN/Datamatrix, inventaire tournant, réassort automatique, rappels clients.
3. **Pilotage** : plan 3D éditable, multi-magasins, prévisions saisonnières, marge par marque.

## Pistes techniques

Dans l'esprit de ce dépôt (outil local, données qui restent au magasin) :
moteur Python + SQLite, interface Streamlit ou web locale, la vue 3D en Three.js (comme le prototype).
Le stock ne remplace pas le logiciel de facturation : il s'alimente de ses exports, puis
d'une synchronisation quand l'éditeur le permet.
