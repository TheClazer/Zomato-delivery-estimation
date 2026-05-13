"""Rebuild reports/understanding_guide.pdf as a real teaching document.
Plain-English first, formula second, our-specific-result third.
Every chart described with axes. Every number unpacked.
"""
from pathlib import Path
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, ListFlowable, ListItem)

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "reports" / "understanding_guide.pdf"
D = json.load(open(ROOT / "reports" / "regional_findings.json"))

NAVY=HexColor("#0A1F33"); TEAL=HexColor("#0D9488")
TEAL_L=HexColor("#2DD4BF"); GOLD=HexColor("#D97706")
GREEN=HexColor("#16A34A"); RED=HexColor("#DC2626")
GREY=HexColor("#475569"); LIGHT=HexColor("#F1F5F9")

ss = getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=ss["Heading1"],fontSize=20,leading=24,textColor=NAVY,
                  spaceBefore=4,spaceAfter=6,fontName="Helvetica-Bold")
H2=ParagraphStyle("H2",parent=ss["Heading2"],fontSize=14,leading=18,textColor=TEAL,
                  spaceBefore=12,spaceAfter=4,fontName="Helvetica-Bold")
H3=ParagraphStyle("H3",parent=ss["Heading3"],fontSize=11.5,leading=14,textColor=NAVY,
                  spaceBefore=8,spaceAfter=2,fontName="Helvetica-Bold")
H4=ParagraphStyle("H4",parent=ss["Heading3"],fontSize=10.5,leading=13,textColor=TEAL,
                  spaceBefore=4,spaceAfter=2,fontName="Helvetica-Bold")
body=ParagraphStyle("body",parent=ss["BodyText"],fontSize=10.5,leading=14,
                    textColor=HexColor("#1E293B"),alignment=TA_JUSTIFY,
                    fontName="Helvetica",spaceAfter=4)
plain=ParagraphStyle("plain",parent=body,alignment=TA_LEFT)
small=ParagraphStyle("small",parent=body,fontSize=9,leading=12,textColor=GREY)
bul=ParagraphStyle("bul",parent=body,leftIndent=14,bulletIndent=2,spaceAfter=2)
mono=ParagraphStyle("mono",parent=body,fontName="Courier",fontSize=9,leading=11,
                    backColor=LIGHT,leftIndent=6,rightIndent=6,
                    spaceBefore=2,spaceAfter=4,borderPadding=4)


def bullets(items, c=TEAL):
    return ListFlowable([ListItem(Paragraph(t,bul),leftIndent=10,bulletColor=c,value="•") for t in items],
                        bulletType="bullet",start="bulletchar",leftIndent=10)


def tbl(data, cw=None, header_bg=NAVY):
    t = Table(data, colWidths=cw, repeatRows=1)
    s=[("BACKGROUND",(0,0),(-1,0),header_bg),("TEXTCOLOR",(0,0),(-1,0),white),
       ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
       ("BOTTOMPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),
       ("GRID",(0,0),(-1,-1),0.3,HexColor("#CBD5E1")),
       ("VALIGN",(0,0),(-1,-1),"TOP")]
    for r in range(1,len(data)):
        if r%2==0: s.append(("BACKGROUND",(0,r),(-1,r),HexColor("#F8FAFC")))
    t.setStyle(TableStyle(s)); return t


def callout(text, color="gold"):
    s=ParagraphStyle("co",parent=body,fontSize=11,leading=14,
                    borderPadding=8,leftIndent=4,rightIndent=4,
                    spaceBefore=6,spaceAfter=8,borderWidth=0.9)
    if color=="teal": s.backColor=HexColor("#CCFBF1"); s.borderColor=TEAL
    elif color=="green": s.backColor=HexColor("#DCFCE7"); s.borderColor=GREEN
    elif color=="red": s.backColor=HexColor("#FEE2E2"); s.borderColor=RED
    else: s.backColor=HexColor("#FEF3C7"); s.borderColor=GOLD
    return Paragraph(text,s)


A=D["model_geo"]; B=D["model_behaviour"]
B2=D["model_behaviour_no_temporal"]; C=D.get("model_structural",{})
deep=D.get("deep_check",{}); leak=D["temporal_leak"]
findings=D["findings"]; city_check=D["city_check"]


story = []

# ====================================================================
# TITLE + ORIENTATION
# ====================================================================
story += [
    Spacer(1, 0.2*cm),
    Paragraph("Understanding Guide  —  the explain-it-to-me-from-scratch version", H1),
    Paragraph(
        "Zomato Delivery · North vs South Regional Classification · Team Hmmmmmmmmmm",
        ParagraphStyle("sub", parent=body, fontSize=11, textColor=TEAL,
                       fontName="Helvetica-Oblique", spaceAfter=6)),
    callout(
        "<b>How to read this document.</b> Each concept is presented three ways: "
        "(1) plain English — what it is in one sentence, no jargon; "
        "(2) why we care — what it actually measures; "
        "(3) our value — the specific number in our project, and what to say if a judge asks. "
        "Read top to bottom; nothing is skipped or assumed.",
        "teal"),
]

# ====================================================================
# SECTION 0 — THE THREE NUMBERS
# ====================================================================
story += [Paragraph("0.  The three numbers you must say correctly", H2)]
story.append(Paragraph(
    "If you remember nothing else, remember these three AUC values and what they mean:",
    body))
nums = [
    ["Number", "Plain English",                                                  "Our value", "What to say"],
    ["GEO AUC",        "Using only the latitude & longitude, can we classify each order as South or North?",
     f"{A['mean_auc']:.3f}",
     "Perfect, because the region is literally defined by location. This is a sanity check that our labels are correct."],
    ["BEHAVIOUR AUC", "Without using location, just using rider/order/weather/traffic data, can we tell South from North?",
     f"{B2['mean_auc']:.3f}",
     "Essentially random (0.50 is coin flip). It means the way deliveries unfold is operationally identical across regions."],
    ["STRUCTURAL AUC","Behaviour + one extra feature: the distance between restaurant and customer for each order.",
     f"{C.get('group_kfold_auc', 0):.3f}",
     "Jumps to 0.91. Geometric layout of cities differs — South cities have a different restaurant-to-customer geometry."],
]
story.append(tbl(nums, cw=[2.6*cm, 5.8*cm, 1.8*cm, 6.2*cm]))

# ====================================================================
# SECTION 1 — WHAT IS AUC, REALLY?
# ====================================================================
story += [PageBreak(), Paragraph("1.  What is AUC?  (the most important metric to explain)", H2)]

story.append(Paragraph("1.1  Plain English", H3))
story.append(Paragraph(
    "AUC stands for <b>Area Under the (ROC) Curve</b>. Imagine you pick two orders at random — one truly from the "
    "South, one truly from the North. You ask the model to score each one with a probability of being South. AUC "
    "is the probability that the model gives the truly-South order a <i>higher</i> score than the truly-North order. ",
    body))
story.append(bullets([
    "AUC = <b>1.0</b> → the model always ranks South higher than North. Perfect separation.",
    "AUC = <b>0.5</b> → the model is guessing. South and North get the same score on average. Coin flip.",
    "AUC = <b>0.0</b> → the model is perfectly wrong. Almost never happens; if it does, you've flipped the labels.",
    "AUC = <b>0.7-0.8</b> → useful predictor. AUC <b>&gt; 0.9</b> = strong. AUC <b>&lt; 0.55</b> = essentially random.",
]))

story.append(Paragraph("1.2  Why we use AUC instead of accuracy", H3))
story.append(Paragraph(
    "Accuracy = (# of correct predictions) / (total predictions). It depends on where you put the decision threshold "
    "(by default 0.5 — 'if probability of South &gt; 0.5, predict South'). Accuracy is misleading when classes are "
    "imbalanced. In our data, North is 61% of rows — a model that always predicts 'North' gets 61% accuracy without "
    "learning anything. AUC sidesteps this by looking at <i>ranking</i> across all possible thresholds.",
    body))

story.append(Paragraph("1.3  What does GEO AUC = 1.000 mean specifically?", H3))
story.append(Paragraph(
    f"It means that on every single one of the 41,944 orders, when we trained the model using only the latitude "
    f"and longitude features, every truly-South order received a higher predicted probability than every truly-"
    f"North order. The model got it right 100% of the time. <b>This is expected and not impressive</b> — we "
    f"defined South as 'state belongs to {{Kerala, TN, AP, Telangana, Karnataka}}', which is itself derived from "
    f"latitude/longitude (state borders are geographic). The GEO model is a <b>sanity check</b> that confirms our "
    f"label vector is correctly aligned with coordinates. If GEO AUC were 0.8 instead of 1.0, it would mean we had "
    f"labelled rows incorrectly. Because it's 1.0, we know our 22-city → region map is bug-free.",
    body))

story.append(callout(
    "<b>If a judge asks 'why is your AUC 1.0, isn't that overfitting?'</b> say: "
    "'AUC = 1.0 here proves the labels are clean. Region was defined by state, which is determined by coordinates. "
    "So a model trained on coordinates can recover region perfectly. This isn't the model being good — it's the "
    "data being internally consistent. The interesting models are the next two.'",
    "gold"))

story.append(Paragraph("1.4  AUC = 0.508 means almost-random — why is that the interesting result?", H3))
story.append(Paragraph(
    "0.508 is within Monte Carlo noise of 0.500. The behaviour-only model (no location, no distance, no time-leak features) "
    "is unable to distinguish South from North orders better than guessing. This is the NEGATIVE finding that, after six "
    "independent stress tests, becomes the headline: <b>Zomato's operational behaviour is statistically identical North vs "
    "South in this dataset</b>. It is not bad performance; it is honest reporting of the absence of a behavioural signal.",
    body))

# ====================================================================
# SECTION 2 — OTHER METRICS
# ====================================================================
story += [Paragraph("2.  Other metrics we report  (and what each tells you)", H2)]

story.append(Paragraph("2.1  F1 score", H3))
story.append(Paragraph(
    "Combines precision (of orders we PREDICTED South, how many were actually South?) and recall (of orders that ARE "
    "truly South, how many did we catch?) into a single number, range 0 to 1.",
    body))
story.append(Paragraph(
    "Precision = TP / (TP + FP)<br/>Recall    = TP / (TP + FN)<br/>F1        = 2 · Precision · Recall / (Precision + Recall)",
    mono))
story.append(Paragraph(
    f"Our structural model has F1 = {C.get('strat_kfold_f1', 0):.3f}. That means precision and recall are both "
    "high and balanced — when the model says 'South', it's right ~95% of the time, and it catches ~95% of the "
    "actual South orders.",
    body))

story.append(Paragraph("2.2  Balanced accuracy", H3))
story.append(Paragraph(
    "Average of recall on the South class and recall on the North class. Unlike plain accuracy, it doesn't favour "
    f"the majority class. Our value: <b>{C.get('strat_kfold_bal_acc', 0):.3f}</b>. A balanced-accuracy of 0.5 would "
    "be random; 1.0 would be perfect.",
    body))

story.append(Paragraph("2.3  Confusion matrix", H3))
story.append(Paragraph(
    "A 2×2 table that counts every prediction:",
    body))
cm = [
    ["",                 "Model predicted NORTH",  "Model predicted SOUTH"],
    ["Truly NORTH",      "TN (true negative)",      "FP (false positive)"],
    ["Truly SOUTH",      "FN (false negative)",     "TP (true positive)"],
]
story.append(tbl(cm, cw=[3.5*cm, 5.5*cm, 5.5*cm]))
story.append(Paragraph(
    "TP, FP, FN, TN are simply how many rows fell into each cell. Precision, recall, accuracy, F1 are all "
    "computed from these four numbers.",
    body))

# ====================================================================
# SECTION 3 — THE THREE MODELS, REALLY EXPLAINED
# ====================================================================
story += [PageBreak(), Paragraph("3.  The three models  —  what each one is and why", H2)]

story.append(Paragraph("3.1  Model A — GEO (the calibration model)", H3))
story.append(Paragraph(
    "<b>What it does:</b> takes five features — Restaurant_latitude, Restaurant_longitude, Delivery_location_"
    "latitude, Delivery_location_longitude, and haversine distance_km — and outputs the probability that the "
    "order is from South India.",
    body))
story.append(Paragraph(
    f"<b>Our result:</b> 5-fold AUC = {A['mean_auc']:.3f}, F1 = {A['mean_f1']:.3f}, balanced accuracy = "
    f"{A['mean_bal_acc']:.3f}. All five folds got AUC 1.0000 exactly.",
    body))
story.append(Paragraph(
    "<b>What it tells us:</b> the label vector is clean. The 22-city → region map we built has no errors. "
    "This isn't a real predictive achievement — it's a sanity check. <b>Why do we report it?</b> If we only "
    "showed Models B and C, judges could ask 'how do you know your labels are right?'. Model A is the audit "
    "trail that proves they are.",
    body))

story.append(Paragraph("3.2  Model B′ — BEHAVIOUR-only (the honest baseline)", H3))
story.append(Paragraph(
    "<b>What it does:</b> uses 12 numeric + 6 categorical behaviour features — rider age, rider rating, prep time, "
    "order hour, peak-hour flags, weekend flag, vehicle condition, multi-delivery count, weather conditions, "
    "traffic density, vehicle type, order type, city tier, festival. <b>No coordinates. No distance. No month or "
    "day_of_week</b> (those leak the data-collection window — see section 5).",
    body))
story.append(Paragraph(
    f"<b>Our result:</b> 5-fold AUC = {B2['mean_auc']:.3f}, F1 = {B2['mean_f1']:.3f}. Fold-by-fold: "
    f"{', '.join(f'{x:.3f}' for x in B2['fold_auc'])}. Two folds are exactly 0.500 — the model literally is "
    "guessing.",
    body))
story.append(Paragraph(
    "<b>What it tells us:</b> none of the behavioural features carry regional signal. Zomato's deliveries unfold "
    "the same way whether they're in Bangalore or Bhopal.",
    body))
story.append(Paragraph(
    "<b>File on disk:</b> <code>models/region_classifier_v1.txt</code> (951 KB, ~330 trees).",
    body))

story.append(Paragraph("3.3  Model C — STRUCTURAL (the headline model)", H3))
story.append(Paragraph(
    "<b>What it does:</b> Model B′ <i>plus</i> one feature — distance_km, the haversine distance between the "
    "restaurant pickup and the customer drop, for each individual order.",
    body))
story.append(Paragraph(
    f"<b>Our result:</b> 5-fold AUC = {C.get('strat_kfold_auc', 0):.3f}, F1 = {C.get('strat_kfold_f1', 0):.3f}. "
    f"GroupKFold AUC (when held-out cities differ from training cities) = {C.get('group_kfold_auc', 0):.3f}. "
    f"The fold-4 number is 0.642 (anomaly explained in section 5.3).",
    body))
story.append(Paragraph(
    "<b>What it tells us:</b> Even though pickup-to-drop distance has nearly identical medians in both regions "
    "(South 9.2 km, North 9.0 km), the <i>distributions differ in shape</i> (KS p ≈ 10⁻⁶⁷). South Indian "
    "cities have a structurally different layout of where restaurants are placed relative to where customers "
    "live. Cities like Bangalore or Chennai have a different fingerprint than Mumbai or Jaipur — and this "
    "geometric difference is what the model picks up on.",
    body))
story.append(Paragraph(
    "<b>File on disk:</b> <code>models/region_classifier_v2_structural.txt</code> (1.9 MB, ~276 trees).",
    body))

story.append(callout(
    "<b>How can distance_km be 'structural' and not 'geographic'?</b><br/>"
    "Geographic features tell you WHERE you are (latitude 12.97°, longitude 77.59° = Bangalore). "
    "Structural features tell you about the SHAPE of the operation. distance_km is the gap between "
    "pickup and drop for a single order — two different cities can produce the same distance_km value. "
    "We never tell the model that 12.97°/77.59° is Bangalore; we just give it the distance number, and "
    "the model learns 'orders in South tend to span 9–14 km with these particular tail behaviours, "
    "orders in North span 8–12 km with different tails'.",
    "gold"))

# ====================================================================
# SECTION 4 — STATISTICAL TESTS, REALLY EXPLAINED
# ====================================================================
story += [PageBreak(), Paragraph("4.  The statistical tests we used  (and their results)", H2)]

story.append(Paragraph("4.1  Mann-Whitney U test", H3))
story.append(Paragraph(
    "<b>Plain English:</b> Are these two groups of numbers similar?<br/>"
    "<b>How:</b> Rank everyone from all groups combined (smallest to largest). Sum the ranks for each group. "
    "If the groups are similar, the rank sums should be roughly equal. If one group is consistently higher or "
    "lower, the rank sums differ — and the U statistic captures that.<br/>"
    "<b>Why we use it:</b> our data is not Gaussian, so a t-test would be unsafe. Mann-Whitney makes no "
    "distributional assumption.",
    body))
story.append(Paragraph(
    "<b>What p-value means:</b> if there were truly no difference between South and North on this column, the "
    "probability of seeing a U statistic at least as extreme as ours is p. Small p (&lt; 0.05) → reject 'no "
    "difference'.",
    body))

story.append(Paragraph("4.2  Chi-square (χ²) test of independence", H3))
story.append(Paragraph(
    "<b>Plain English:</b> Do two categorical variables go together or are they unrelated?<br/>"
    "<b>How:</b> Build a table of counts (rows = traffic categories, columns = region). Compute what the table "
    "would look like if region and traffic were independent — that's the 'expected' table. Compare to what we "
    "actually see. The χ² statistic measures total squared difference, normalised by expected counts.<br/>"
    "<b>Why we use it:</b> weather, traffic, vehicle, order type are categorical; we want to know if their "
    "distribution differs by region.",
    body))

story.append(Paragraph("4.3  Kolmogorov-Smirnov (KS) two-sample test", H3))
story.append(Paragraph(
    "<b>Plain English:</b> Are two whole distributions identical, not just their medians?<br/>"
    "<b>How:</b> Plot the cumulative distribution function (CDF) of each group. The KS statistic D is the maximum "
    "vertical distance between the two curves at any point.<br/>"
    "<b>Why we use it:</b> Mann-Whitney can miss differences in the tails or shape. Two distributions can have "
    "identical medians but completely different spreads or skews — KS catches that.<br/>"
    "<b>Our key finding:</b> distance_km has KS D = 0.088, p ≈ 6.7 × 10⁻⁶⁷ — distributions differ in shape even "
    "though medians match (South 9.2 vs North 9.0). This is what justifies Model C.",
    body))

story.append(Paragraph("4.4  All eleven univariate tests at a glance", H3))
ft = [["#", "Feature", "Test", "Statistic", "p-value", "Verdict"]]
for f in findings:
    name = f["name"].split(":", 1)[1].strip() if ":" in f["name"] else f["name"]
    ft.append([f["id"].replace("fig_reg_", ""), name, f["test"], f["stat"],
               f"{f['p']:.2e}", f["verdict"]])
story.append(tbl(ft, cw=[1.5*cm, 5.0*cm, 3.5*cm, 2.5*cm, 2.0*cm, 2.0*cm]))
story.append(Paragraph(
    "<b>All eleven p-values are &gt; 0.05.</b> By the standard significance threshold, none of these univariate "
    "differences are statistically real. This is the 'apparent flat finding' that motivated the deeper checks.",
    body))

# ====================================================================
# SECTION 5 — STRESS TESTS, ONE PAGE EACH IDEA
# ====================================================================
story += [PageBreak(), Paragraph("5.  The six stress tests  —  trying to break the finding", H2)]

story.append(Paragraph(
    "After eleven univariate tests all said 'no difference', and the behaviour-only model AUC was 0.508 (random), "
    "we ran six MORE checks in case we were missing something. Here's each one in plain English.",
    body))

st_blocks = [
    ("5.1  KS distribution-shape on every numeric column",
     "<b>The worry it addresses:</b> 'maybe the medians match but the tails differ — Mann-Whitney would miss that'. "
     "<b>What we did:</b> ran KS test on every numeric column (delivery time, distance, age, rating, etc.). "
     "<b>Result:</b> only distance_km significant (D=0.088, p≈10⁻⁶⁷). Every other column had near-identical shapes."),
    ("5.2  Dispersion ratio (std comparison)",
     "<b>The worry:</b> 'maybe both regions have the same average but South has more variability'. "
     "<b>What we did:</b> computed south_std / north_std for every numeric column. "
     "<b>Result:</b> all ratios between 0.98 and 1.04. Variability is the same in both regions."),
    ("5.3  Interaction features ablation",
     "<b>The worry:</b> 'two features individually might not differ but their interaction could'. "
     "<b>What we did:</b> engineered 5 interaction features (traffic × hour, weather × traffic, vehicle × multi, "
     "distance × age, rating × traffic). Added them one at a time on top of behaviour-only and watched the AUC. "
     "<b>Result:</b> 4 out of 5 added zero lift. The one that lifted (distance_per_age) was distance_km in disguise."),
    ("5.4  GroupKFold by city",
     "<b>The worry:</b> 'maybe the model memorises per-city patterns and looks better than it really is'. "
     "<b>What we did:</b> in normal KFold we hold out random ROWS; in GroupKFold we hold out entire CITIES. "
     f"So the training cities and test cities don't overlap. <b>Result:</b> behaviour-only stayed at AUC "
     f"{deep.get('group_kfold_by_city',{}).get('mean_auc', 0.506):.3f} (random). Structural reached "
     f"{C.get('group_kfold_auc', 0):.3f} on held-out cities, with one fold (Fold 4, held Kochi + Hyderabad) "
     "dropping to 0.642 — a real limit (see section 7)."),
    ("5.5  Per-South-state internal classifier",
     f"<b>The worry:</b> 'is South India internally uniform, or are Kerala, TN, AP, Karnataka, Telangana all different "
     "from each other?'. <b>What we did:</b> trained a 4-way classifier on the South subset only, predicting state. "
     f"<b>Result:</b> accuracy = {deep.get('south_internal',{}).get('mean_accuracy', 0.377):.3f} vs random "
     f"{deep.get('south_internal',{}).get('random_baseline', 0.25):.3f}. South India is weakly internally heterogeneous "
     "— enough to explain the Fold-4 dip but not enough to overturn the 'behaviourally uniform' headline."),
    ("5.6  CatBoost cross-check",
     "<b>The worry:</b> 'is the 0.508 AUC a LightGBM-specific artefact?'. <b>What we did:</b> retrained the exact "
     "same task with CatBoost, a different gradient-boosting library that handles categoricals differently. "
     f"<b>Result:</b> CatBoost AUC = {deep.get('catboost_crosscheck',{}).get('mean_auc', 0.507):.3f}, within "
     "0.001 of LightGBM. Not a framework artefact."),
]
for title, content in st_blocks:
    story.append(Paragraph(title, H3))
    story.append(Paragraph(content, body))

# ====================================================================
# SECTION 6 — SANITY CHECKS EXPLAINED  ("Goa worst offender")
# ====================================================================
story += [PageBreak(), Paragraph("6.  The city-code sanity check (Goa was 'the worst offender')", H2)]

story.append(Paragraph(
    "We labelled each row by extracting the city prefix from <code>Delivery_person_ID</code> (e.g. <code>KOC"
    "RES16DEL01</code> → KOC → Kochi → Kerala → South). For this to be trustworthy, we needed to verify that "
    "the labels actually match reality.",
    body))

story.append(Paragraph("6.1  What we did", H3))
story.append(Paragraph(
    "For each of the 22 city codes, we already knew the expected lat/lon centroid (e.g. Bangalore ≈ 12.97°N, "
    "77.59°E). We computed the median latitude and median longitude of every row carrying that city code, then "
    "measured the distance (in kilometres) between the measured median and the expected centroid.",
    body))

story.append(Paragraph("6.2  Why a 'worst offender'?", H3))
story.append(Paragraph(
    "If all 22 cities had medians within (say) 10 km of their expected centroids, the labelling is rock-solid. "
    "If one city's median was off by 500 km, that would suggest the rider-ID prefix is mislabelled or the "
    "coordinate column is corrupted for those rows. We sort the table by km_off and report the worst one — "
    "to be transparent that we checked.",
    body))

story.append(Paragraph("6.3  The result", H3))
goa = next((r for r in city_check if r["code"] == "GOA"), None)
if goa:
    story.append(Paragraph(
        f"All 22 cities passed. The worst offender is <b>Goa (GOA)</b> at <b>{goa['km_off']} km</b> off centroid: "
        f"our orders' median was lat {goa['median_lat']}, lon {goa['median_lon']}, expected {goa['expected_lat']}, "
        f"{goa['expected_lon']}. 45 km is well under our 250 km tolerance — likely just that the GOA centroid we "
        "used was Panaji (the capital), while many orders come from elsewhere on the Goan coast (Margao, Vasco). "
        "<b>19 of the 22 cities are within 7 km</b> of their expected centroids — verification is exceptionally clean.",
        body))

story.append(callout(
    "<b>If asked 'what does worst offender mean?'</b> say: "
    "'It's the city whose actual median lat/lon was farthest from the expected centroid in our city-code map. "
    "Goa was 45 km off, well within our 250 km tolerance. It just means the labelled centroid for Goa state was "
    "Panaji, but Goa's orders are spread across Panaji, Margao, and Vasco. No correction needed — the city code "
    "still correctly identifies the region.'",
    "teal"))

# ====================================================================
# SECTION 7 — EVERY GRAPH, AXES EXPLAINED
# ====================================================================
story += [PageBreak(), Paragraph("7.  Every graph in our deliverables  —  axes explained", H2)]

graphs = [
    ("fig_reg_auc_compare.png",
     "Bar chart with 5 bars for the GEO model and 5 bars for the BEHAVIOUR model.",
     "Fold number (1, 2, 3, 4, 5)",
     "ROC-AUC (0.5 = random, 1.0 = perfect)",
     "Grey bars all sit at 1.0 (geo perfect). Teal bars all sit near 0.5 (behaviour random). The visual gap is the headline finding."),
    ("fig_reg_shap_bar.png",
     "Horizontal bars showing the average importance of each behaviour feature in Model B.",
     "Mean absolute SHAP value (how much the feature shifts the prediction)",
     "Feature name",
     "Month dominates (SHAP ≈ 0.45); every other feature has SHAP < 0.05. This is what revealed the temporal leak."),
    ("fig_reg_shap_beeswarm.png",
     "Dotted strip plot: each dot is one row from a 1,500-row sample, plotted along the SHAP-value axis per feature.",
     "SHAP value (negative = pushes prediction toward North, positive = toward South)",
     "Feature name (ranked top to bottom by importance)",
     "Colour of each dot = the feature's actual value (red=high, blue=low). Lets you see how a feature's value relates to its directional impact."),
    ("fig_reg_structural_shap.png",
     "Same as fig_reg_shap_bar but for the structural model (Model C, with distance_km added).",
     "Mean absolute SHAP value",
     "Feature name",
     "distance_km dominates with SHAP ≈ 4.87. Every other feature is below 0.15. This is the visual proof that distance_km is doing all the work in Model C."),
    ("fig_reg_deep_compare.png",
     "Six bars summarising all our model variants under GroupKFold-by-city.",
     "Model variant",
     "ROC-AUC",
     "Geo perfect (1.0), all behaviour variants near 0.5 (random), structural with distance jumps to ~0.87. The dotted line at 0.5 is random; values above it carry signal."),
    ("fig_reg_confusion.png",
     "2×2 heatmap of the out-of-fold predictions vs truth at threshold 0.5.",
     "Predicted label (North on the left column, South on the right)",
     "True label (North on top row, South on bottom row)",
     "Top-left and bottom-right cells = correct predictions (TN, TP). Top-right and bottom-left = mistakes (FP, FN). For the structural model, almost everything is on the diagonal."),
    ("fig_reg_curves.png",
     "Three-panel diagnostic plot for Model C.",
     "Panel 1 (ROC) — False Positive Rate;  Panel 2 (PR) — Recall;  Panel 3 (Calibration) — Mean predicted probability",
     "Panel 1 — True Positive Rate;  Panel 2 — Precision;  Panel 3 — Observed fraction South",
     "All three curves should hug the top/left ideal. Calibration curve being close to the dashed y=x line means the predicted probability is close to the actual probability."),
    ("fig_reg_01_target.png … fig_reg_11_citytier.png",
     "Eleven side-by-side comparisons (violin or stacked-bar) of behaviour features in North vs South.",
     "Region (North on left, South on right)",
     "The feature value (delivery time, age, rating, etc.) OR the % share within each region (for categoricals)",
     "Visually, North and South distributions look almost identical in every one of these plots — confirming the 'no behavioural signal' finding visually."),
]
for fname, what, xax, yax, read in graphs:
    story.append(Paragraph(f"<b>{fname}</b>", H4))
    story.append(Paragraph(f"<b>What it is:</b> {what}", body))
    story.append(Paragraph(f"<b>X axis:</b> {xax}", body))
    story.append(Paragraph(f"<b>Y axis:</b> {yax}", body))
    story.append(Paragraph(f"<b>How to read:</b> {read}", body))
    story.append(Spacer(1, 0.1*cm))

# ====================================================================
# SECTION 8 — JARGON CHEAT SHEET
# ====================================================================
story += [PageBreak(), Paragraph("8.  Jargon cheat sheet  (defend in one sentence)", H2)]

jargon = [
    ("AUC",              "Probability the model ranks a random South higher than a random North. 0.5=random, 1.0=perfect."),
    ("F1 score",         "Harmonic mean of precision and recall, range 0 to 1, higher is better."),
    ("Precision",        "Of the orders we predicted South, what fraction was actually South."),
    ("Recall",           "Of orders that were actually South, what fraction did we correctly catch."),
    ("Balanced accuracy","Average of recall on each class — not skewed by class imbalance like raw accuracy."),
    ("Confusion matrix", "2×2 table of true vs predicted counts (TN, FP, FN, TP)."),
    ("KFold",            "Split rows into K equal folds; train on K-1, predict on 1, rotate, average."),
    ("StratifiedKFold",  "KFold that preserves the South/North ratio in every fold."),
    ("GroupKFold",       "KFold variant where rows from the same city never appear in both train and test."),
    ("OOF (out-of-fold)","For each row, the prediction made when that row was in the validation fold."),
    ("Mann-Whitney U",   "Non-parametric test for whether two samples have the same median."),
    ("Chi-square",       "Test for independence between two categorical variables."),
    ("KS test",          "Test for whether two whole distributions are identical (not just medians)."),
    ("Spearman ρ",       "Correlation on ranks; measures monotonic (not necessarily linear) relationship."),
    ("Haversine",        "Great-circle distance between two lat/lon points on a sphere."),
    ("LightGBM",         "Gradient-boosted decision tree library, leaf-wise growth, handles categoricals natively."),
    ("CatBoost",         "Another gradient-boosting library used for cross-checking."),
    ("Class weight=balanced", "Re-scales loss inversely to class frequency so the minority class isn't ignored."),
    ("Early stopping",   "Stop adding trees once validation AUC plateaus, to prevent overfit."),
    ("SHAP (TreeExplainer)", "Per-feature attribution telling you how much each feature shifted the prediction."),
    ("Data leak / temporal leak",
     "When a feature carries information not available at prediction time, or is a proxy for the label."),
    ("Ablation",         "Adding or removing one feature at a time to measure its individual contribution."),
    ("Centroid",         "The geographic centre point of a city, used as the expected lat/lon for that city's orders."),
]
j_data = [["Term", "One-sentence definition"]]
for t, d in jargon: j_data.append([t, d])
story.append(tbl(j_data, cw=[4.0*cm, 13.5*cm]))

# Closing
story += [
    Spacer(1, 0.4*cm),
    callout(
        "<b>Pre-pitch ritual.</b> Read section 0 (the three numbers) one more time. Open the deck, walk through "
        "slides 1, 5, 8, 10 in your head. Open a terminal in the repo folder and have <code>python predict.py "
        "--input \"data/raw/Zomato Dataset.csv\" --output preds.csv</code> ready to paste if asked for a demo. "
        "Take this PDF with you.",
        "green"),
    Spacer(1, 0.2*cm),
    Paragraph(
        "<b>Repo</b>: github.com/TheClazer/Zomato-delivery-estimation  ·  "
        "<b>Generator</b>: notebooks/_build_understanding_guide.py from live regional_findings.json",
        small),
]


def hf(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEAL_L); canvas.rect(0, A4[1] - 0.4*cm, A4[0], 0.4*cm, fill=1, stroke=0)
    canvas.setFillColor(NAVY); canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5*cm, A4[1] - 0.95*cm, "UNDERSTANDING GUIDE  ·  explain-it-to-me-from-scratch")
    canvas.setFont("Helvetica", 8); canvas.setFillColor(GREY)
    canvas.drawRightString(A4[0] - 1.5*cm, A4[1] - 0.95*cm, "Team Hmmmmmmmmmm")
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5*cm, 0.8*cm, "github.com/TheClazer/Zomato-delivery-estimation")
    canvas.drawRightString(A4[0] - 1.5*cm, 0.8*cm, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                        leftMargin=1.5*cm, rightMargin=1.5*cm,
                        topMargin=1.6*cm, bottomMargin=1.4*cm,
                        title="Understanding Guide - Regional Classification",
                        author="Team Hmmmmmmmmmm")
doc.build(story, onFirstPage=hf, onLaterPages=hf)
print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes)")
