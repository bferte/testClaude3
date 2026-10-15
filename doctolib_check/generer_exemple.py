"""Génère urls_magasins_exemple.xlsx, un exemple de fichier d'entrée."""
from pathlib import Path

import pandas as pd

urls = [
    "https://www.doctolib.fr/opticien/paris/optique-exemple-paris-11",
    "https://www.doctolib.fr/opticien/lyon/optique-exemple-lyon-centre",
    "https://www.doctolib.fr/audioprothesiste/marseille/audition-exemple-marseille",
    "https://www.doctolib.fr/opticien/lille/optique-exemple-lille",
    "https://www.doctolib.fr/audioprothesiste/nantes/audition-exemple-nantes",
]
df = pd.DataFrame({"Code magasin": [f"MAG{i:03d}" for i in range(1, len(urls) + 1)], "URL": urls})
sortie = Path(__file__).with_name("urls_magasins_exemple.xlsx")
df.to_excel(sortie, index=False)
print(f"Exemple écrit : {sortie}")
