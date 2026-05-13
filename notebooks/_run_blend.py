"""CatBoost 5-fold + weighted blend with tuned LightGBM. Produces:
  - reports/scores_v1_blend.json
"""
import json, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error
from src.features import build_modeling_frame

df = pd.read_parquet("data/processed/train.parquet")
X, y, cat_cols = build_modeling_frame(df)

# CatBoost needs categorical features as strings (no NaN allowed in cat cols)
Xc = X.copy()
for c in cat_cols:
    Xc[c] = Xc[c].astype("object").fillna("missing").astype(str)

oof_lgbm = np.load("data/processed/oof_lgbm_v1.npy")
print(f"Loaded LGBM OOF: {oof_lgbm.shape}, MAE={mean_absolute_error(y, oof_lgbm):.4f}")

kf = KFold(n_splits=5, shuffle=True, random_state=42)
cb_maes = []
oof_cb = np.zeros(len(y))

for fold, (tr, va) in enumerate(kf.split(Xc), 1):
    train_pool = Pool(Xc.iloc[tr], y.iloc[tr], cat_features=cat_cols)
    valid_pool = Pool(Xc.iloc[va], y.iloc[va], cat_features=cat_cols)
    m = CatBoostRegressor(
        iterations=1500, depth=8, learning_rate=0.05,
        loss_function="MAE", eval_metric="MAE",
        random_seed=42, early_stopping_rounds=50, verbose=False,
    )
    m.fit(train_pool, eval_set=valid_pool, use_best_model=True)
    p = m.predict(Xc.iloc[va])
    oof_cb[va] = p
    mae = mean_absolute_error(y.iloc[va], p)
    cb_maes.append(mae)
    print(f"CatBoost fold {fold} MAE = {mae:.3f}  (best_iter={m.best_iteration_})")

print(f"\nCatBoost mean MAE = {np.mean(cb_maes):.3f} ± {np.std(cb_maes):.3f}")

# Weighted blend on same 5-fold split (so OOF indices align)
w_lgbm, w_cb = 0.55, 0.45
oof_blend = w_lgbm * oof_lgbm + w_cb * oof_cb

# Per-fold blend MAE on same split
blend_fold_maes = []
for tr, va in kf.split(Xc):
    blend_fold_maes.append(mean_absolute_error(y.iloc[va], oof_blend[va]))

lgbm_mean = float(mean_absolute_error(y, oof_lgbm))
cb_mean = float(np.mean(cb_maes))
blend_mean = float(np.mean(blend_fold_maes))

print(f"\nLGBM tuned (OOF)  MAE = {lgbm_mean:.4f}")
print(f"CatBoost          MAE = {cb_mean:.4f}")
print(f"Blend 0.55/0.45   MAE = {blend_mean:.4f}")

if blend_mean < lgbm_mean:
    verdict = f"Blend BEATS LGBM by {lgbm_mean - blend_mean:.4f} MAE"
else:
    verdict = f"Blend DOES NOT beat LGBM (worse by {blend_mean - lgbm_mean:.4f} MAE)"
print(verdict)

with open("reports/scores_v1_blend.json", "w") as f:
    json.dump({
        "weights": {"lgbm": w_lgbm, "catboost": w_cb},
        "lgbm_oof_mae": lgbm_mean,
        "catboost_fold_mae": [float(x) for x in cb_maes],
        "catboost_mean_mae": cb_mean,
        "blend_fold_mae": [float(x) for x in blend_fold_maes],
        "blend_mean_mae": blend_mean,
        "blend_std_mae": float(np.std(blend_fold_maes)),
        "beats_lgbm": bool(blend_mean < lgbm_mean),
        "improvement_over_lgbm": float(lgbm_mean - blend_mean),
    }, f, indent=2)
print("Saved reports/scores_v1_blend.json")
