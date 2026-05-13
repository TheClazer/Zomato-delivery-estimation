"""Generate proper .ipynb files from the canonical _run_*.py scripts and the
05_pivot skeleton. Run once; commit the resulting notebooks."""
import json, re, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"


def cell(source, kind="code"):
    return {
        "cell_type": kind,
        "metadata": {},
        "source": source if isinstance(source, list) else [source],
        **({"execution_count": None, "outputs": []} if kind == "code" else {}),
    }


def write_nb(path, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def split_py_into_cells(py_path, intro_md=None):
    """Split a runner script on '# ---- ... ----' bars into notebook cells."""
    text = py_path.read_text(encoding="utf-8")
    # First non-empty block up to the first divider is the prologue/imports
    parts = re.split(r"\n# ---- (.*?) ----\n", text)
    cells = []
    if intro_md:
        cells.append(cell(intro_md, "markdown"))
    # parts[0] = prologue; then (title, body, title, body, ...)
    cells.append(cell(parts[0].rstrip() + "\n"))
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].rstrip() + "\n" if i + 1 < len(parts) else ""
        cells.append(cell(f"## {title}\n", "markdown"))
        cells.append(cell(body))
    return cells


# 01_eda.ipynb
intro_eda = (
    "# 01 — Exploratory Data Analysis\n\n"
    "Loads the raw Zomato delivery CSV, applies minimal inline cleaning, "
    "produces figures `fig01`–`fig09` and an `eda_summary.json` consumed by "
    "the deck builder. Runs end-to-end independent of P1's processed parquet."
)
write_nb(NB_DIR / "01_eda.ipynb", split_py_into_cells(NB_DIR / "_run_eda.py", intro_eda))

# 06_interpretability.ipynb
intro_shap = (
    "# 06 — Interpretability (SHAP)\n\n"
    "Loads the tuned LightGBM v1 booster and produces SHAP beeswarm + bar "
    "summary plots. Top-feature ranking is written to `reports/shap_top.json`."
)
write_nb(NB_DIR / "06_interpretability.ipynb",
         [cell(intro_shap, "markdown"), cell((NB_DIR / "_run_shap.py").read_text(encoding="utf-8"))])

# Remove stale duplicate placeholders
for stale in ["03_model_baseline.ipynb", "04_model_tuned.ipynb", "02_features.ipynb", "05_pivot_merge.ipynb"]:
    p = NB_DIR / stale
    if p.exists() and p.stat().st_size < 200:
        p.unlink()
        print(f"removed empty {stale}")
