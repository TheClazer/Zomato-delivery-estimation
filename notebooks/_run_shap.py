"""P2-6: SHAP on the tuned LGBM v1 booster. Produces fig10, fig11."""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
import lightgbm as lgb
from src.features import build_modeling_frame

FIG = "reports/figures"
os.makedirs(FIG, exist_ok=True)

df = pd.read_parquet("data/processed/train.parquet")
X, y, cat_cols = build_modeling_frame(df)

booster = lgb.Booster(model_file="models/lgbm_v1.txt")
explainer = shap.TreeExplainer(booster)
X_sample = X.sample(1500, random_state=42)
shap_values = explainer.shap_values(X_sample)

plt.figure()
shap.summary_plot(shap_values, X_sample, show=False)
plt.savefig(f"{FIG}/fig10_shap_beeswarm.png", bbox_inches="tight", dpi=180)
plt.close()

plt.figure()
shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
plt.savefig(f"{FIG}/fig11_shap_bar.png", bbox_inches="tight", dpi=180)
plt.close()

imp = pd.Series(np.abs(shap_values).mean(axis=0), index=X_sample.columns)
top10 = imp.sort_values(ascending=False).head(10)
print("Top features by SHAP:")
print(top10.to_string())

with open("reports/shap_top.json", "w") as f:
    json.dump({k: float(v) for k, v in top10.items()}, f, indent=2)
print("\nSaved reports/shap_top.json + fig10/11")
