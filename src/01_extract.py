"""Etape 1 - Extraction.

Telecharge les deux tables du jeu de donnees public freMTPL2 (OpenML, licence CC0) :
- freMTPL2freq : une ligne par contrat (exposition, nombre de sinistres, caracteristiques)
- freMTPL2sev  : une ligne par sinistre (montant)
"""
from pathlib import Path
import urllib.request

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

SOURCES = {
    "freMTPL2freq.parquet": "https://data.openml.org/datasets/0004/41214/dataset_41214.pq",
    "freMTPL2sev.parquet": "https://data.openml.org/datasets/0004/41215/dataset_41215.pq",
}
EXPECTED_ROWS = {"freMTPL2freq.parquet": 678_013, "freMTPL2sev.parquet": 26_639}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        path = RAW / name
        if not path.exists():
            print(f"Telechargement de {name}...")
            urllib.request.urlretrieve(url, path)
        rows = len(pd.read_parquet(path))
        if rows != EXPECTED_ROWS[name]:
            raise ValueError(f"Controle bloquant : {name} contient {rows:,} lignes, {EXPECTED_ROWS[name]:,} attendues")
        print(f"{name}: {rows:,} lignes (OK)")


if __name__ == "__main__":
    main()
