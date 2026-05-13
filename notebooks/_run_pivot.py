"""P1-7/8/9 — Pivot merge runner. Designed to run **as soon as** files land
in data/pivot/. Auto-detects the join key from the columns of each file,
merges, builds 3 new features depending on what's available, retrains the
tuned LGBM v1 with the same KFold seed, and writes:
  - data/processed/train_v2.parquet
  - reports/scores_v2.json
  - reports/delta.json
  - models/lgbm_final.txt   (with binary-safe save)
"""
from __future__ import annotations
import os, sys, json, glob
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error
from src.features import build_modeling_frame, NUMERIC_FEATURES, CATEGORICAL_FEATURES, add_features

ROOT = Path(__file__).resolve().parent.parent
PIVOT_DIR = ROOT / "data" / "pivot"

# ---------- 1. load pivot files ----------
pivot_files = sorted([p for p in PIVOT_DIR.iterdir()
                      if p.suffix.lower() in (".csv", ".parquet") and p.name != ".gitkeep"])
if not pivot_files:
    print("No pivot files found in data/pivot/. Waiting on the 15:00 drop.")
    sys.exit(0)

pivots = {}
for p in pivot_files:
    pf = pd.read_csv(p) if p.suffix.lower() == ".csv" else pd.read_parquet(p)
    pivots[p.name] = pf
    print(f"=== {p.name} ===  shape={pf.shape}")
    print("columns:", pf.columns.tolist())
    print(pf.head(2).to_string(), "\n")

# ---------- 2. auto-detect the join key ----------
df = pd.read_parquet(ROOT / "data" / "processed" / "train.parquet")
train_cols = set(df.columns)

CANDIDATE_KEYS = ["Delivery_person_ID", "Order_ID", "ID",
                  "Restaurant_ID", "City", "Order_Date"]


def pick_key(pivot_df: pd.DataFrame) -> str | None:
    for k in CANDIDATE_KEYS:
        if k in pivot_df.columns and k in train_cols:
            return k
    common = list(set(pivot_df.columns) & train_cols)
    return common[0] if common else None


merged = df.copy()
join_log = []
for name, pf in pivots.items():
    key = pick_key(pf)
    if key is None:
        print(f"!! {name}: no join key found, skipping")
        continue
    before = len(merged)
    pf_unique = pf.drop_duplicates(subset=[key])
    merged = merged.merge(pf_unique, on=key, how="left", suffixes=("", f"_{name}"))
    new_cols = [c for c in merged.columns if c not in df.columns]
    null_rate = merged[new_cols].isna().mean().mean() if new_cols else 1.0
    join_log.append({"file": name, "key": key, "rows_before": before,
                     "rows_after": len(merged), "new_cols": new_cols,
                     "mean_null_rate": float(null_rate)})
    print(f"   joined {name} on '{key}': rows {before}→{len(merged)}, "
          f"new={len(new_cols)} cols, mean-null={null_rate:.1%}")

# ---------- 3. engineer up to 3 features from new columns ----------
new_cols = [c for c in merged.columns if c not in df.columns]
new_numeric, new_categorical = [], []

for c in new_cols:
    if merged[c].isna().mean() > 0.8:
        continue
    if pd.api.types.is_numeric_dtype(merged[c]):
        new_numeric.append(c)
    else:
        merged[c] = merged[c].astype("category")
        new_categorical.append(c)

# Bounded — judges should see <=3 new features on the slide
new_numeric = new_numeric[:3]
new_categorical = new_categorical[: max(0, 3 - len(new_numeric))]
pivot_features = new_numeric + new_categorical
print(f"\nPivot features kept: {pivot_features}")

merged.to_parquet(ROOT / "data" / "processed" / "train_v2.parquet")

# ---------- 4. build modeling frame with the new columns added ----------
X, y, _ = build_modeling_frame(df)  # v1 frame for delta baseline reference

X2_full = add_features(merged)
X2 = X2_full[NUMERIC_FEATURES + new_numeric + CATEGORICAL_FEATURES + new_categorical].copy()
for c in CATEGORICAL_FEATURES + new_categorical:
    X2[c] = X2[c].astype("category")
y2 = X2_full["Time_taken (min)"].astype(float)
cat2 = CATEGORICAL_FEATURES + new_categorical
print(f"v2 X shape = {X2.shape}  (v1 was {X.shape})")

# ---------- 5. retrain 5-fold with v1 best params ----------
best = json.load(open(ROOT / "reports" / "scores_v1_tuned.json"))["best_params"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)
maes = []
final_model = None
for fold, (tr, va) in enumerate(kf.split(X2), 1):
    m = lgb.LGBMRegressor(**best)
    m.fit(X2.iloc[tr], y2.iloc[tr], categorical_feature=cat2,
          eval_set=[(X2.iloc[va], y2.iloc[va])],
          callbacks=[lgb.early_stopping(50, verbose=False)])
    mae = mean_absolute_error(y2.iloc[va], m.predict(X2.iloc[va]))
    maes.append(mae)
    print(f"v2 fold {fold} MAE = {mae:.3f}")
    if fold == 5:
        final_model = m
v2_mae = float(np.mean(maes))
print(f"\nv2 mean MAE = {v2_mae:.3f} ± {np.std(maes):.3f}")

# ---------- 6. save scores + delta ----------
v1 = json.load(open(ROOT / "reports" / "scores_v1_tuned.json"))
delta_val = v1["mae_mean"] - v2_mae

with open(ROOT / "reports" / "scores_v2.json", "w") as f:
    json.dump({"fold_mae": [float(x) for x in maes],
               "mae_mean": v2_mae,
               "mae_std": float(np.std(maes)),
               "pivot_features": pivot_features,
               "join_log": join_log}, f, indent=2)

with open(ROOT / "reports" / "delta.json", "w") as f:
    json.dump({"v1_mae": v1["mae_mean"],
               "v2_mae": v2_mae,
               "delta": delta_val,
               "v1_fold_mae": v1["fold_mae"],
               "v2_fold_mae": [float(x) for x in maes],
               "new_features": pivot_features,
               "ship_v2": bool(delta_val > 0.05)}, f, indent=2)

final_model.booster_.save_model(str(ROOT / "models" / "lgbm_final.txt"))
print(f"\nSaved scores_v2.json, delta.json, models/lgbm_final.txt")
print(f"Delta MAE = {delta_val:+.3f}  (positive = improvement, ship_v2={delta_val>0.05})")
