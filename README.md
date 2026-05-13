# Zomato Delivery Time Estimation — DataVerse 2026

[![CV MAE](https://img.shields.io/badge/CV%20MAE-3.04%20min-2dd4bf?style=flat-square)](reports/scores_v1_blend.json)
[![Model](https://img.shields.io/badge/model-LightGBM%20%2B%20CatBoost%20blend-0d9488?style=flat-square)](models/lgbm_v1.txt)
[![Reproducible](https://img.shields.io/badge/seed-42%20everywhere-1e40af?style=flat-square)](#reproducibility)

A 10-hour hackathon sprint to predict `Time_taken (min)` for food deliveries. Final cross-validated MAE: **3.04 min** (0.55 LightGBM + 0.45 CatBoost blend, 5-fold KFold, seed 42).

---

## TL;DR — the numbers

| Stage | Mean MAE (min) | Std | RMSE | R² |
|---|---:|---:|---:|---:|
| Baseline LightGBM | 3.057 | 0.016 | 3.83 | 0.833 |
| Optuna-tuned LightGBM (60 trials, 5-min cap) | **3.053** | 0.018 | — | — |
| CatBoost (depth 8, 1500 iters, early-stop@50) | 3.088 | 0.019 | — | — |
| **Blend (0.55 LGBM + 0.45 CatBoost)** | **3.043** | 0.018 | — | — |
| Post-pivot v2 | _filled at 15:00 by `_run_pivot.py`_ | | | |

All scores are honest 5-fold OOF on the same `KFold(shuffle=True, random_state=42)` split.

---

## Pipeline architecture

```
data/raw/Zomato Dataset.csv
        │
        ▼  src/data.py::load_clean
   • strip whitespace, normalise "NaN" / "conditions " / dirty target
   • coerce numerics, parse Order_Date (dayfirst)
   • drop zero-island coordinates
   • cap impossible ratings (>5 → NaN)
        │
data/processed/train.parquet  ──►  notebooks/01_eda.ipynb (figs 01–09)
        │
        ▼  src/features.py::build_modeling_frame
   • haversine distance (>30 km → NaN, no row loss)
   • prep_time (midnight-safe)
   • order_hour, peak/late-night/weekend flags
   • 13 numeric + 6 categorical (passed natively to LGBM/CatBoost)
        │
        ▼  notebooks/_run_tuned.py
   • Optuna 60-trial TPE on 3-fold inner CV (5-min wallclock cap)
   • Refit 5-fold KFold(seed=42)  →  models/lgbm_v1.txt
        │
        ▼  notebooks/_run_blend.py
   • CatBoost on same 5-fold split  →  weighted blend
   • Saves OOF preds for downstream stacking
        │
        ▼  notebooks/_run_pivot.py  (auto-runs at 15:00 when files drop)
   • Auto-detect join key, build ≤3 features, retrain
   • models/lgbm_final.txt + reports/delta.json
```

---

## Repo layout

```text
.
├── .gitattributes          ← keeps model files as binary across OS
├── .gitignore              ← .venv, data/raw, *.pkl, catboost_info, etc.
├── data/
│   ├── raw/                ← Zomato Dataset.csv (gitignored)
│   ├── processed/          ← train.parquet, train_v2.parquet, oof_*.npy
│   └── pivot/              ← drop the 15:00 files here
├── notebooks/
│   ├── 01_eda.ipynb               # P2 — EDA, figs 01–09
│   ├── 03_baseline.ipynb          # P1 — baseline LGBM 5-fold
│   ├── 04_tuned.ipynb             # P1 — Optuna + CatBoost + blend
│   ├── 05_pivot.ipynb             # P1 — pivot merge harness (auto)
│   ├── 06_interpretability.ipynb  # P2 — SHAP (figs 10–11)
│   └── _run_*.py                  # canonical runners; cron/CI friendly
├── src/
│   ├── data.py             # load_clean
│   ├── features.py         # haversine, prep_time, build_modeling_frame
│   ├── models.py           # (placeholder for stacking work)
│   └── utils.py            # (placeholder)
├── reports/
│   ├── figures/            # fig01_target_dist.png … fig12_delta_bars.png
│   ├── scores_v1.json      # baseline 5-fold metrics
│   ├── scores_v1_tuned.json
│   ├── scores_v1_blend.json
│   ├── scores_v2.json      ← produced by _run_pivot.py
│   ├── delta.json          ← v1 vs v2 with ship/no-ship verdict
│   ├── eda_summary.json    # numbers consumed by the deck builder
│   ├── shap_top.json
│   ├── eda_2pm.{pptx,pdf}  # 14:00 submission deck
│   └── pitch_6pm.{pptx,pdf}# 18:00 pitch deck
├── models/
│   ├── lgbm_v1.txt         # tuned LGBM (fold-5 booster, 2.2 MB)
│   └── lgbm_final.txt      ← produced by _run_pivot.py
├── submissions/            # Kaggle-style CSV outputs (if produced)
└── requirements.txt
```

---

## How to reproduce end-to-end

```bash
python -m venv .venv
.venv\Scripts\activate                            # Windows
pip install -r requirements.txt

# 1. clean raw CSV → parquet
python src/data.py

# 2. EDA (figs 01–09 + reports/eda_summary.json)
python notebooks/_run_eda.py

# 3. Tuned LightGBM (model + tuned scores + OOF preds)
python notebooks/_run_tuned.py

# 4. CatBoost + blend
python notebooks/_run_blend.py

# 5. SHAP interpretability (figs 10–11)
python notebooks/_run_shap.py

# 6. (15:00) drop pivot files in data/pivot/ then:
python notebooks/_run_pivot.py

# 7. Build the decks
python notebooks/_build_decks.py     # writes reports/eda_2pm.pptx + pitch_6pm.pptx
python notebooks/_pptx_to_pdf.py     # converts to PDF via PowerPoint COM (Windows)
```

Total cold-start runtime: ~12 minutes on a laptop CPU (no GPU).

---

## Key methodology decisions (the "explain every line" defense)

The hackathon rulebook §6 requires we can explain every line. Here are the load-bearing choices:

1. **Target column has a space** — the CSV ships `"Time_taken (min)"` with a space before the parenthesis, not `"Time_taken(min)"`. We use the exact name and document it in [src/data.py](src/data.py).
2. **Distance >30 km → NaN, not dropped.** Food delivery >30 km is physically implausible (data entry error), but the rider age, traffic, weather etc. on those rows are typically clean. NaN preserves the partial signal — LightGBM handles missing values natively. ~1% of rows are affected.
3. **`add_features` is idempotent.** `df.copy()` at the top + only assignments via `df[col] = ...` means it can be called twice without changing results. The blend runner relies on this.
4. **5-fold KFold seed=42 is the single source of truth** for every model and OOF prediction. Same `KFold` instance → same indices → honest deltas across v1, v2, blend.
5. **CatBoost gets string-typed categoricals.** Pandas `Category` dtype with NaN is rejected by `Pool`; we cast to `object`, fill `"missing"`, then to `str`. Documented in `_run_blend.py`.
6. **Optuna has a wall-clock cap of 300 seconds** alongside `n_trials=60`. Whichever fires first ends the search — the hackathon time budget is the hard constraint, not the trial count.
7. **No target leakage.** `prep_time_min = picked_min − ordered_min` uses only order metadata available at prediction time; we verified no feature uses `Time_taken (min)` directly.
8. **`.gitattributes` marks `models/*.txt` as binary.** A previous LGBM booster file got CRLF-translated by git on Windows and broke SHAP. Won't happen again.
9. **Pivot runner is hands-off.** `_run_pivot.py` auto-detects the join key from a fixed candidate list (`Delivery_person_ID`, `Order_ID`, `ID`, `Restaurant_ID`, `City`, `Order_Date`), warns on null-rate > 80%, and writes `delta.json` with a `ship_v2: bool` verdict so we don't ship a regression.

---

## Reproducibility

| Item | Value |
|---|---|
| Random state | 42 (numpy, sklearn, LGBM, CatBoost, Optuna sampler) |
| KFold | `KFold(n_splits=5, shuffle=True, random_state=42)` |
| Python | 3.11 |
| Key versions | LightGBM 4.6, CatBoost 1.2.10, Optuna 4.8, sklearn 1.8 |
| Final tag | `final` (set at 18:00) |

---

## EDA highlights (real numbers from the data)

- **Rows × cols after cleaning:** 45,153 × 21 (the EDA notebook applies a `0.5 < distance < 50 km` filter for plot clarity)
- **Target:** 10–54 min, median 26, mean 26.3
- **Distance ↔ time:** Spearman ρ = 0.32 (moderate, not as dominant as the raw scatter suggests)
- **Traffic ANOVA:** F = 3,390, p ≪ 1e-300 (medians grow monotonically Low → Medium → High → Jam)
- **Weather:** bad (Stormy/Fog/Sandstorm) > Sunny by ~10 min median (Mann-Whitney, p ≪ 0.05)
- **Festival days:** +14 min mean vs non-festival (Welch t = 138, p ≪ 0.05)
- **Multi-deliveries:** ρ = 0.34 — each extra drop adds measurable time
- **The buried insight (SHAP):** `Road_traffic_density` is the #1 feature, ahead of `distance_km`. Distance is a strong _univariate_ signal but conditioned on traffic it becomes secondary. This is the slide that wins the data-literacy point.

---

## Risk register (the things we watched for)

| Risk | Mitigation |
|---|---|
| MAE > 5 → feature broken | Hypothesis tests at every fold; SHAP confirms direction |
| Stringified `"NaN"` survives | `_run_eda.py` and `src/data.py` both apply the replace |
| Pivot data joins to nothing | `_run_pivot.py` tries 6 candidate keys; logs null-rate; skips bad files |
| Pivot hurts performance | `delta.json` writes `"ship_v2": false` if delta ≤ 0.05 → we ship v1 |
| Git CRLF breaks model | `.gitattributes` pins `models/*.txt` to binary |
| Can't explain a line | Each runner is < 200 LOC, function-level commented |
| Push fails at 17:55 | Local tag `final`; can zip + email as fallback |

---

## Team

| Role | Owns |
|---|---|
| **P1 — Pipeline** (60%) | `src/`, model, CV, pivot merge, freeze, push |
| **P2 — EDA & Insights** (20%) | `notebooks/01_eda.ipynb`, plots, hypothesis tests, SHAP |
| **P3 — Deck & Pitch** (20%) | `reports/eda_2pm.pdf`, `reports/pitch_6pm.pdf`, pitch delivery |

Team members: **[P1 NAME] · [P2 NAME] · [P3 NAME]** (placeholders — replace before submission).

---

## License + acknowledgements

Dataset © Zomato (provided by the hackathon organisers — not redistributed). Code MIT, see [LICENSE](LICENSE) if present.

DataVerse 2026 · BMSCE. Repo: <https://github.com/TheClazer/Zomato-delivery-estimation>
