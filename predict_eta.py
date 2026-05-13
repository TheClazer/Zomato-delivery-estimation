"""Zomato ETA predictor — beautiful CLI + interactive HTML dashboard.

Usage
-----
    python predict_eta.py                           # uses default paths, opens dashboard
    python predict_eta.py --no-open                 # don't auto-open browser
    python predict_eta.py --input X.csv             # different input CSV

Outputs
-------
    predictions_eta.csv       — per-row predicted delivery time
    reports/eta_dashboard.html — interactive Plotly dashboard
"""
from __future__ import annotations
import argparse, time, sys, json, webbrowser
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.data import load_clean
from src.features import build_modeling_frame, TARGET

# ----------------------------- colours (ANSI) -----------------------------
class C:
    R, G, B = '\033[91m', '\033[92m', '\033[94m'
    Y, M, K = '\033[93m', '\033[95m', '\033[96m'
    TEAL = '\033[38;5;43m'; GOLD = '\033[38;5;214m'
    GREY = '\033[38;5;245m'; NAVY = '\033[38;5;24m'
    BOLD = '\033[1m'; DIM = '\033[2m'; END = '\033[0m'

def banner():
    print(f"\n{C.NAVY}{C.BOLD}╔══════════════════════════════════════════════════════════════════════╗{C.END}")
    print(f"{C.NAVY}{C.BOLD}║{C.END}    {C.TEAL}{C.BOLD}ZOMATO  ETA  PREDICTOR{C.END}  {C.GREY}·  delivery-time regression{C.END}              {C.NAVY}{C.BOLD}║{C.END}")
    print(f"{C.NAVY}{C.BOLD}║{C.END}    {C.GOLD}Team Hmmmmmmmmmm  ·  DataVerse 2026  ·  BMSCE{C.END}                    {C.NAVY}{C.BOLD}║{C.END}")
    print(f"{C.NAVY}{C.BOLD}╚══════════════════════════════════════════════════════════════════════╝{C.END}\n")


def step(n, total, label, dt_ms=None):
    bar = "▓" * n + "░" * (total - n)
    extra = f"  {C.GREY}({dt_ms:.0f} ms){C.END}" if dt_ms is not None else ""
    print(f"  {C.TEAL}{bar}{C.END}  [{n}/{total}]  {C.BOLD}{label}{C.END}{extra}")


# ----------------------------- main ---------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Predict Zomato delivery time (minutes) from a CSV.")
    ap.add_argument("--input",  default="data/raw/Zomato Dataset.csv")
    ap.add_argument("--model",  default="models/lgbm_v1.txt")
    ap.add_argument("--output", default="predictions_eta.csv")
    ap.add_argument("--dashboard", default="reports/eta_dashboard.html")
    ap.add_argument("--no-open", action="store_true", help="don't auto-open the dashboard")
    args = ap.parse_args()

    banner()
    t0 = time.perf_counter()

    print(f"  {C.DIM}Input :{C.END} {args.input}")
    print(f"  {C.DIM}Model :{C.END} {args.model}")
    print()

    t = time.perf_counter()
    df_raw = load_clean(args.input)
    step(1, 5, f"Cleaned {len(df_raw):,} rows", (time.perf_counter()-t)*1000)

    t = time.perf_counter()
    X, y_true, cat_cols = build_modeling_frame(df_raw)
    step(2, 5, f"Built feature matrix  X={X.shape[0]:,}×{X.shape[1]}", (time.perf_counter()-t)*1000)

    t = time.perf_counter()
    booster = lgb.Booster(model_file=args.model)
    step(3, 5, f"Loaded model  ·  {booster.num_trees()} trees · {len(booster.feature_name())} feats",
         (time.perf_counter()-t)*1000)

    t = time.perf_counter()
    y_pred = booster.predict(X)
    step(4, 5, f"Predicted {len(y_pred):,} delivery times", (time.perf_counter()-t)*1000)

    # ---- metrics if ground truth is available
    have_truth = not np.isnan(y_true).all()
    mae = mae_p25 = mae_p75 = rmse = r2 = None
    if have_truth:
        err = np.abs(y_pred - y_true.values)
        mae = float(np.mean(err))
        mae_p25, mae_p75 = float(np.percentile(err, 25)), float(np.percentile(err, 75))
        rmse = float(np.sqrt(np.mean((y_pred - y_true.values)**2)))
        ss_res = float(np.sum((y_true.values - y_pred)**2))
        ss_tot = float(np.sum((y_true.values - y_true.mean())**2))
        r2 = 1 - ss_res / ss_tot

    # ---- write CSV
    t = time.perf_counter()
    out = df_raw.copy()
    out["predicted_minutes"] = y_pred.round(2)
    if have_truth:
        out["actual_minutes"] = y_true.values
        out["error_minutes"]  = (y_pred - y_true.values).round(2)
    out.to_csv(args.output, index=False)
    step(5, 5, f"Wrote {args.output}", (time.perf_counter()-t)*1000)

    total_ms = (time.perf_counter()-t0)*1000
    per_row_us = (total_ms*1000) / max(1, len(df_raw))

    # ---- hero banner of results
    print()
    print(f"  {C.NAVY}{C.BOLD}┌─────────────────────────────────────────────────────────────────┐{C.END}")
    if have_truth:
        print(f"  {C.NAVY}{C.BOLD}│{C.END}   {C.GOLD}{C.BOLD}MAE{C.END}        {C.BOLD}{mae:6.3f} min{C.END}    "
              f"{C.GREY}(median error from true delivery time){C.END}     {C.NAVY}{C.BOLD}│{C.END}")
        print(f"  {C.NAVY}{C.BOLD}│{C.END}   {C.TEAL}{C.BOLD}RMSE{C.END}       {C.BOLD}{rmse:6.3f} min{C.END}    "
              f"{C.GREY}(root mean squared error){C.END}                  {C.NAVY}{C.BOLD}│{C.END}")
        print(f"  {C.NAVY}{C.BOLD}│{C.END}   {C.TEAL}{C.BOLD}R²{C.END}         {C.BOLD}{r2:6.3f}{C.END}        "
              f"{C.GREY}(fraction of variance explained){C.END}           {C.NAVY}{C.BOLD}│{C.END}")
        print(f"  {C.NAVY}{C.BOLD}│{C.END}   {C.GREY}IQR of error: {mae_p25:.2f} – {mae_p75:.2f} min                                {C.NAVY}{C.BOLD}│{C.END}")
    print(f"  {C.NAVY}{C.BOLD}│{C.END}   {C.GREY}Latency  : {total_ms:.0f} ms end-to-end                                {C.NAVY}{C.BOLD}│{C.END}")
    print(f"  {C.NAVY}{C.BOLD}│{C.END}   {C.GREY}Speed    : {per_row_us:.1f} µs/row  ({1_000_000/per_row_us:,.0f} rows/sec){C.END}             {C.NAVY}{C.BOLD}│{C.END}")
    print(f"  {C.NAVY}{C.BOLD}└─────────────────────────────────────────────────────────────────┘{C.END}\n")

    # ---- sample predictions table
    sample = out.sample(min(8, len(out)), random_state=42)[
        ["ID", "Restaurant_latitude", "Restaurant_longitude", "predicted_minutes"]
        + (["actual_minutes", "error_minutes"] if have_truth else [])
    ]
    print(f"  {C.BOLD}{C.TEAL}Sample of predictions{C.END}  {C.GREY}(random 8 of {len(out):,}){C.END}")
    print(f"  {C.GREY}{'─'*92}{C.END}")
    header = "  {:<10} {:>12} {:>13} {:>15}".format("ID", "Rest. lat", "Rest. lon", "pred (min)")
    if have_truth:
        header += "{:>15}{:>15}".format("actual (min)", "error (min)")
    print(f"  {C.BOLD}{header[2:]}{C.END}")
    for _, r in sample.iterrows():
        row = "  {:<10} {:>12.4f} {:>13.4f} {:>15.2f}".format(
            str(r["ID"])[:10], r["Restaurant_latitude"], r["Restaurant_longitude"], r["predicted_minutes"])
        if have_truth:
            err_col = C.G if abs(r["error_minutes"]) < 3 else (C.Y if abs(r["error_minutes"]) < 6 else C.R)
            row += "{:>15.1f}".format(r["actual_minutes"]) + f"{err_col}{r['error_minutes']:>14.2f}{C.END}"
        print(row)
    print()

    # ---- dashboard
    print(f"  {C.GOLD}{C.BOLD}▶ Building interactive dashboard…{C.END}")
    build_dashboard(df_raw, y_true, y_pred, mae, rmse, r2, booster, args.dashboard, have_truth)
    print(f"  {C.G}{C.BOLD}✓{C.END}  {C.BOLD}Dashboard saved:{C.END}  {args.dashboard}")
    print(f"  {C.G}{C.BOLD}✓{C.END}  {C.BOLD}Predictions CSV:{C.END} {args.output}")
    print(f"  {C.G}{C.BOLD}✓{C.END}  {C.BOLD}Model file:{C.END}      {args.model}  ({Path(args.model).stat().st_size:,} bytes)")
    print()

    if not args.no_open:
        url = "file:///" + str(Path(args.dashboard).resolve()).replace("\\", "/")
        print(f"  {C.TEAL}Opening in browser…{C.END}  {C.DIM}{url}{C.END}\n")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"  {C.Y}Couldn't auto-open ({e}). Open the HTML manually.{C.END}\n")


# ----------------------------- dashboard ---------------------------------
def build_dashboard(df, y_true, y_pred, mae, rmse, r2, booster, out_path, have_truth):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    NAVY  = "#0A1F33"; TEAL = "#0D9488"; TEAL_L = "#2DD4BF"
    GOLD  = "#F59E0B"; GREY = "#94A3B8"

    # ---- subplots: 2x2
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Predicted vs Actual delivery time",
            "Distribution of predictions (vs actual)",
            "Error distribution  (predicted − actual)",
            "Top-15 feature importance (LightGBM gain)",
        ),
        specs=[[{"type":"scatter"},{"type":"histogram"}],
               [{"type":"histogram"},{"type":"bar"}]],
        vertical_spacing=0.14, horizontal_spacing=0.10,
    )

    # 1. scatter pred vs actual
    if have_truth:
        sample_idx = np.random.RandomState(42).choice(len(y_pred), size=min(4000, len(y_pred)), replace=False)
        fig.add_trace(go.Scatter(
            x=y_true.values[sample_idx], y=y_pred[sample_idx], mode="markers",
            marker=dict(size=4, color=TEAL, opacity=0.35),
            name="Orders",
            hovertemplate="Actual: %{x:.1f} min<br>Predicted: %{y:.1f} min<extra></extra>"),
            row=1, col=1)
        mx = max(y_true.max(), y_pred.max()) * 1.05
        fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines",
                                  line=dict(color=GOLD, dash="dash", width=2),
                                  name="Perfect prediction y=x"), row=1, col=1)
    else:
        fig.add_annotation(text="No ground truth available", row=1, col=1, showarrow=False)

    # 2. distribution overlap
    fig.add_trace(go.Histogram(x=y_pred, nbinsx=40, name="Predicted",
                                marker_color=TEAL, opacity=0.65), row=1, col=2)
    if have_truth:
        fig.add_trace(go.Histogram(x=y_true.values, nbinsx=40, name="Actual",
                                    marker_color=GOLD, opacity=0.55), row=1, col=2)

    # 3. error histogram
    if have_truth:
        err = y_pred - y_true.values
        fig.add_trace(go.Histogram(x=err, nbinsx=50, marker_color=TEAL_L,
                                    name="error", showlegend=False), row=2, col=1)
        fig.add_vline(x=0, line_dash="dash", line_color=GOLD, row=2, col=1)

    # 4. feature importance
    imp = pd.Series(booster.feature_importance(importance_type="gain"),
                    index=booster.feature_name()).sort_values(ascending=True).tail(15)
    fig.add_trace(go.Bar(x=imp.values, y=imp.index, orientation="h",
                          marker_color=TEAL, showlegend=False,
                          hovertemplate="%{y}<br>gain: %{x:.0f}<extra></extra>"),
                  row=2, col=2)

    # layout
    fig.update_layout(
        title=dict(text="<b>Zomato ETA Predictor  —  Live Dashboard</b>",
                   font=dict(size=22, color=NAVY)),
        paper_bgcolor="#F8FAFC",
        plot_bgcolor="white",
        font=dict(family="Inter, Helvetica, Arial", color=NAVY, size=12),
        height=820, width=1300,
        showlegend=True,
        legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"),
        margin=dict(l=60, r=40, t=110, b=60),
    )
    fig.update_xaxes(title_text="Actual time (min)", row=1, col=1)
    fig.update_yaxes(title_text="Predicted time (min)", row=1, col=1)
    fig.update_xaxes(title_text="Time (min)", row=1, col=2)
    fig.update_yaxes(title_text="Order count", row=1, col=2)
    fig.update_xaxes(title_text="Error (pred − actual) min", row=2, col=1)
    fig.update_yaxes(title_text="Order count", row=2, col=1)
    fig.update_xaxes(title_text="LightGBM gain", row=2, col=2)
    fig.update_yaxes(title_text="", row=2, col=2)

    plot_div = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="main-dash")

    # Build the full HTML
    mae_str  = f"{mae:.3f} min"  if have_truth else "n/a"
    rmse_str = f"{rmse:.3f} min" if have_truth else "n/a"
    r2_str   = f"{r2:.3f}"       if have_truth else "n/a"

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><title>Zomato ETA Dashboard</title>
<style>
  body{{margin:0;font-family:Inter,Helvetica,Arial,sans-serif;background:#F1F5F9;color:#0F172A;}}
  .hero{{background:linear-gradient(135deg,#0A1F33 0%,#12304A 100%);color:#fff;
        padding:36px 48px;}}
  .hero h1{{margin:0;font-size:34px;font-weight:800;letter-spacing:-0.5px;}}
  .hero h1 span{{color:#2DD4BF;}}
  .hero .sub{{color:#94A3B8;margin-top:6px;font-size:14px;}}
  .stats{{display:flex;gap:14px;margin-top:24px;flex-wrap:wrap;}}
  .stat{{background:rgba(255,255,255,.06);border:1px solid #2DD4BF40;
        border-radius:10px;padding:14px 18px;min-width:160px;}}
  .stat .v{{font-size:30px;font-weight:800;color:#fff;}}
  .stat .l{{font-size:11px;color:#94A3B8;letter-spacing:0.5px;text-transform:uppercase;
           margin-top:4px;}}
  .stat.gold{{border-color:#F59E0B80;}}
  .stat.gold .v{{color:#F59E0B;}}
  .panel{{padding:24px 48px 48px;}}
  .card{{background:#fff;border-radius:14px;
        box-shadow:0 4px 24px rgba(10,31,51,.08);padding:24px;margin-bottom:24px;}}
  .card h2{{margin:0 0 6px;color:#0A1F33;font-size:18px;}}
  .card p.muted{{margin:0 0 16px;color:#64748B;font-size:13px;}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:24px;}}
  .tag{{display:inline-block;background:#CCFBF1;color:#0D9488;padding:3px 10px;
        border-radius:12px;font-size:11px;font-weight:600;margin-right:6px;}}
  .tag.gold{{background:#FEF3C7;color:#B45309;}}
  table{{border-collapse:collapse;width:100%;font-size:13px;}}
  th{{background:#0A1F33;color:#fff;text-align:left;padding:8px 12px;}}
  td{{padding:8px 12px;border-bottom:1px solid #E2E8F0;}}
  tr:nth-child(even) td{{background:#F8FAFC;}}
  .footer{{padding:24px 48px 32px;color:#64748B;font-size:12px;text-align:center;}}
  .footer a{{color:#0D9488;text-decoration:none;}}
  code{{background:#F1F5F9;padding:2px 6px;border-radius:4px;font-family:monospace;
        font-size:12px;}}
</style></head><body>

<div class="hero">
  <h1>Zomato <span>ETA</span> Predictor</h1>
  <div class="sub">Tuned LightGBM regressor &nbsp;·&nbsp; 5-fold CV, seed 42 &nbsp;·&nbsp;
                   Team <b>Hmmmmmmmmmm</b> &nbsp;·&nbsp; DataVerse 2026 · BMSCE</div>
  <div class="stats">
    <div class="stat gold"><div class="v">{mae_str}</div><div class="l">Mean Abs Error</div></div>
    <div class="stat"><div class="v">{rmse_str}</div><div class="l">RMSE</div></div>
    <div class="stat"><div class="v">{r2_str}</div><div class="l">R²</div></div>
    <div class="stat"><div class="v">{len(df):,}</div><div class="l">Orders scored</div></div>
    <div class="stat"><div class="v">{booster.num_trees()}</div><div class="l">Trees in ensemble</div></div>
    <div class="stat"><div class="v">{len(booster.feature_name())}</div><div class="l">Features</div></div>
  </div>
</div>

<div class="panel">
  <div class="card">
    <h2>Live model dashboard</h2>
    <p class="muted">Predicted vs actual delivery time, distribution overlap, error histogram, and feature importance.
       Hover any chart for exact values.</p>
    {plot_div}
  </div>

  <div class="grid2">
    <div class="card">
      <h2>Architecture</h2>
      <p class="muted">Tabular regression pipeline — same patterns as the regional classifier, different head.</p>
      <p><span class="tag">cleaning</span><span class="tag">features</span><span class="tag">CV</span>
         <span class="tag gold">model</span></p>
      <pre style="font-size:11px;line-height:1.4;background:#0A1F33;color:#E2E8F0;
                   padding:14px;border-radius:8px;overflow-x:auto;">
raw CSV
  │
  ▼  src/data.py::load_clean
      strip "NaN", coerce numerics, parse dates,
      cap ratings, drop zero-island coords
  │
  ▼  src/features.py::build_modeling_frame
      haversine distance (capped at 30 km),
      prep_time, peak-hour flags, weekend,
      day_of_week, month
  │
  ▼  LightGBM Regressor
      n_estimators=1200, lr=0.04, num_leaves=63
      Optuna-tuned (60 trials, 5-min cap)
  │
  ▼  5-fold StratifiedKFold (seed=42)
  │
  ▼  models/lgbm_v1.txt    ← THE model
      </pre>
    </div>

    <div class="card">
      <h2>How to reproduce</h2>
      <p class="muted">Single command, deterministic seed, no GPU needed.</p>
      <pre style="font-size:12px;line-height:1.5;background:#0A1F33;color:#E2E8F0;
                  padding:14px;border-radius:8px;overflow-x:auto;">
$ python predict_eta.py \\
    --input "data/raw/Zomato Dataset.csv" \\
    --output predictions_eta.csv

Cleans → features → loads model → predicts →
saves CSV → renders this HTML.
End-to-end in &lt; 5 seconds on a laptop CPU.
      </pre>
      <p style="margin-top:16px;color:#64748B;font-size:13px;">
        Same pattern as <code>predict.py</code> for the regional classifier.
        Both models share the same cleaning and feature pipeline — only the prediction head differs.
      </p>
    </div>
  </div>
</div>

<div class="footer">
  <b>Team Hmmmmmmmmmm</b> &nbsp;·&nbsp; Suchit SM &nbsp;·&nbsp; Rayyan Shaikh &nbsp;·&nbsp; Ranadeep M
  <br/>
  <a href="https://github.com/TheClazer/Zomato-delivery-estimation" target="_blank">
    github.com/TheClazer/Zomato-delivery-estimation
  </a>
</div>
</body></html>"""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
