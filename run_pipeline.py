"""Execute tout le pipeline : extraction -> nettoyage + controle qualite -> modele en etoile -> figure du README."""
import runpy
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"

for step in ["01_extract.py", "02_clean.py", "03_build_model.py", "04_charts.py"]:
    print(f"\n=== {step} ===")
    runpy.run_path(str(SRC / step), run_name="__main__")
