"""Runner script that mirrors notebooks/04_tuned.ipynb. Produces:
  - reports/scores_v1_tuned.json
  - models/lgbm_v1.txt
  - data/processed/oof_lgbm_v1.npy   (used by blend step)
"""
import json, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error
from src.features import build_modeling_frame

optuna.logging.set_verbosity(optuna.logging.WARNING)

df = pd.read_parquet("data/processed/train.parquet")
X, y, cat_cols = build_modeling_frame(df)
print(f"X={X.shape}  y={y.shape}  cats={len(cat_cols)}")


def objective(trial):
    params = {
        "n_estimators": 800,
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.08, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 31, 127),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 60),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.7, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.7, 1.0),
        "bagging_freq": 5,
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 1.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 1.0, log=True),
        "random_state": 42, "n_jobs": -1, "verbose": -1,
    }
    kf = KFold(n_splits=3, shuffle=True, random_state=42)
    maes = []
    for tr, va in kf.split(X):
        m = lgb.LGBMRegressor(**params)
        m.fit(X.iloc[tr], y.iloc[tr], categorical_feature=cat_cols,
              eval_set=[(X.iloc[va], y.iloc[va])],
              callbacks=[lgb.early_stopping(40, verbose=False)])
        maes.append(mean_absolute_error(y.iloc[va], m.predict(X.iloc[va])))
    return float(np.mean(maes))


study = optuna.create_study(direction="minimize",
                            sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=60, timeout=300, show_progress_bar=False)
print(f"Optuna done. trials={len(study.trials)}  best_3fold_MAE={study.best_value:.4f}")
print("Best params:", study.best_params)

best = dict(study.best_params)
best.update(dict(n_estimators=1200, bagging_freq=5,
                 random_state=42, n_jobs=-1, verbose=-1))

kf = KFold(n_splits=5, shuffle=True, random_state=42)
maes = []
oof = np.zeros(len(y))
final_model = None
for fold, (tr, va) in enumerate(kf.split(X), 1):
    m = lgb.LGBMRegressor(**best)
    m.fit(X.iloc[tr], y.iloc[tr], categorical_feature=cat_cols,
          eval_set=[(X.iloc[va], y.iloc[va])],
          callbacks=[lgb.early_stopping(50, verbose=False)])
    p = m.predict(X.iloc[va])
    oof[va] = p
    mae = mean_absolute_error(y.iloc[va], p)
    maes.append(mae)
    print(f"Fold {fold} MAE = {mae:.3f}")
    if fold == 5:
        final_model = m

print(f"\nTuned mean MAE = {np.mean(maes):.3f} ± {np.std(maes):.3f}")

with open("reports/scores_v1_tuned.json", "w") as f:
    json.dump({
        "fold_mae": [float(x) for x in maes],
        "mae_mean": float(np.mean(maes)),
        "mae_std":  float(np.std(maes)),
        "best_params": best,
    }, f, indent=2)

final_model.booster_.save_model("models/lgbm_v1.txt")
np.save("data/processed/oof_lgbm_v1.npy", oof)
print("Saved scores + model + OOF preds")
