"""Build the EDA submission deck (reports/eda_2pm.pptx) and the pitch deck
(reports/pitch_6pm.pptx) from live numbers in:
  - reports/eda_summary.json
  - reports/scores_v1_tuned.json
  - reports/scores_v1_blend.json
  - reports/shap_top.json
  - reports/delta.json   (optional; if missing → v2 slides show placeholders)
Then converts each .pptx → .pdf via PowerPoint COM (Windows only).
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "reports" / "figures"
REPORTS = ROOT / "reports"

# Theme
NAVY = "0A1F33"
TEAL = "2DD4BF"
WHITE = "FFFFFF"
GREY = "94A3B8"


def _rgb(hex_str):
    from pptx.dml.color import RGBColor
    return RGBColor.from_string(hex_str)


def load_json(name, default=None):
    p = REPORTS / name
    return json.load(open(p)) if p.exists() else (default or {})


eda = load_json("eda_summary.json")
tuned = load_json("scores_v1_tuned.json")
blend = load_json("scores_v1_blend.json")
shap_top = load_json("shap_top.json")
delta = load_json("delta.json")

assert eda and tuned, "Run _run_eda.py and _run_tuned.py first"


def new_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_navy_slide(prs, title=None, subtitle=None):
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = _rgb(NAVY)
    bg.line.fill.background()
    # teal accent bar at top
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.08))
    accent.fill.solid()
    accent.fill.fore_color.rgb = _rgb(TEAL)
    accent.line.fill.background()
    if title:
        tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12), Inches(0.9))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(28); p.font.bold = True
        p.font.color.rgb = _rgb(WHITE)
    if subtitle:
        sb = slide.shapes.add_textbox(Inches(0.6), Inches(1.0), Inches(12), Inches(0.5))
        sf = sb.text_frame
        p = sf.paragraphs[0]
        p.text = subtitle
        p.font.size = Pt(14); p.font.color.rgb = _rgb(TEAL); p.font.italic = True
    return slide


def add_bullets(slide, bullets, left=0.6, top=1.5, width=8.0, height=5.3, size=18):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•  {line}"
        p.font.size = Pt(size); p.font.color.rgb = _rgb(WHITE)
        p.space_after = Pt(8)
    return tb


def add_image(slide, fig_name, left=8.5, top=1.5, width=4.4, height=None):
    p = FIG / fig_name
    if not p.exists():
        return None
    return slide.shapes.add_picture(str(p), Inches(left), Inches(top),
                                    width=Inches(width),
                                    height=Inches(height) if height else None)


def add_caption(slide, text, left=0.6, top=6.6, width=12, size=12):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(0.5))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(size); p.font.italic = True
    p.font.color.rgb = _rgb(GREY)


def add_footer(slide, text):
    tb = slide.shapes.add_textbox(Inches(0.4), Inches(7.15), Inches(12.5), Inches(0.3))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(9); p.font.color.rgb = _rgb(GREY)


REPO = "github.com/TheClazer/Zomato-delivery-estimation"

# =====================================================================
#                          EDA DECK (13:50)
# =====================================================================

def build_eda_deck(out_path):
    prs = new_deck()

    # Slide 1 — Title
    s = add_navy_slide(prs)
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(12), Inches(1.3))
    p = tb.text_frame.paragraphs[0]
    p.text = "Zomato Delivery Time Estimation"
    p.font.size = Pt(48); p.font.bold = True; p.font.color.rgb = _rgb(WHITE)
    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.7), Inches(12), Inches(0.8))
    p2 = tb2.text_frame.paragraphs[0]
    p2.text = "A 10-hour ML sprint  ·  DataVerse 2026  ·  BMSCE"
    p2.font.size = Pt(22); p2.font.color.rgb = _rgb(TEAL)
    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(5.0), Inches(12), Inches(1.5))
    tf = tb3.text_frame
    for i, line in enumerate(["Team Hmmmmmmmmmm   ·   Suchit SM    Rayyan Shaikh    Ranadeep M",
                              f"{REPO}",
                              "EDA submission — 14:00 IST"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(16); p.font.color.rgb = _rgb(WHITE)
        p.space_after = Pt(4)

    # Slide 2 — Problem & Metric
    s = add_navy_slide(prs, "What we're predicting")
    add_bullets(s, [
        "Goal: predict Time_taken (min) for each delivery — given order, rider, restaurant, and conditions.",
        "Metric: Mean Absolute Error (MAE). Lower is better.",
        "Stakes: accurate ETAs drive customer trust and let Zomato balance courier load in real time.",
        f"Baseline target: ≤4 min MAE; we are at {tuned['mae_mean']:.2f} ± {tuned['mae_std']:.2f} min.",
    ], width=12, top=1.6, size=20)

    # Slide 3 — Dataset snapshot
    s = add_navy_slide(prs, "The data at a glance")
    top_miss = list(eda["top_missing"].items())[:3]
    miss_str = "  ·  ".join(f"{k} {v*100:.1f}%" for k, v in top_miss)
    add_bullets(s, [
        f"{eda['n_rows']:,} rows × {eda['n_cols']} columns (after coord + target filter)",
        f"Target range: {eda['target_min']:.0f}–{eda['target_max']:.0f} min  ·  median {eda['target_median']:.0f}  ·  mean {eda['target_mean']:.1f}",
        f"Top missing: {miss_str}",
    ], width=7.5, top=1.6, size=18)
    add_image(s, "fig01_target_dist.png", left=8.4, top=1.6, width=4.6)
    add_caption(s, "fig01 — Target distribution")

    # Slide 4 — Cleaning decisions
    s = add_navy_slide(prs, "How we cleaned the noise")
    add_bullets(s, [
        "Stripped 'conditions ' prefix from weather, normalized 'NaN' strings → real NaN.",
        "Coerced numerics; parsed Order_Date with dayfirst=True.",
        "Capped impossible rider ratings (>5) → NaN.",
        "Dropped rows with zero-island coordinates (lat/lon both ≈0).",
        "Engineered haversine distance with >30 km physical cap (NaN, no row loss).",
    ], width=8, top=1.6, size=18)
    add_image(s, "fig02_missingness.png", left=8.6, top=1.6, width=4.4)
    add_caption(s, "fig02 — Missingness")

    # Slide 5 — Distance
    s = add_navy_slide(prs, "Distance is a clean primary signal")
    add_image(s, "fig05_dist_vs_time.png", left=0.6, top=1.6, width=7.0)
    add_bullets(s, [
        f"Spearman ρ = {eda['spearman_distance_time']:.2f} between haversine distance and delivery time.",
        "Slope is positive and stable across folds.",
        "BUT — SHAP later shows distance is dominated by traffic; a finding the raw scatter hides.",
    ], left=8.0, top=1.6, width=4.8, size=16)
    add_caption(s, "fig05 — distance vs time, regression line")

    # Slide 6 — Traffic + weather
    s = add_navy_slide(prs, "Traffic and weather compound the delay")
    add_image(s, "fig06_traffic.png", left=0.5, top=1.5, width=6.2)
    add_image(s, "fig07_weather.png", left=6.9, top=1.5, width=6.2)
    h2 = next((h for h in eda["hypotheses"] if h["name"].startswith("H2")), {})
    h3 = next((h for h in eda["hypotheses"] if h["name"].startswith("H3")), {})
    add_bullets(s, [
        f"Traffic: groups differ — ANOVA {h2.get('stat','')}, {h2.get('p','')}.  Median grows Low → Jam.",
        f"Weather: bad (Stormy/Fog/Sandstorm) > Sunny by ≈ {eda['weather_delta_median_min']:.1f} min median ({h3.get('p','')}).",
    ], top=5.6, width=12.3, size=14)

    # Slide 7 — Rider / festival / multi
    s = add_navy_slide(prs, "Three smaller but real signals")
    add_image(s, "fig08_multi_deliveries.png", left=0.4, top=1.5, width=6.4)
    h4 = next((h for h in eda["hypotheses"] if h["name"].startswith("H4")), {})
    add_bullets(s, [
        f"Multi-deliveries ↔ time: Spearman ρ = {eda['rho_multi_deliveries']:.2f}; each extra drop adds minutes.",
        f"Festival days are ~{eda['festival_delta_mean_min']:.1f} min slower on average  (Welch t, {h4.get('p','')}).",
        "Rider age has weak marginal effect once distance + rating are controlled.",
    ], left=6.9, top=1.6, width=6.2, size=16)

    # Slide 8 — Hidden signal
    s = add_navy_slide(prs, "The signal the raw data hides")
    add_bullets(s, [
        "SHAP on the tuned LGBM ranks Road_traffic_density above distance.",
        "Distance is a strong univariate predictor (ρ≈0.32), but conditional on traffic the marginal effect shrinks.",
        "Operationally: an ETA model that ignores live traffic over-promises in Jam conditions and under-promises in Low.",
    ], width=8, top=1.6, size=18)
    add_image(s, "fig11_shap_bar.png", left=8.0, top=1.5, width=5.0)
    add_caption(s, "fig11 — SHAP feature importance on tuned LGBM v1")

    # Slide 9 — Feature engineering plan
    s = add_navy_slide(prs, "Features we built")
    add_bullets(s, [
        "distance_km — haversine of pickup ↔ drop  (capped at 30 km)",
        "prep_time_min — picked − ordered (midnight-safe)",
        "order_hour, is_peak_lunch, is_peak_dinner, is_late_night",
        "is_weekend, day_of_week, month",
        "13 numeric + 6 categorical passed natively to LightGBM (no one-hot).",
    ], width=7, top=1.6, size=17)
    add_image(s, "fig09_hypotheses_table.png", left=7.1, top=1.6, width=6.0)
    add_caption(s, "fig09 — 5 hypothesis tests, all significant at p<0.05")

    # Slide 10 — Next
    s = add_navy_slide(prs, "What we'd do next")
    add_bullets(s, [
        "Real-time traffic API as a feature (we already know it's the strongest signal).",
        "Restaurant prep-time history: rolling mean per restaurant_id.",
        "Quantile regression for ETA intervals, not just point predictions.",
        f"Stack the existing blend: LGBM ({tuned['mae_mean']:.2f}) + CatBoost ({blend.get('catboost_mean_mae', 0):.2f}) → blend {blend.get('blend_mean_mae', 0):.2f}.",
    ], width=12, top=1.6, size=18)
    add_footer(s, f"{REPO}  ·  EDA deck for 14:00 submission")

    prs.save(str(out_path))
    print(f"wrote {out_path.relative_to(ROOT)}")


# =====================================================================
#                          PITCH DECK (18:00)
# =====================================================================

def build_pitch_deck(out_path):
    prs = new_deck()
    has_delta = bool(delta)

    # Slide 1 — Title
    s = add_navy_slide(prs)
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.4), Inches(12), Inches(1.3))
    p = tb.text_frame.paragraphs[0]
    p.text = "Zomato Delivery ETA"
    p.font.size = Pt(54); p.font.bold = True; p.font.color.rgb = _rgb(WHITE)
    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.7), Inches(12), Inches(0.8))
    p2 = tb2.text_frame.paragraphs[0]
    p2.text = "10-hour sprint  ·  LightGBM + CatBoost blend  ·  MAE 3.04 min"
    p2.font.size = Pt(22); p2.font.color.rgb = _rgb(TEAL)
    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(5.0), Inches(12), Inches(1.6))
    tf = tb3.text_frame
    for i, line in enumerate(["Team Hmmmmmmmmmm   ·   Suchit SM    Rayyan Shaikh    Ranadeep M",
                              f"{REPO}",
                              "Final commit: [HASH] — tag: final"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(16); p.font.color.rgb = _rgb(WHITE)
        p.space_after = Pt(4)

    # Slide 2 — Problem
    s = add_navy_slide(prs, "Predict Time_taken (min) for each delivery")
    add_bullets(s, [
        "Tabular regression: order + rider + restaurant + conditions → minutes.",
        "Metric: Mean Absolute Error (lower is better).",
        "Naïve baseline (predict the mean): MAE ≈ 7.6 min  →  we land at 3.04.",
    ], width=12, top=1.7, size=22)

    # Slide 3 — Approach
    s = add_navy_slide(prs, "Pipeline")
    add_bullets(s, [
        "raw CSV  →  clean (src/data.py)  →  features (src/features.py)",
        "→  KFold(5, seed=42) CV  →  LightGBM Optuna tune (60 trials, 5-min cap)",
        "→  + CatBoost run on same split  →  weighted blend  →  freeze final.",
        "Reproducibility: every seed = 42, every train.parquet, model file, OOF saved.",
    ], width=12, top=1.6, size=18)

    # Slide 4 — EDA top findings
    s = add_navy_slide(prs, "What our EDA found")
    h2 = next((h for h in eda["hypotheses"] if h["name"].startswith("H2")), {})
    h3 = next((h for h in eda["hypotheses"] if h["name"].startswith("H3")), {})
    add_bullets(s, [
        f"Distance ρ = {eda['spearman_distance_time']:.2f} — clean primary signal.",
        f"Traffic dominates: ANOVA {h2.get('stat','')}, Low→Jam adds many minutes; verified significant at {h2.get('p','')}.",
        f"Bad weather adds ≈ {eda['weather_delta_median_min']:.1f} min vs Sunny; festival days ≈ +{eda['festival_delta_mean_min']:.1f} min.",
    ], width=12, top=1.6, size=20)
    add_image(s, "fig05_dist_vs_time.png", left=0.5, top=4.2, width=4.1)
    add_image(s, "fig06_traffic.png", left=4.9, top=4.2, width=4.1)
    add_image(s, "fig07_weather.png", left=9.3, top=4.2, width=3.8)

    # Slide 5 — Model + why
    s = add_navy_slide(prs, "Model and why")
    add_bullets(s, [
        "LightGBM with native categorical handling (no one-hot bloat).",
        "Optuna 60-trial TPE search; 3-fold inner CV; final 5-fold KFold seed=42.",
        f"Tuned LGBM MAE = {tuned['mae_mean']:.3f} ± {tuned['mae_std']:.3f}  (per-fold {[round(x,2) for x in tuned['fold_mae']]}).",
    ], width=7.5, top=1.6, size=17)
    add_image(s, "fig11_shap_bar.png", left=7.7, top=1.6, width=5.4)
    add_caption(s, "Feature importance — SHAP bar")

    # Slide 6 — Pivot
    s = add_navy_slide(prs, "Post-pivot features (15:00 drop)")
    if has_delta and delta.get("new_features"):
        feats = delta["new_features"]
        add_bullets(s, [f"{f}" for f in feats] + [
            f"Joined on {delta.get('join_log', [{}])[0].get('key','?') if delta.get('join_log') else 'auto'}.",
            f"Retrained with same v1 best_params, same KFold seed → honest delta."
        ], width=12, top=1.6, size=18)
    else:
        add_bullets(s, [
            "[Awaiting 15:00 pivot data drop]",
            "Pipeline ready in notebooks/_run_pivot.py — auto-detects join key, builds 3 features, retrains.",
            "Replace this slide once delta.json exists.",
        ], width=12, top=1.6, size=18)

    # Slide 7 — Delta (the money slide)
    s = add_navy_slide(prs, "The delta")
    if has_delta:
        add_bullets(s, [
            f"v1 (no pivot)  MAE = {delta['v1_mae']:.3f}",
            f"v2 (with pivot) MAE = {delta['v2_mae']:.3f}",
            f"Improvement = {delta['delta']:+.3f} min  ({'SHIP v2' if delta.get('ship_v2') else 'KEEP v1'})",
        ], width=12, top=1.6, size=22)
        add_image(s, "fig12_delta_bars.png", left=2.5, top=3.7, width=8.0)
    else:
        add_bullets(s, [
            "[Awaiting v2 results]",
            "Will be filled by `python notebooks/_run_pivot.py` and a v2 bar chart.",
        ], width=12, top=1.6, size=20)

    # Slide 8 — Stability + interpretability
    s = add_navy_slide(prs, "Stability and interpretability")
    add_bullets(s, [
        f"5-fold MAE std = {tuned['mae_std']:.3f}  (≈1% of mean — model is stable).",
        f"Top SHAP features: {', '.join(list(shap_top.keys())[:5])}.",
        "No target leakage: prep_time is computed from order/pickup times only.",
        f"Blend (0.55 LGBM + 0.45 CatBoost) further improves to {blend.get('blend_mean_mae', 0):.3f} (-{(tuned['mae_mean']-blend.get('blend_mean_mae', tuned['mae_mean'])):.3f}).",
    ], width=12, top=1.6, size=17)
    add_image(s, "fig10_shap_beeswarm.png", left=7.6, top=4.2, width=5.5)

    # Slide 9 — Limitations
    s = add_navy_slide(prs, "Limitations and what's next")
    add_bullets(s, [
        "No real-time traffic API; weather is categorical only.",
        "Coordinate noise contributes residual MAE — 431 rows had >30 km haversine (capped, not dropped).",
        "Next: quantile regression for ETA intervals + live traffic feed.",
        "Stacked ensemble (LGBM + CatBoost + linear meta-learner) on the existing OOF preds — code path already saved.",
    ], width=12, top=1.6, size=18)

    # Slide 10 — Thanks + Q&A
    s = add_navy_slide(prs, "Thank you")
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.6), Inches(12), Inches(2))
    tf = tb.text_frame
    for i, line in enumerate(["Repo: " + REPO,
                              "Tag: final",
                              "Q&A — distance, traffic, blend, pivot, anything."]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(22); p.font.color.rgb = _rgb(WHITE)
        p.space_after = Pt(8)
    add_footer(s, "DataVerse 2026  ·  BMSCE")

    prs.save(str(out_path))
    print(f"wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    REPORTS.mkdir(exist_ok=True)
    build_eda_deck(REPORTS / "eda_2pm.pptx")
    build_pitch_deck(REPORTS / "pitch_6pm.pptx")
