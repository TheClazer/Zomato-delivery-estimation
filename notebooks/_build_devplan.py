"""Generate the developer plan PDF for the North vs South India regional
classification task (final deadline 18:30). Single self-contained PDF
saved to reports/dev_plan_regional.pdf."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether, ListFlowable, ListItem)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "dev_plan_regional.pdf"

NAVY = HexColor("#0A1F33")
NAVY_2 = HexColor("#12304A")
TEAL = HexColor("#0D9488")
TEAL_LIGHT = HexColor("#2DD4BF")
GOLD = HexColor("#F59E0B")
RED = HexColor("#DC2626")
GREEN = HexColor("#16A34A")
GREY = HexColor("#475569")
GREY_LIGHT = HexColor("#E2E8F0")


# --- styles ---------------------------------------------------------------
ss = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=22, leading=26,
                    textColor=NAVY, spaceBefore=4, spaceAfter=8,
                    fontName="Helvetica-Bold")
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=15, leading=19,
                    textColor=TEAL, spaceBefore=14, spaceAfter=6,
                    fontName="Helvetica-Bold")
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=12, leading=15,
                    textColor=NAVY, spaceBefore=8, spaceAfter=2,
                    fontName="Helvetica-Bold")
body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=10.5, leading=14,
                      textColor=HexColor("#1E293B"),
                      alignment=TA_JUSTIFY,
                      fontName="Helvetica", spaceAfter=4)
small = ParagraphStyle("small", parent=body, fontSize=9, leading=12,
                       textColor=GREY)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, bulletIndent=2,
                        spaceAfter=2)
code = ParagraphStyle("code", parent=body, fontName="Courier", fontSize=9,
                      leading=11, textColor=HexColor("#0F172A"),
                      backColor=HexColor("#F1F5F9"), leftIndent=8,
                      rightIndent=8, spaceBefore=2, spaceAfter=6,
                      borderPadding=4)
callout_style = ParagraphStyle("callout", parent=body, fontSize=10.5, leading=13,
                               textColor=NAVY, backColor=HexColor("#FEF3C7"),
                               borderColor=GOLD, borderWidth=0.8,
                               borderPadding=8, leftIndent=4, rightIndent=4,
                               spaceBefore=6, spaceAfter=8)


def bullets(items, style=bullet):
    return ListFlowable(
        [ListItem(Paragraph(t, style), leftIndent=10, bulletColor=TEAL,
                  value="●") for t in items],
        bulletType="bullet", start="bulletchar", leftIndent=10)


def styled_table(data, col_widths=None, header_bg=NAVY, header_fg=white,
                 alt_bg=HexColor("#F8FAFC")):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), header_fg),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for r in range(1, len(data)):
        if r % 2 == 0:
            style.append(("BACKGROUND", (0, r), (-1, r), alt_bg))
    t.setStyle(TableStyle(style))
    return t


def callout(text, color="gold"):
    """Yellow/teal/red callout box."""
    s = ParagraphStyle("co", parent=callout_style)
    if color == "teal":
        s.backColor = HexColor("#CCFBF1"); s.borderColor = TEAL
    elif color == "red":
        s.backColor = HexColor("#FEE2E2"); s.borderColor = RED
    elif color == "green":
        s.backColor = HexColor("#DCFCE7"); s.borderColor = GREEN
    return Paragraph(text, s)


# --- build the document ---------------------------------------------------

story = []

# Title block
story += [
    Spacer(1, 0.4 * cm),
    Paragraph("North vs South India — Regional Classification", H1),
    Paragraph(
        "Developer plan for the 18:30 deliverable  ·  Zomato Delivery dataset  ·  Team Hmmmmmmmmmm",
        ParagraphStyle("sub", parent=body, fontSize=11, textColor=TEAL,
                       fontName="Helvetica-Oblique", spaceAfter=10)),
]

# Executive summary callout
story.append(callout(
    "<b>Mission.</b> Classify each Zomato order as originating in <b>South India</b> (Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka) or <b>North India</b> (every other state), and surface the behavioural patterns that distinguish the two. We have <b>22 city codes</b> hidden in <code>Delivery_person_ID</code> giving us free ground-truth labels — no reverse geocoding needed. Target: a working classifier, a five-finding insights report, and a 10-slide pitch deck, all on GitHub by <b>18:30</b>."))

# Section 1: Data & label
story += [
    Paragraph("1. The data and how we label it", H2),
    Paragraph("The 'new' CSV in <code>Downloads/archive (2)/</code> is byte-identical to our existing <code>data/raw/Zomato Dataset.csv</code> — same 45,584 rows × 20 columns, same schema. No additional pivot signal arrived; instead, the <i>hidden</i> regional signal was always inside <code>Delivery_person_ID</code>.", body),
    Paragraph("1.1 City code extraction", H3),
    Paragraph("Each rider ID follows the pattern <code>{CITY}RES{##}DEL{##}</code>. A simple regex extracts the city prefix and gives us 22 unique cities.", body),
    Paragraph("<font face='Courier' size='9'>df['city_code'] = df['Delivery_person_ID'].str.extract(r'^([A-Z]+)RES', expand=False)</font>", code),
    Paragraph("1.2 City → state → region mapping", H3),
]

# City mapping table
city_data = [
    ["Code", "City", "State", "Region", "≈ Orders"],
    ["BANG", "Bangalore", "Karnataka", "South", "3,193"],
    ["HYD", "Hyderabad", "Telangana", "South", "3,179"],
    ["MYS", "Mysore", "Karnataka", "South", "3,170"],
    ["COIMB", "Coimbatore", "Tamil Nadu", "South", "3,169"],
    ["CHEN", "Chennai", "Tamil Nadu", "South", "3,144"],
    ["KOC", "Kochi", "Kerala", "South", "701"],
    ["JAP", "Jaipur", "Rajasthan", "North", "3,443"],
    ["RANCHI", "Ranchi", "Jharkhand", "North", "3,228"],
    ["SUR", "Surat", "Gujarat", "North", "3,187"],
    ["MUM", "Mumbai", "Maharashtra", "North", "3,173"],
    ["VAD", "Vadodara", "Gujarat", "North", "3,166"],
    ["INDO", "Indore", "Madhya Pradesh", "North", "3,158"],
    ["PUNE", "Pune", "Maharashtra", "North", "3,132"],
    ["AGR", "Agra", "Uttar Pradesh", "North", "763"],
    ["LUDH", "Ludhiana", "Punjab", "North", "758"],
    ["KNP", "Kanpur", "Uttar Pradesh", "North", "740"],
    ["ALH", "Allahabad", "Uttar Pradesh", "North", "740"],
    ["DEH", "Dehradun", "Uttarakhand", "North", "737"],
    ["GOA", "Goa", "Goa", "North", "709"],
    ["AURG", "Aurangabad", "Maharashtra", "North", "703"],
    ["KOL", "Kolkata", "West Bengal", "North", "700"],
    ["BHP", "Bhopal", "Madhya Pradesh", "North", "691"],
]
story.append(styled_table(city_data, col_widths=[1.6*cm, 3*cm, 4*cm, 2*cm, 2.2*cm]))
story.append(Spacer(1, 0.2 * cm))

# Class balance
story += [
    Paragraph("1.3 Class balance and base-rate", H3),
    Paragraph("Aggregating: <b>South ≈ 16,556 orders (36.3%)</b>  ·  <b>North ≈ 29,028 orders (63.7%)</b>. Class imbalance is mild — accuracy alone would be misleading at the 64% no-skill floor, so we will report <b>ROC-AUC, F1, and balanced accuracy</b> as primary metrics.", body),
    callout("<b>Sanity cross-check.</b> Each Restaurant_latitude / longitude already falls inside the bounding box of its mapped state for the city codes we recognise — so the lat/lon column is a valid <i>fallback</i> if a future row has an unknown prefix. We will keep it as a backup, not the primary label source.", "teal"),
]

# Section 2: Two-model strategy
story += [
    PageBreak(),
    Paragraph("2. Two-model strategy (the interesting twist)", H2),
    Paragraph("Lat/lon is a near-perfect predictor of region — a model with coordinates will hit 99%+ accuracy trivially. That is not the insight. The interesting question is:", body),
    callout("<b>Can we tell North apart from South orders WITHOUT looking at where the rider is?</b><br/>If yes, the dataset encodes regional behavioural patterns. If no, regions look operationally identical and the difference is purely geographic.", "gold"),
    Paragraph("So we train <b>two LightGBM binary classifiers</b> on the same 5-fold split:", body),
]

model_tbl = [
    ["", "Model A  —  GEO", "Model B  —  BEHAVIOUR"],
    ["Features",
     "Restaurant_lat, Restaurant_lon, Delivery_lat, Delivery_lon, distance_km",
     "Everything EXCEPT coordinates: weather, traffic, vehicle, prep_time, multi_deliveries, ratings, age, order type, festival, time-of-day, weekend, City (Metropolitan/Urban/Semi)"],
    ["Expected ROC-AUC", "≥ 0.99 (near-perfect)", "0.65 – 0.85 (the real number is the insight)"],
    ["Purpose",
     "Upper bound; sanity check on labels",
     "Reveals which non-geo features carry regional signal"],
    ["What we report",
     "1 line: 'geo-baseline 0.99X — labels are clean'",
     "Full SHAP analysis + per-feature regional effect-size table"],
]
story.append(styled_table(model_tbl,
                          col_widths=[2.5*cm, 6.5*cm, 6.5*cm]))

story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "The <b>gap between Model A and Model B AUC</b> is the headline number. A 0.99 vs 0.78 split would mean 'we can tell North from South ~80% of the time even with the map taken away' — that is the kind of finding judges remember.", body))

# Section 3: EDA / patterns to look for
story += [
    Paragraph("3. The pattern hunt — what we look for", H2),
    Paragraph("Before training, run a structured EDA contrasting the two regions across every column. Each test produces one row in the findings table.", body),
]

eda_tbl = [
    ["#", "Question", "Test", "Why it might split N/S"],
    ["F1", "Are delivery times longer in one region?",
     "Mann-Whitney U on Time_taken (min)",
     "Traffic culture, road quality, city density"],
    ["F2", "Does weather distribution differ?",
     "Chi-square on Weather_conditions",
     "South sees more Stormy/Fog (coastal); North more Sandstorms"],
    ["F3", "Different traffic patterns?",
     "Chi-square on Road_traffic_density",
     "Metro south (Bangalore/Chennai) is famously Jam-heavy"],
    ["F4", "Multi-delivery norms?",
     "Mann-Whitney on multiple_deliveries",
     "Rider concurrency varies with city density and policy"],
    ["F5", "Rider age skew?",
     "Mann-Whitney on Delivery_person_Age",
     "Cultural / labour-market demographics"],
    ["F6", "Rating skew?",
     "Mann-Whitney on Delivery_person_Ratings",
     "Different rating-inflation behaviour by region"],
    ["F7", "Vehicle preferences?",
     "Chi-square on Type_of_vehicle",
     "Scooter dominance in south, motorcycle in north?"],
    ["F8", "Order-type mix?",
     "Chi-square on Type_of_order",
     "Snack/Meal/Drinks/Buffet mix shifts with cuisine culture"],
    ["F9", "Festival impact differs?",
     "Welch t-test on Time_taken|Festival=Yes vs No, per region",
     "Diwali (north) vs Onam/Pongal (south) hit different weeks"],
    ["F10", "Time-of-day rhythm?",
     "KS test on order_hour distribution",
     "Dinner peak runs later in metro south; lunch rules in north"],
    ["F11", "City-tier mix?",
     "Chi-square on City (Metro/Urban/Semi)",
     "South sample is metro-heavy in our data"],
]
story.append(styled_table(eda_tbl,
                          col_widths=[1.0*cm, 4.5*cm, 4.0*cm, 6.5*cm]))

# Section 4: Pipeline
story += [
    PageBreak(),
    Paragraph("4. Implementation pipeline", H2),
    Paragraph("Eight files, all in the existing repo layout. Nothing new outside the established conventions.", body),
]
pipe_tbl = [
    ["#", "File", "Produces"],
    ["1", "src/regional.py", "extract_city_code(), map_to_region(), helpers"],
    ["2", "notebooks/_run_regional_eda.py",
     "regional_summary.json + fig_reg_01..11 PNGs (per-finding plot)"],
    ["3", "notebooks/_run_regional_models.py",
     "Trains Model A and Model B (5-fold KFold seed=42), saves AUC/F1/CM"],
    ["4", "notebooks/_run_regional_shap.py",
     "fig_reg_shap_beeswarm.png + fig_reg_shap_bar.png on Model B"],
    ["5", "notebooks/07_regional.ipynb",
     "Thin notebook wrapping the runners (judges open this first)"],
    ["6", "reports/regional_findings.json",
     "Per-test stat, p-value, effect size, verdict"],
    ["7", "reports/regional_models.json",
     "AUC/F1/accuracy per fold for both models"],
    ["8", "reports/dev_plan_regional.pdf",
     "THIS file (for the audit trail)"],
]
story.append(styled_table(pipe_tbl,
                          col_widths=[0.8*cm, 5.5*cm, 9.7*cm]))

story += [
    Spacer(1, 0.3*cm),
    Paragraph("4.1 The model contract (Rulebook §6 compliance)", H3),
    bullets([
        "<b>One source of cleaning</b> — reuse <code>src/data.py::load_clean</code>. Don't fork cleaning logic.",
        "<b>One feature builder</b> — reuse <code>src/features.py</code> for the engineered numeric/cat features.",
        "<b>One split</b> — <code>KFold(5, shuffle=True, random_state=42)</code>, same seed as the ETA work, so judges can verify deltas.",
        "<b>Two regressors → two classifiers</b> — swap <code>LGBMRegressor</code> for <code>LGBMClassifier</code>, objective='binary', metric='auc'.",
        "<b>No hard-coded results</b> — every number in the deck/PDF reads from JSON written by the runners.",
        "<b>Reproducibility</b> — model files saved as binary-safe .txt (already covered by <code>.gitattributes</code>).",
    ]),
]

# Section 5: Deck structure
story += [
    Paragraph("5. The 18:30 pitch deck (regional findings)", H2),
    Paragraph("New deck: <code>reports/pitch_regional_630pm.pptx</code> (+ PDF). 10 slides, navy + teal + gold theme to match the existing decks. Built from the same JSON-driven approach.", body),
]
deck_tbl = [
    ["#", "Slide", "Core content"],
    ["1", "Title", "Team chip + repo + the single headline AUC number"],
    ["2", "Mission", "Region definition (S = KL/TN/AP/TG/KA, N = rest) + class balance"],
    ["3", "Method — labels for free", "City-code extraction from Delivery_person_ID, 22-city table"],
    ["4", "Model A — geo baseline", "AUC ≈ 0.99, confusion matrix, 'labels are clean' callout"],
    ["5", "Model B — behaviour only", "AUC value as the centrepiece, SHAP bar, 5 top features"],
    ["6", "The gap", "Model A AUC vs Model B AUC — what survives the geography blackout"],
    ["7", "Pattern 1–3", "Three strongest non-geo findings (e.g. weather, traffic, time)"],
    ["8", "Pattern 4–5", "Two more (e.g. vehicle mix, order type)"],
    ["9", "Caveats + limitations", "Class imbalance, sample size per city, no temporal split"],
    ["10", "Q&A + repo", "github.com/TheClazer/...  +  final commit hash"],
]
story.append(styled_table(deck_tbl,
                          col_widths=[0.8*cm, 4.5*cm, 10.7*cm]))

# Section 6: Risk + timeline
story += [
    PageBreak(),
    Paragraph("6. Risk register", H2),
]
risk_tbl = [
    ["Risk", "Mitigation"],
    ["Model B AUC < 0.55 — almost no behavioural signal",
     "That IS the finding. Frame slide 6 as 'Behavioural patterns are nearly identical — the difference between North and South is purely geographic'. Honest > vanity (Rulebook §6 explicit guidance)."],
    ["A city code maps to wrong state",
     "Cross-validate every code by checking the median lat/lon of its rows falls inside the state's bounding box; flag and re-label any mismatch."],
    ["Hidden 23rd city code we missed",
     "<code>map_to_region()</code> falls back to lat/lon-based label for any unknown prefix; rows with no valid coord are dropped from training, never silently mislabelled."],
    ["Class imbalance distorts metrics",
     "Report ROC-AUC, balanced accuracy, and per-class F1 — not raw accuracy. Use <code>class_weight='balanced'</code> in LGBM."],
    ["Time pressure — 4 hours to 18:30",
     "Models are LightGBM 5-fold (~1 min each). 80% of the time goes to EDA plots + deck. Do NOT introduce new model families."],
    ["GitHub push fails at 18:25",
     "Same hotspot/zip-and-email fallback as the existing rulebook risk register."],
]
story.append(styled_table(risk_tbl, col_widths=[5.0*cm, 11.0*cm]))

story += [
    Spacer(1, 0.3*cm),
    Paragraph("7. Timeline (4 hours)", H2),
]
time_tbl = [
    ["Window", "Task"],
    ["14:30 – 14:50 (20m)", "src/regional.py + label sanity check via lat/lon bounding box cross-validation"],
    ["14:50 – 15:30 (40m)", "Regional EDA runner — 11 statistical tests + matched plots; write regional_findings.json"],
    ["15:30 – 16:00 (30m)", "Model A (geo) — 5-fold AUC, confusion matrix, save model + metrics"],
    ["16:00 – 16:40 (40m)", "Model B (behaviour) — same 5-fold, save SHAP plots"],
    ["16:40 – 17:00 (20m)", "Two-model comparison plot (AUC bar), feature-effect-size table"],
    ["17:00 – 17:30 (30m)", "Build pitch_regional_630pm.pptx, convert to PDF"],
    ["17:30 – 17:50 (20m)", "README update (regional section), commit, push, tag <code>regional-final</code>"],
    ["17:50 – 18:20 (30m)", "Dry-run + buffer for any last-minute fix"],
    ["18:20 – 18:30 (10m)", "Final upload + chat announcement"],
]
story.append(styled_table(time_tbl, col_widths=[3.5*cm, 12.5*cm]))

# Section 8: What we need from the user
story += [
    Paragraph("8. What we need from you (Rayyan)", H2),
    bullets([
        "<b>Sign off on the city-code → state mapping in §1.2.</b> If any of the 22 codes are wrong, fix here, not later.",
        "<b>Confirm the South definition.</b> You said Kerala, Tamil Nadu, Andhra, Telangana, Karnataka — Goa often gets folded into south coastal; the plan keeps it North per your spec. Say if you want it South.",
        "<b>Confirm the pitch substitution.</b> Should the 18:30 pitch <i>replace</i> the existing 18:00 ETA pitch, or be a <i>second</i> deck? Plan assumes second deck (<code>pitch_regional_630pm.pdf</code>); the ETA work stays untouched.",
        "<b>Confirm metric priority.</b> Plan reports AUC + F1 + balanced accuracy. Say if you want a different headline metric.",
    ]),
    callout("Once you reply with the four answers above (or just say 'looks good, proceed'), the runners and deck are ~3.5 hours of straight work and we make 18:30 comfortably.", "green"),
]

# Footer
story += [
    Spacer(1, 0.4*cm),
    Paragraph(
        "<b>Repo</b>: github.com/TheClazer/Zomato-delivery-estimation  ·  <b>Branch</b>: p1/pipeline  ·  <b>Document version</b>: v1, generated by <code>notebooks/_build_devplan.py</code> from live data exploration.",
        small),
]

# --- render ---------------------------------------------------------------

def header_footer(canvas, doc):
    canvas.saveState()
    # Top accent bar
    canvas.setFillColor(TEAL_LIGHT)
    canvas.rect(0, A4[1] - 0.4 * cm, A4[0], 0.4 * cm, fill=1, stroke=0)
    # Header text
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5 * cm, A4[1] - 0.95 * cm,
                      "DEVELOPER PLAN  ·  North vs South India Regional Classification")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawRightString(A4[0] - 1.5 * cm, A4[1] - 0.95 * cm,
                           "Team Hmmmmmmmmmm  ·  18:30 deadline")
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(1.5 * cm, 0.8 * cm,
                      "github.com/TheClazer/Zomato-delivery-estimation")
    canvas.drawRightString(A4[0] - 1.5 * cm, 0.8 * cm,
                           f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                        topMargin=1.6 * cm, bottomMargin=1.4 * cm,
                        title="Regional Classification Dev Plan",
                        author="Team Hmmmmmmmmmm")
doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes)")
