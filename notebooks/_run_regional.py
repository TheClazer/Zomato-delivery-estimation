"""Regional classification end-to-end runner.

Produces:
  - reports/figures/fig_reg_*.png            (11 EDA plots + 2 SHAP plots + AUC bar)
  - reports/regional_findings.json           (per-test stat, p, effect, verdict)
  - reports/regional_models.json             (per-fold AUC/F1/acc for Model A & B)
  - reports/regional_city_check.json         (city-code → centroid km-off table)
  - models/region_classifier_v1.txt          (Model B booster, behaviour-only)
"""
from __future__ import annotations
import os, sys, json, warnings
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import lightgbm as lgb
import shap
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (roc_auc_score, f1_score, balanced_accuracy_score,
                             confusion_matrix, accuracy_score)

from src.data import load_clean
from src.features import build_modeling_frame, add_features
from src.regional import annotate_region, coord_consistency_check

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.0)
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 160
plt.rcParams["savefig.bbox"] = "tight"

TEAL = "#0D9488"
NAVY = "#0A1F33"
GOLD = "#F59E0B"
GREY = "#94A3B8"

# =====================================================================
# 1. LOAD + LABEL
# =====================================================================
print("=" * 60); print("STEP 1: load + label"); print("=" * 60)
df = load_clean("data/raw/Zomato Dataset.csv")
df = annotate_region(df)
print(f"Rows: {len(df):,}  ·  South: {df['is_south'].sum():,}  ·  North: {(df['is_south']==0).sum():,}")

# City consistency check, persisted for the deck
chk = coord_consistency_check(df)
chk.to_csv(ROOT / "reports" / "regional_city_check.csv", index=False)
chk_json = chk.to_dict(orient="records")
print(f"Cities verified: {chk['ok'].sum()}/{len(chk)} within 250 km of centroid")

# =====================================================================
# 2. EDA — 11 STRUCTURED TESTS, ONE PLOT EACH
# =====================================================================
print("\n" + "=" * 60); print("STEP 2: structured EDA — 11 tests"); print("=" * 60)
df_feat = add_features(df)
df_feat["region"] = df["region"].values
df_feat["is_south"] = df["is_south"].values
TARGET = "Time_taken (min)"
findings = []


def num_test(col, test_name, title, fname, ylim=None):
    """Mann-Whitney U on a numeric column, South vs North."""
    s = df_feat[df_feat["is_south"] == 1][col].dropna()
    n = df_feat[df_feat["is_south"] == 0][col].dropna()
    u, p = stats.mannwhitneyu(s, n, alternative="two-sided")
    effect = float(s.median() - n.median())
    findings.append({"id": fname, "name": test_name, "test": "Mann-Whitney U",
                     "stat": f"U={u:.0f}", "p": float(p),
                     "south_median": float(s.median()), "north_median": float(n.median()),
                     "effect_median_diff": effect,
                     "verdict": "South > North" if effect > 0 else "North > South"})
    # plot
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.violinplot(x="region", y=col, data=df_feat[df_feat["region"].isin(["North","South"])],
                   order=["North", "South"], palette={"North": GREY, "South": TEAL}, inner="quartile", ax=ax)
    ax.set_title(f"{title}\nMann-Whitney p = {p:.2e}  ·  Δ median = {effect:+.2f}")
    if ylim: ax.set_ylim(ylim)
    plt.savefig(FIG / f"{fname}.png"); plt.close()


def cat_test(col, test_name, title, fname):
    """Chi-square on a categorical column."""
    ct = pd.crosstab(df_feat[col], df_feat["region"])
    if "North" not in ct.columns or "South" not in ct.columns or ct.shape[0] < 2:
        return
    chi2, p, _, _ = stats.chi2_contingency(ct)
    # Cramér's V as effect size
    n_total = ct.sum().sum()
    v = float(np.sqrt(chi2 / (n_total * (min(ct.shape) - 1))))
    findings.append({"id": fname, "name": test_name, "test": "Chi-square",
                     "stat": f"chi2={chi2:.1f}", "p": float(p),
                     "cramers_v": v,
                     "verdict": "Different" if p < 0.05 else "Same"})
    # plot: stacked percentage bars
    pct = ct.div(ct.sum(axis=0), axis=1) * 100  # column-percentage within region
    fig, ax = plt.subplots(figsize=(9, 4.5))
    pct.T.plot(kind="bar", stacked=True, ax=ax,
               colormap="crest", edgecolor="white")
    ax.set_title(f"{title}\nChi-square p = {p:.2e}  ·  Cramér's V = {v:.3f}")
    ax.set_ylabel("% of orders in region")
    ax.legend(title=col, bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    ax.tick_params(axis="x", rotation=0)
    plt.savefig(FIG / f"{fname}.png"); plt.close()


# F1: delivery time
num_test(TARGET, "F1: Delivery time differs by region", "Delivery time (min) — North vs South", "fig_reg_01_target")
# F2: weather
cat_test("Weather_conditions", "F2: Weather distribution differs", "Weather conditions — share by region", "fig_reg_02_weather")
# F3: traffic
cat_test("Road_traffic_density", "F3: Traffic density differs", "Road traffic density — share by region", "fig_reg_03_traffic")
# F4: multiple_deliveries
num_test("multiple_deliveries", "F4: Multi-delivery norms differ", "Concurrent deliveries — North vs South", "fig_reg_04_multi")
# F5: rider age
num_test("Delivery_person_Age", "F5: Rider age skew", "Rider age — North vs South", "fig_reg_05_age")
# F6: ratings
num_test("Delivery_person_Ratings", "F6: Rider rating skew", "Rider rating — North vs South", "fig_reg_06_rating")
# F7: vehicle
cat_test("Type_of_vehicle", "F7: Vehicle preferences differ", "Vehicle type — share by region", "fig_reg_07_vehicle")
# F8: order type
cat_test("Type_of_order", "F8: Order-type mix differs", "Type of order — share by region", "fig_reg_08_ordertype")
# F9: festival
cat_test("Festival", "F9: Festival incidence differs", "Festival flag — share by region", "fig_reg_09_festival")
# F10: order_hour distribution (KS test)
s_hours = df_feat[df_feat["is_south"]==1]["order_hour"].dropna()
n_hours = df_feat[df_feat["is_south"]==0]["order_hour"].dropna()
ks_stat, ks_p = stats.ks_2samp(s_hours, n_hours)
findings.append({"id":"fig_reg_10_hour","name":"F10: Time-of-day rhythm",
                 "test":"KS 2-sample","stat":f"D={ks_stat:.3f}","p":float(ks_p),
                 "verdict":"Different" if ks_p < 0.05 else "Same"})
fig, ax = plt.subplots(figsize=(9, 4.5))
for label, data, c in [("North", n_hours, GREY), ("South", s_hours, TEAL)]:
    sns.histplot(data, bins=24, stat="probability", ax=ax, color=c, alpha=0.5,
                 label=label, element="step", linewidth=2)
ax.set_title(f"Order hour distribution — KS p = {ks_p:.2e}  ·  D = {ks_stat:.3f}")
ax.set_xlabel("Hour of day (order placed)"); ax.legend()
plt.savefig(FIG / "fig_reg_10_hour.png"); plt.close()
# F11: city tier (Metropolitan/Urban/Semi)
cat_test("City", "F11: City-tier mix differs", "City tier — share by region", "fig_reg_11_citytier")

print(f"\n{len(findings)} tests complete")
for f in findings:
    print(f"  {f['id']:25s}  p={f['p']:.2e}  ·  {f['verdict']}")

# =====================================================================
# 3. MODEL A — geo baseline (lat/lon + distance)  —  upper bound
# =====================================================================
print("\n" + "=" * 60); print("STEP 3: Model A (GEO baseline)"); print("=" * 60)
df_feat["distance_km"] = df_feat.get("distance_km", np.nan)
geo_features = ["Restaurant_latitude", "Restaurant_longitude",
                "Delivery_location_latitude", "Delivery_location_longitude",
                "distance_km"]
mask = df_feat[geo_features].notna().all(axis=1) & df_feat["region"].isin(["North","South"])
X_geo = df_feat.loc[mask, geo_features].astype(float)
y = df_feat.loc[mask, "is_south"].astype(int).values

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
a_aucs, a_f1s, a_bals, a_accs = [], [], [], []
for fold, (tr, va) in enumerate(skf.split(X_geo, y), 1):
    m = lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                            random_state=42, n_jobs=-1, verbose=-1, class_weight="balanced")
    m.fit(X_geo.iloc[tr], y[tr], eval_set=[(X_geo.iloc[va], y[va])],
          callbacks=[lgb.early_stopping(30, verbose=False)])
    p = m.predict_proba(X_geo.iloc[va])[:, 1]
    pred = (p >= 0.5).astype(int)
    a_aucs.append(roc_auc_score(y[va], p))
    a_f1s.append(f1_score(y[va], pred))
    a_bals.append(balanced_accuracy_score(y[va], pred))
    a_accs.append(accuracy_score(y[va], pred))
    print(f"  Fold {fold}: AUC={a_aucs[-1]:.4f}  F1={a_f1s[-1]:.3f}  balAcc={a_bals[-1]:.3f}")
print(f"  GEO mean AUC = {np.mean(a_aucs):.4f} ± {np.std(a_aucs):.4f}")

# =====================================================================
# 4. MODEL B — behaviour only (NO coords, NO distance, NO city_code/state)
# =====================================================================
print("\n" + "=" * 60); print("STEP 4: Model B (BEHAVIOUR-only)"); print("=" * 60)
behaviour_numeric = ["prep_time_min", "order_hour", "is_peak_lunch", "is_peak_dinner",
                     "is_late_night", "is_weekend", "day_of_week", "month",
                     "Delivery_person_Age", "Delivery_person_Ratings",
                     "Vehicle_condition", "multiple_deliveries"]
behaviour_cat = ["Weather_conditions", "Road_traffic_density",
                 "Type_of_vehicle", "Type_of_order", "City", "Festival"]

mask_b = df_feat["region"].isin(["North", "South"])
Xb = df_feat.loc[mask_b, behaviour_numeric + behaviour_cat].copy()
for c in behaviour_cat:
    Xb[c] = Xb[c].astype("category")
yb = df_feat.loc[mask_b, "is_south"].astype(int).values

b_aucs, b_f1s, b_bals, b_accs = [], [], [], []
oof_b = np.zeros(len(yb))
last_model = None
for fold, (tr, va) in enumerate(skf.split(Xb, yb), 1):
    m = lgb.LGBMClassifier(n_estimators=800, learning_rate=0.04, num_leaves=63,
                            min_child_samples=20, feature_fraction=0.9,
                            bagging_fraction=0.9, bagging_freq=5,
                            random_state=42, n_jobs=-1, verbose=-1,
                            class_weight="balanced")
    m.fit(Xb.iloc[tr], yb[tr], categorical_feature=behaviour_cat,
          eval_set=[(Xb.iloc[va], yb[va])],
          callbacks=[lgb.early_stopping(40, verbose=False)])
    p = m.predict_proba(Xb.iloc[va])[:, 1]
    oof_b[va] = p
    pred = (p >= 0.5).astype(int)
    b_aucs.append(roc_auc_score(yb[va], p))
    b_f1s.append(f1_score(yb[va], pred))
    b_bals.append(balanced_accuracy_score(yb[va], pred))
    b_accs.append(accuracy_score(yb[va], pred))
    print(f"  Fold {fold}: AUC={b_aucs[-1]:.4f}  F1={b_f1s[-1]:.3f}  balAcc={b_bals[-1]:.3f}")
    if fold == 5:
        last_model = m
print(f"  BEHAVIOUR mean AUC = {np.mean(b_aucs):.4f} ± {np.std(b_aucs):.4f}")
last_model.booster_.save_model(str(ROOT / "models" / "region_classifier_v1.txt"))

# OOF confusion matrix at 0.5 threshold
oof_pred = (oof_b >= 0.5).astype(int)
cm = confusion_matrix(yb, oof_pred)
print(f"  OOF confusion: TN={cm[0,0]} FP={cm[0,1]} FN={cm[1,0]} TP={cm[1,1]}")

# =====================================================================
# 5. SHAP on Model B
# =====================================================================
print("\n" + "=" * 60); print("STEP 5: SHAP on Model B"); print("=" * 60)
X_sample = Xb.sample(min(1500, len(Xb)), random_state=42)
expl = shap.TreeExplainer(last_model.booster_)
sv = expl.shap_values(X_sample)
# LGBM binary returns a single matrix (logits for positive class) in shap 0.51
if isinstance(sv, list):
    sv = sv[1]
plt.figure()
shap.summary_plot(sv, X_sample, show=False, plot_type="bar")
plt.savefig(FIG / "fig_reg_shap_bar.png", bbox_inches="tight"); plt.close()
plt.figure()
shap.summary_plot(sv, X_sample, show=False)
plt.savefig(FIG / "fig_reg_shap_beeswarm.png", bbox_inches="tight"); plt.close()
imp = pd.Series(np.abs(sv).mean(axis=0), index=X_sample.columns).sort_values(ascending=False)
print("Top behavioural drivers of region:")
print(imp.head(10).to_string())

# =====================================================================
# 6. AUC comparison plot
# =====================================================================
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(5)
ax.bar(x - 0.18, a_aucs, width=0.36, label=f"Model A — GEO  (mean {np.mean(a_aucs):.3f})", color=GREY)
ax.bar(x + 0.18, b_aucs, width=0.36, label=f"Model B — BEHAVIOUR  (mean {np.mean(b_aucs):.3f})", color=TEAL)
ax.set_xticks(x); ax.set_xticklabels([f"Fold {i+1}" for i in range(5)])
ax.set_ylabel("ROC-AUC")
ax.set_title("Region classification — geo vs behaviour-only")
ax.set_ylim(0.5, 1.02)
ax.legend(loc="lower right")
ax.axhline(0.5, color="black", linestyle=":", alpha=0.3)
for i, v in enumerate(a_aucs): ax.text(i - 0.18, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
for i, v in enumerate(b_aucs): ax.text(i + 0.18, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
plt.savefig(FIG / "fig_reg_auc_compare.png"); plt.close()

# Confusion matrix heatmap
fig, ax = plt.subplots(figsize=(5.5, 4.5))
sns.heatmap(cm, annot=True, fmt="d", cmap="crest", ax=ax,
            xticklabels=["Pred North", "Pred South"],
            yticklabels=["True North", "True South"])
ax.set_title(f"Behaviour-only OOF confusion @ thr=0.5\n"
             f"AUC={np.mean(b_aucs):.3f}  ·  F1={np.mean(b_f1s):.3f}  ·  balAcc={np.mean(b_bals):.3f}")
plt.savefig(FIG / "fig_reg_confusion.png"); plt.close()

# =====================================================================
# 7. SAVE JSONS
# =====================================================================
out = {
    "n_rows": int(len(df)),
    "n_south": int(df["is_south"].sum()),
    "n_north": int((df["is_south"] == 0).sum()),
    "findings": findings,
    "city_check": chk_json,
    "model_geo": {
        "features": geo_features,
        "fold_auc": [float(x) for x in a_aucs],
        "fold_f1":  [float(x) for x in a_f1s],
        "fold_bal_acc": [float(x) for x in a_bals],
        "fold_acc": [float(x) for x in a_accs],
        "mean_auc": float(np.mean(a_aucs)),
        "mean_f1": float(np.mean(a_f1s)),
        "mean_bal_acc": float(np.mean(a_bals)),
    },
    "model_behaviour": {
        "features": behaviour_numeric + behaviour_cat,
        "fold_auc": [float(x) for x in b_aucs],
        "fold_f1":  [float(x) for x in b_f1s],
        "fold_bal_acc": [float(x) for x in b_bals],
        "fold_acc": [float(x) for x in b_accs],
        "mean_auc": float(np.mean(b_aucs)),
        "mean_f1": float(np.mean(b_f1s)),
        "mean_bal_acc": float(np.mean(b_bals)),
        "confusion_matrix": cm.tolist(),
        "top_shap_features": imp.head(10).round(4).to_dict(),
    },
    "auc_gap": float(np.mean(a_aucs) - np.mean(b_aucs)),
}
with open(ROOT / "reports" / "regional_findings.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\nSaved: reports/regional_findings.json")
print(f"      reports/regional_city_check.csv")
print(f"      models/region_classifier_v1.txt")
print(f"      11 EDA plots + 4 model plots in reports/figures/")
print(f"\nHEADLINE:")
print(f"  Model A (GEO)        AUC = {np.mean(a_aucs):.4f}")
print(f"  Model B (BEHAVIOUR)  AUC = {np.mean(b_aucs):.4f}")
print(f"  Gap                       = {np.mean(a_aucs)-np.mean(b_aucs):.4f}")
