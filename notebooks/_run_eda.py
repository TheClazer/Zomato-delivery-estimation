"""P2 EDA — produces fig01..fig09 in reports/figures/ and a JSON of
hypothesis-test results used by the deck builder. Mirrors the cells in
notebooks/01_eda.ipynb so the notebook is documentation and this script
is the reproducible runner.
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_theme(style="whitegrid", palette="deep", font_scale=1.0)
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"

FIG = "reports/figures"
os.makedirs(FIG, exist_ok=True)

# ---- load + minimal clean (independent of P1's parquet, by design) ----
df = pd.read_csv("data/raw/Zomato Dataset.csv")
for c in df.select_dtypes(include="object").columns:
    df[c] = df[c].astype(str).str.strip()
    df[c] = df[c].replace({"NaN": np.nan, "nan": np.nan, "": np.nan})

df["Time_taken (min)"] = pd.to_numeric(df["Time_taken (min)"], errors="coerce")
if "Weather_conditions" in df.columns:
    df["Weather_conditions"] = (df["Weather_conditions"].astype(str)
                                  .str.replace("conditions", "", regex=False)
                                  .str.strip())
for c in ["Delivery_person_Age", "Delivery_person_Ratings",
          "Restaurant_latitude", "Restaurant_longitude",
          "Delivery_location_latitude", "Delivery_location_longitude",
          "Vehicle_condition", "multiple_deliveries"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce", dayfirst=True)
df = df.dropna(subset=["Time_taken (min)"]).reset_index(drop=True)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


df["distance_km"] = haversine_km(
    df["Restaurant_latitude"], df["Restaurant_longitude"],
    df["Delivery_location_latitude"], df["Delivery_location_longitude"],
)
df = df[df["distance_km"].between(0.5, 50)].reset_index(drop=True)
TARGET = "Time_taken (min)"
print(f"Working frame: {df.shape}")

TEAL = "#0d9488"
NAVY = "#0a1f33"

# ---- fig01 target distribution ----
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(df[TARGET], bins=40, ax=ax, color=TEAL, edgecolor="white")
mean_v, med_v = df[TARGET].mean(), df[TARGET].median()
ax.axvline(mean_v, color="black", linestyle="--", label=f"Mean {mean_v:.1f} min")
ax.axvline(med_v, color="red", linestyle=":", label=f"Median {med_v:.0f} min")
ax.set_title("Distribution of delivery time")
ax.set_xlabel("Time taken (min)"); ax.set_ylabel("Order count"); ax.legend()
plt.savefig(f"{FIG}/fig01_target_dist.png"); plt.close()

# ---- fig02 missingness ----
miss = df.isna().mean().sort_values(ascending=False)
miss = miss[miss > 0]
fig, ax = plt.subplots(figsize=(9, 5))
miss.plot(kind="barh", ax=ax, color=TEAL)
ax.set_title("Missingness by column"); ax.set_xlabel("Fraction missing")
ax.invert_yaxis()
plt.savefig(f"{FIG}/fig02_missingness.png"); plt.close()

# ---- fig03 outliers (4-panel) ----
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
sns.boxplot(y=df["Delivery_person_Age"], ax=axes[0, 0], color=TEAL); axes[0, 0].set_title("Rider age")
sns.boxplot(y=df["Delivery_person_Ratings"], ax=axes[0, 1], color=TEAL); axes[0, 1].set_title("Rider rating")
sns.boxplot(y=df["distance_km"], ax=axes[1, 0], color=TEAL); axes[1, 0].set_title("Distance (km)")
sns.boxplot(y=df["multiple_deliveries"], ax=axes[1, 1], color=TEAL); axes[1, 1].set_title("Multiple deliveries")
plt.tight_layout(); plt.savefig(f"{FIG}/fig03_outliers.png"); plt.close()

# ---- fig04 categoricals ----
fig, axes = plt.subplots(2, 2, figsize=(11, 7))
for ax, col in zip(axes.flat,
                   ["Weather_conditions", "Road_traffic_density", "Type_of_vehicle", "City"]):
    if col in df.columns:
        order = df[col].value_counts().index
        sns.countplot(x=col, data=df, order=order, ax=ax, color=TEAL)
        ax.set_title(col); ax.tick_params(axis="x", rotation=30)
plt.tight_layout(); plt.savefig(f"{FIG}/fig04_categoricals.png"); plt.close()

# ---- fig05 distance vs time (the money plot) ----
samp = df.sample(min(8000, len(df)), random_state=42)
fig, ax = plt.subplots(figsize=(9, 6))
sns.scatterplot(x="distance_km", y=TARGET, data=samp,
                alpha=0.25, s=10, ax=ax, color=TEAL)
sns.regplot(x="distance_km", y=TARGET, data=samp,
            scatter=False, ax=ax, color="#1e40af")
rho_dist, _ = stats.spearmanr(samp["distance_km"], samp[TARGET])
ax.set_title(f"Delivery time vs distance  (Spearman ρ = {rho_dist:.2f})")
ax.set_xlabel("Distance (km)"); ax.set_ylabel("Time taken (min)")
plt.savefig(f"{FIG}/fig05_dist_vs_time.png"); plt.close()

# ---- fig06 traffic vs time ----
order_t = ["Low", "Medium", "High", "Jam"]
present = [t for t in order_t if t in df["Road_traffic_density"].dropna().unique()]
fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(x="Road_traffic_density", y=TARGET, data=df,
            order=present, ax=ax, palette="crest")
ax.set_title("Delivery time by road traffic density")
plt.savefig(f"{FIG}/fig06_traffic.png"); plt.close()

# ---- fig07 weather vs time ----
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(x="Weather_conditions", y=TARGET, data=df, ax=ax, palette="crest")
ax.set_title("Delivery time by weather"); ax.tick_params(axis="x", rotation=20)
plt.savefig(f"{FIG}/fig07_weather.png"); plt.close()

# ---- fig08 multi-deliveries vs time ----
fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(x="multiple_deliveries", y=TARGET, data=df, ax=ax, color=TEAL)
ax.set_title("Time taken by number of multi-deliveries on the run")
plt.savefig(f"{FIG}/fig08_multi_deliveries.png"); plt.close()

# ---- hypothesis tests ----
results = []
rho1, p1 = stats.spearmanr(df["distance_km"], df[TARGET])
results.append(("H1: distance ↔ time (Spearman)", f"ρ={rho1:.3f}", f"p={p1:.2e}",
                "Strong positive" if rho1 > 0.4 else "Weak"))

groups = [g[TARGET].dropna().values for _, g in df.groupby("Road_traffic_density") if len(g) > 30]
f_stat, p2 = stats.f_oneway(*groups)
results.append(("H2: traffic groups (ANOVA)", f"F={f_stat:.1f}", f"p={p2:.2e}",
                "Different" if p2 < 0.05 else "Same"))

bad = df[df["Weather_conditions"].isin(["Stormy", "Sandstorms", "Fog"])][TARGET]
good = df[df["Weather_conditions"] == "Sunny"][TARGET]
u, p3 = stats.mannwhitneyu(bad, good, alternative="greater")
weather_delta = bad.median() - good.median()
results.append(("H3: bad weather > sunny (M-W)", f"U={u:.0f}", f"p={p3:.2e}",
                "Yes" if p3 < 0.05 else "No"))

fes = df[df["Festival"] == "Yes"][TARGET]
nof = df[df["Festival"] == "No"][TARGET]
t_stat, p4 = stats.ttest_ind(fes, nof, equal_var=False)
festival_delta = fes.mean() - nof.mean()
results.append(("H4: festival > non-festival (Welch)", f"t={t_stat:.2f}", f"p={p4:.2e}",
                "Yes" if (p4 < 0.05 and t_stat > 0) else "No"))

rho5, p5 = stats.spearmanr(df["multiple_deliveries"].fillna(0), df[TARGET])
results.append(("H5: multi-deliveries ↔ time (Spearman)", f"ρ={rho5:.3f}",
                f"p={p5:.2e}", "Yes" if rho5 > 0.2 else "Weak"))

res_df = pd.DataFrame(results, columns=["Hypothesis", "Statistic", "p", "Verdict"])
print(res_df.to_string(index=False))

# ---- fig09 hypothesis table image ----
fig, ax = plt.subplots(figsize=(11, 3.5))
ax.axis("off")
tbl = ax.table(cellText=res_df.values, colLabels=res_df.columns,
               loc="center", cellLoc="left")
tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1, 1.6)
for i in range(len(res_df.columns)):
    tbl[(0, i)].set_facecolor(TEAL)
    tbl[(0, i)].set_text_props(color="white", weight="bold")
plt.savefig(f"{FIG}/fig09_hypotheses_table.png", bbox_inches="tight", dpi=180)
plt.close()

# ---- summary stats for the deck builder ----
summary = {
    "n_rows": int(len(df)),
    "n_cols": int(df.shape[1]),
    "target_min": float(df[TARGET].min()),
    "target_max": float(df[TARGET].max()),
    "target_mean": float(mean_v),
    "target_median": float(med_v),
    "top_missing": miss.head(3).to_dict(),
    "spearman_distance_time": float(rho_dist),
    "weather_delta_median_min": float(weather_delta),
    "festival_delta_mean_min": float(festival_delta),
    "rho_multi_deliveries": float(rho5),
    "hypotheses": [
        {"name": h, "stat": s, "p": p, "verdict": v} for h, s, p, v in results
    ],
}
with open("reports/eda_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSaved reports/eda_summary.json")
print("Figures:", sorted(os.listdir(FIG)))
