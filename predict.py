"""Single-command regional classifier — production-style.

Usage
-----
    python predict.py --input data/raw/Zomato\ Dataset.csv \
                      --model models/region_classifier_v2_structural.txt \
                      --output predictions.csv

The CSV needs the same columns as our raw Zomato schema (we run the
exact same cleaning + feature pipeline as training). The output adds
two columns: `prob_south` and `predicted_region`.

Also benchmarks inference latency so judges can see real numbers.
"""
from __future__ import annotations
import argparse, time, sys
from pathlib import Path
import pandas as pd
import numpy as np
import lightgbm as lgb

# Make src/ importable when called from any working directory
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.data import load_clean
from src.features import add_features
from src.regional import annotate_region


def main():
    ap = argparse.ArgumentParser(description="Predict region (South=1 / North=0) for Zomato delivery orders.")
    ap.add_argument("--input",  required=True, help="path to a CSV with the Zomato schema")
    ap.add_argument("--model",  default="models/region_classifier_v2_structural.txt",
                    help="LightGBM booster file (default: structural model)")
    ap.add_argument("--output", default="predictions.csv",
                    help="where to write per-row predictions")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="probability threshold for South=1 / North=0 (default 0.5)")
    args = ap.parse_args()

    t0 = time.perf_counter()
    print(f"[1/5] Loading + cleaning {args.input} ...")
    df = load_clean(args.input)
    t1 = time.perf_counter()
    print(f"      {len(df):,} rows after cleaning   ({(t1-t0)*1000:.0f} ms)")

    print(f"[2/5] Engineering features ...")
    df_f = add_features(df)
    t2 = time.perf_counter()
    print(f"      {df_f.shape[1]} columns                 ({(t2-t1)*1000:.0f} ms)")

    print(f"[3/5] Region label (city-code → state → region) ...")
    df_f = annotate_region(df_f)
    t3 = time.perf_counter()
    print(f"      South candidates: {(df_f['is_south']==1).sum():,}   "
          f"({(t3-t2)*1000:.0f} ms)")

    print(f"[4/5] Loading model from {args.model} ...")
    booster = lgb.Booster(model_file=args.model)
    feat_names = booster.feature_name()
    t4 = time.perf_counter()
    print(f"      {booster.num_trees()} trees · {len(feat_names)} features   ({(t4-t3)*1000:.0f} ms)")

    print(f"[5/5] Predicting ...")
    # Materialise the feature columns; categoricals must be 'category' dtype
    missing = [c for c in feat_names if c not in df_f.columns]
    if missing:
        raise SystemExit(f"input is missing columns required by the model: {missing}")
    X = df_f[feat_names].copy()
    for c in feat_names:
        if df_f[c].dtype.name in ("object", "category"):
            X[c] = X[c].astype("category")
    proba = booster.predict(X)
    pred  = (proba >= args.threshold).astype(int)
    t5 = time.perf_counter()
    print(f"      done                              ({(t5-t4)*1000:.0f} ms)")

    df_out = df.copy()
    df_out["prob_south"] = proba
    df_out["predicted_region"] = np.where(pred == 1, "South", "North")
    df_out.to_csv(args.output, index=False)

    total_ms = (t5 - t0) * 1000
    per_row_us = (total_ms * 1000) / max(1, len(df))
    print()
    print("=" * 60)
    print(f"Wrote {args.output}  ({len(df_out):,} rows)")
    print(f"End-to-end latency : {total_ms:.0f} ms")
    print(f"Per-row throughput : {per_row_us:.1f} µs/row  "
          f"({1_000_000/per_row_us:,.0f} rows/sec)")
    print(f"Model file         : {args.model}  "
          f"({Path(args.model).stat().st_size:,} bytes)")
    # Agreement with the embedded ground-truth label, if present
    if "is_south" in df_f.columns:
        from sklearn.metrics import roc_auc_score, accuracy_score
        valid = df_f["region"].isin(["North", "South"])
        if valid.sum() > 100:
            auc = roc_auc_score(df_f.loc[valid, "is_south"], proba[valid.values])
            acc = accuracy_score(df_f.loc[valid, "is_south"], pred[valid.values])
            print(f"Agreement with truth: AUC = {auc:.4f}  ·  accuracy = {acc:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
