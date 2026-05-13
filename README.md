# Zomato Delivery Estimation

A machine learning project to estimate delivery times for Zomato orders.

## Project Structure

```text
Zomato-delivery-estimation/
+-- data/
|   +-- raw/              # original dataset
|   +-- processed/        # cleaned parquet
|   +-- pivot/            # 3PM secret files
+-- notebooks/
|   +-- 01_eda.ipynb              # P2
|   +-- 02_features.ipynb         # P1
|   +-- 03_model_baseline.ipynb   # P1
|   +-- 04_model_tuned.ipynb      # P1
|   +-- 05_pivot_merge.ipynb      # P1 (post 3PM)
|   +-- 06_interpretability.ipynb # P2
+-- src/
|   +-- __init__.py
|   +-- data.py           # loaders + cleaning
|   +-- features.py       # feature engineering
|   +-- models.py         # model factory + CV
|   +-- utils.py          # haversine, time parsing, plot helpers
+-- reports/
|   +-- eda_2pm.pdf       # P3 -- SUBMITTED AT 14:00
|   +-- pitch_6pm.pdf     # P3 -- for final pitch
|   +-- figures/          # PNGs P2 saves here
+-- submissions/          # kaggle-style CSV outputs
+-- requirements.txt
+-- .gitignore
+-- README.md
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
