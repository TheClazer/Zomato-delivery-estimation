"""reports/pitch_script.pdf — a clean 4-page speaking script for the
18:30 pitch. Tight, no jargon, verbatim 'SAY' lines + 'DO' actions +
mark-claiming moments highlighted."""
from pathlib import Path
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether)

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "reports" / "pitch_script.pdf"
D = json.load(open(ROOT / "reports" / "regional_findings.json"))

NAVY=HexColor("#0A1F33"); TEAL=HexColor("#0D9488")
TEAL_L=HexColor("#2DD4BF"); GOLD=HexColor("#D97706")
GREEN=HexColor("#16A34A"); GREY=HexColor("#475569")
RED=HexColor("#DC2626"); LIGHT=HexColor("#F1F5F9")

ss = getSampleStyleSheet()
TITLE=ParagraphStyle("T",parent=ss["Title"],fontSize=18,leading=22,textColor=NAVY,
                     fontName="Helvetica-Bold",spaceAfter=2,alignment=TA_LEFT)
SUB=ParagraphStyle("S",parent=ss["BodyText"],fontSize=10,leading=12,textColor=TEAL,
                   fontName="Helvetica-Oblique",spaceAfter=6,alignment=TA_LEFT)
SLIDE=ParagraphStyle("SLIDE",parent=ss["Heading2"],fontSize=12,leading=14,
                     textColor=NAVY,fontName="Helvetica-Bold",
                     spaceBefore=8,spaceAfter=3)
SPEAKER=ParagraphStyle("SP",parent=ss["BodyText"],fontSize=9,leading=11,
                       textColor=TEAL,fontName="Helvetica-Bold",
                       spaceAfter=2,alignment=TA_LEFT)
SAY=ParagraphStyle("SAY",parent=ss["BodyText"],fontSize=10,leading=13,
                   textColor=HexColor("#1E293B"),fontName="Helvetica",
                   alignment=TA_JUSTIFY,spaceAfter=2,
                   leftIndent=10)
DO=ParagraphStyle("DO",parent=ss["BodyText"],fontSize=9,leading=11,
                  textColor=GREY,fontName="Helvetica-Oblique",
                  spaceAfter=4,leftIndent=10)
MARK=ParagraphStyle("MARK",parent=ss["BodyText"],fontSize=9,leading=11,
                    textColor=GOLD,fontName="Helvetica-Bold",
                    spaceAfter=4,leftIndent=10)
body=ParagraphStyle("body",parent=ss["BodyText"],fontSize=10,leading=13,
                    textColor=HexColor("#1E293B"),fontName="Helvetica",
                    alignment=TA_JUSTIFY,spaceAfter=4)
small=ParagraphStyle("small",parent=body,fontSize=8.5,leading=11,textColor=GREY)


def slide_block(num_title, who, time_range, items):
    """items is list of tuples: ('SAY' or 'DO' or 'MARK', text)."""
    flow = [Paragraph(num_title, SLIDE),
            Paragraph(f"Speaker: {who}  ·  Time: {time_range}", SPEAKER)]
    for kind, text in items:
        if kind == "SAY":
            flow.append(Paragraph(f"<b>SAY  &gt;</b>  “{text}”", SAY))
        elif kind == "DO":
            flow.append(Paragraph(f"DO  &gt;  {text}", DO))
        else:
            flow.append(Paragraph(f"★ CLAIM &gt;  {text}", MARK))
    return KeepTogether(flow)


story = []

# ====================================================================
# PAGE 1 — Pre-pitch + opening (slides 1-3)
# ====================================================================
story.append(Paragraph("Pitch Script — 18:30 Final", TITLE))
story.append(Paragraph(
    "Team Hmmmmmmmmmm  ·  Regional Classification  ·  9-minute speak-time, 1-minute Q&A buffer  ·  "
    "Speakers: P3 = Ranadeep  ·  P1 = Rayyan  ·  P2 = Suchit",
    SUB))

# Pre-pitch checklist
story.append(Paragraph("Pre-pitch (do this in the 5 minutes before you walk in)", SLIDE))
story.append(Paragraph(
    "1. Laptop on projector. Open <b>reports/pitch_regional_630pm.pdf</b> full-screen.<br/>"
    "2. Open a terminal in the repo folder. Pre-type but DO NOT press enter:<br/>"
    "&nbsp;&nbsp;&nbsp;<font face='Courier' size='9'>python predict.py --input \"data/raw/Zomato Dataset.csv\" --output preds.csv</font><br/>"
    "3. Open <b>reports/qna_elite.pdf</b> on phone — Q&A safety net.<br/>"
    "4. Have <b>reports/judges_handout.pdf</b> printed or on phone — give one copy per judge after.<br/>"
    "5. Three numbers in your head: <b>0.51 · 0.91 · 1.00</b> (behaviour · structure · geography).",
    body))

# Slide 1
story.append(slide_block(
    "Slide 1 — TITLE (30 sec)",
    "P3 (Ranadeep)", "0:00 – 0:30",
    [("SAY", "Team Hmmmmmmmmmm. Three of us — Suchit, Rayyan, Ranadeep. Our task: classify each Zomato "
            "delivery as North or South Indian, find what makes the two regions different. We have one "
            "trained model, six independent stress tests defending the finding, and a single command that "
            "runs inference on any new dataset."),
     ("DO", "Click to slide 2. Do not pause."),
     ("MARK", "Establishes presence; lists all 4 deliverables (model, tests, CLI, deck) in the first 20 seconds.")]))

# Slide 2
story.append(slide_block(
    "Slide 2 — MISSION (45 sec)",
    "P3", "0:30 – 1:15",
    [("SAY", "South India per the brief means Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka. "
            "Everything else is North — Maharashtra, Gujarat, Goa, MP, Punjab, UP, the rest. We have 41,944 "
            "orders after cleaning. South is 16,397 of those — 39 percent. North is 25,547 — 61 percent. "
            "A mildly imbalanced binary classification."),
     ("SAY", "Metric: ROC-AUC. We also report F1 and balanced accuracy because raw accuracy would be "
            "misleading at the 61-percent no-skill floor."),
     ("DO", "Click to slide 3."),
     ("MARK", "Defines target, balance, and metric in 45 seconds. Honest acknowledgement of imbalance.")]))

# Slide 3
story.append(slide_block(
    "Slide 3 — METHOD: labels for free (45 sec)",
    "P3", "1:15 – 2:00",
    [("SAY", "Every Delivery_person_ID follows the pattern CITY-RES-DEL — for example KOC-RES-16-DEL-01 is "
            "Kochi, Kerala, South. A regex pulls the prefix, a 22-row dictionary maps it to state and region. "
            "No reverse-geocoding needed."),
     ("SAY", "Six South cities account for 16,500 orders. Sixteen North cities account for the rest."),
     ("DO", "Click to slide 4."),
     ("MARK", "Shows we mined the dataset itself for the ground truth — efficient, defensible.")]))

story.append(PageBreak())

# ====================================================================
# PAGE 2 — Middle (slides 4-7)
# ====================================================================
story.append(Paragraph("Pitch Script — page 2", TITLE))
story.append(Paragraph(
    "Mid-pitch  ·  slides 4 through 7  ·  this is the technical-rigor block",
    SUB))

# Slide 4
story.append(slide_block(
    "Slide 4 — SANITY CHECK (45 sec)",
    "P3 → hand to P1 (Rayyan)", "2:00 – 2:45",
    [("SAY", "We did not trust the city-code map blindly. For each of 22 cities we compared the "
            "median latitude and longitude of its orders to the expected city centroid. The worst city was "
            "Goa at 45 kilometres off centroid — well under our 250-kilometre tolerance. Nineteen out of 22 "
            "cities are within 7 kilometres."),
     ("SAY", "All 22 pass. The labels are clean before we train a single model."),
     ("DO", "Click to slide 5. Pass the mic to P1."),
     ("MARK", "Reproducibility + honesty. Judges see we audited our own data.")]))

# Slide 5
story.append(slide_block(
    "Slide 5 — MODEL A: the calibration baseline (45 sec)",
    "P1 (Rayyan)", "2:45 – 3:30",
    [("SAY", "Our first model uses only coordinate features — restaurant and delivery latitude and longitude "
            "plus haversine distance. 5-fold stratified cross-validation, seed 42. AUC equals 1.000 on every "
            "fold."),
     ("SAY", "This is expected, not impressive. We defined region by state, state is determined by "
            "coordinates, so a coordinate-only classifier gets it perfectly. AUC 1.000 is our proof that "
            "the labels are internally consistent — it is a sanity check, not a real predictive achievement."),
     ("DO", "Click to slide 6."),
     ("MARK", "Pre-empts the obvious 'isn’t 1.000 overfitting?' question by addressing it head-on.")]))

# Slide 6
story.append(slide_block(
    "Slide 6 — MODEL B: behaviour only, with a leak (60 sec)",
    "P1", "3:30 – 4:30",
    [("SAY", "Model B removes coordinates. We use 12 numeric and 6 categorical behaviour features — rider "
            "age and rating, weather, traffic, vehicle, prep time, peak-hour flags, order type, festival "
            "indicator, multi-delivery count, city tier."),
     ("SAY", "Mean AUC drops from 1.000 to 0.588. But when we ran SHAP, one feature dominated — month — "
            "with an importance ten times the next feature. That is suspicious. Months should not "
            "individually carry regional signal."),
     ("DO", "Click to slide 7."),
     ("MARK", "Shows we run interpretation tools, not just metrics.")]))

# Slide 7
story.append(slide_block(
    "Slide 7 — THE TEMPORAL LEAK (45 sec)",
    "P1", "4:30 – 5:15",
    [("SAY", "We checked the date ranges. Both regions span Feb 11 to April 6 2022 — identical. But "
            "within-region density differs sharply. February is 20.8 percent of North orders but only 4.3 "
            "percent of South orders. That is 4.8 times more representation in North. It is a "
            "data-collection-window artifact, not seasonality."),
     ("SAY", "Month was a region proxy, not a real behavioural signal. We dropped month and day-of-week, "
            "retrained — Model B prime."),
     ("DO", "Click to slide 8. Stay on the mic for slide 8."),
     ("MARK", "Catches our own data quality issue, fixes it. This is the rigor mark.")]))

story.append(PageBreak())

# ====================================================================
# PAGE 3 — End + Live demo (slides 8-10)
# ====================================================================
story.append(Paragraph("Pitch Script — page 3", TITLE))
story.append(Paragraph(
    "Close-out  ·  slides 8, 9, 10 + the live model demo + handover",
    SUB))

# Slide 8
story.append(slide_block(
    "Slide 8 — MODEL B PRIME: the honest answer (45 sec)",
    "P1", "5:15 – 6:00",
    [("SAY", "Model B prime with month dropped. AUC = 0.508 across 5 folds — within Monte Carlo noise of "
            "0.500. Two folds were exactly 0.500 — the model literally is guessing."),
     ("SAY", "This is the headline of Layer 1: Zomato's operational behaviour — riders, customers, weather "
            "impact, traffic patterns, vehicle choice, festival effect — is statistically uniform across "
            "India in this dataset."),
     ("DO", "Click to slide 9. Hand mic to P2 (Suchit)."),
     ("MARK", "Demonstrates we report negative findings honestly.")]))

# Slide 9
story.append(slide_block(
    "Slide 9 — THE DEEP DIVE: six stress tests (75 sec)",
    "P2 (Suchit)", "6:00 – 7:15",
    [("SAY", "A negative finding is easy to dismiss. We attacked it six ways."),
     ("SAY", "First: KS distribution-shape on every numeric column. Only one — distance_km — is "
            "significant, with p around 10 to the minus 67. Second: dispersion ratios — south_std over "
            "north_std all between 0.98 and 1.04. No variance difference. Third: five engineered "
            "interaction features — only distance-derived ones lifted AUC. Fourth: GroupKFold by city — "
            "train on some cities, test on others. Behaviour-only stayed at 0.506 random. Fifth: a "
            "per-South-state classifier returned 38 percent accuracy versus 25 percent random — South "
            "India is weakly internally heterogeneous, which explains a single fold drop we report "
            "honestly. Sixth: CatBoost cross-check, AUC 0.507 — within 0.001 of LightGBM. Not a framework "
            "artifact."),
     ("SAY", "Five tests confirm behaviour is uniform. One — distance_km — reveals the hidden pattern."),
     ("DO", "Click to slide 10. Stay on mic."),
     ("MARK", "Sixfold robustness. This single slide carries the technical-rigor case.")]))

# Slide 10
story.append(slide_block(
    "Slide 10 — THE FINAL FINDING: three layers (75 sec)",
    "P2", "7:15 – 8:30",
    [("SAY", "Layer 1 — Behaviour: AUC 0.51. Operationally identical across India."),
     ("SAY", "Layer 2 — Structure: AUC 0.91 under GroupKFold-by-city. Adding only the haversine pickup-to-"
            "drop distance lifts AUC to 0.91 — even on cities the model has never seen. Distance distributions "
            "differ in shape, not median. South cities have a structurally different layout of restaurants "
            "relative to customers than North cities. This is urban geometry, not behaviour."),
     ("SAY", "Layer 3 — Geography: AUC 1.00. Raw coordinates are perfectly separable by construction."),
     ("SAY", "So the finding is: Zomato runs uniformly across India. Riders behave the same way, customers "
            "order the same way, the operation is regionally invariant. The only thing that differs is the "
            "geometric fingerprint of the city itself."),
     ("DO", "Pass mic back to P1 (Rayyan) for the live demo."),
     ("MARK", "Three-layer narrative — clean memorable arc. The handout has it printed.")]))

# Live demo
story.append(slide_block(
    "Live demo (45 sec)",
    "P1", "8:30 – 9:15",
    [("SAY", "Our model is on disk. Let me load it and run it on the dataset in front of you."),
     ("DO", "Switch to the terminal. Run: python predict.py --input \"data/raw/Zomato Dataset.csv\" "
            "--output preds.csv. Wait 4 seconds."),
     ("SAY", "Forty-one thousand rows, four seconds, ten thousand rows per second, AUC 0.9985 against "
            "the embedded ground truth. The model is a 1.9 MB LightGBM booster — 276 trees. Single command, "
            "no GPU, runs on a laptop. That is adaptability — give us any Zomato-schema CSV, get predictions."),
     ("DO", "Switch back to the deck. Hand judges the handout."),
     ("MARK", "ADAPTABILITY mark earned right here. Tangible, runnable, measurable.")]))

# Q&A handover
story.append(slide_block(
    "Handover (15 sec)",
    "P3 closes", "9:15 – 9:30",
    [("SAY", "That is our submission. Repo is on GitHub, tag is on the handout. We are happy to take "
            "questions."),
     ("DO", "Sit down. Open qna_elite.pdf on phone discreetly under the desk.")]))

story.append(PageBreak())

# ====================================================================
# PAGE 4 — Q&A handling + mark-claiming + 5 numbers
# ====================================================================
story.append(Paragraph("Pitch Script — page 4 (Q&A handling)", TITLE))
story.append(Paragraph(
    "How to answer the seven questions you are most likely to get.  ·  Section IDs reference qna_elite.pdf",
    SUB))

qa = [
    ("Q1. Where is your model?",
     "P1", "Open File Explorer or the GitHub repo. Point at "
           "models/region_classifier_v2_structural.txt. 1.9 MB, 276 trees, loads in under 100 ms."),
    ("Q2. Why is GEO AUC = 1.0? Isn't that overfitting?",
     "P1", "AUC 1.0 here proves the labels are clean. Region was defined by state, which is determined by "
           "coordinates. So a model trained on coordinates can recover region perfectly. This is the data "
           "being internally consistent, not the model being good. Models B prime and C are the interesting ones."),
    ("Q3. Why did you drop month from the features?",
     "P1", "Within-region month percentages differ sharply even though calendar dates are identical. "
           "February is 20.8 percent of North but 4.3 percent of South. That is a data-collection-window "
           "artifact, not seasonality. Including month would let the model use it as a region proxy and "
           "inflate AUC dishonestly."),
    ("Q4. How do you know it isn't a LightGBM artifact?",
     "P2", "We ran the same task with CatBoost — an independent gradient-boosting library. AUC = 0.507 vs "
           "LightGBM 0.508. Within 0.001. Not framework-specific."),
    ("Q5. Could there be a pattern you missed?",
     "P2", "Six stress tests aligned. KS shape, dispersion, interaction ablation, GroupKFold by city, "
           "per-South-state classifier, CatBoost cross-check. Five say behaviour is uniform. One — distance — "
           "says structure differs. We attacked the negative finding from six angles; one survived. That is "
           "the pattern."),
    ("Q6. Why did one GroupKFold fold drop to 0.64?",
     "P2", "Fold 4 held both Kochi and Hyderabad — Kerala plus Telangana. Our remaining South training "
           "cities were all Karnataka and Tamil Nadu. The model learned the Karnataka-TN distance profile "
           "and did not fully generalise to Kerala plus Telangana. We report this honestly — it tells us "
           "South India is internally heterogeneous, confirmed by the per-state classifier."),
    ("Q7. Could the system handle a new dataset?",
     "P1", "Yes — that is what predict.py does. Any CSV with the Zomato schema, single command, 4 seconds. "
           "If a new city appears with an unknown prefix, the lat/lon bounding-box fallback labels it "
           "automatically. If the region definition changes, it is a one-line edit. Every PDF and slide "
           "rebuilds from JSON."),
]
qa_tbl = [["Question", "Who answers", "Answer"]]
for q, who, a in qa:
    qa_tbl.append([q, who, a])
t = Table(qa_tbl, colWidths=[5.0*cm, 1.6*cm, 11.0*cm])
t.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),
    ("GRID",(0,0),(-1,-1),0.3,HexColor("#CBD5E1")),
    ("VALIGN",(0,0),(-1,-1),"TOP")]))
for r in range(1, len(qa_tbl)):
    if r % 2 == 0:
        t.setStyle(TableStyle([("BACKGROUND",(0,r),(-1,r),HexColor("#F8FAFC"))]))
story.append(t)

story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("The five numbers you must say without hesitation", SLIDE))
nums = [
    ["#", "Number", "What it means"],
    ["1", "0.51",  "behaviour-only AUC — Zomato is operationally uniform across India"],
    ["2", "0.91",  "structural AUC under GroupKFold — geometry differs"],
    ["3", "1.00",  "GEO AUC — labels are clean (by construction)"],
    ["4", "0.088", "KS distribution-shape statistic on distance — the only behaviour-style column that differs"],
    ["5", "10⁻⁶⁷", "p-value on that KS — distance distributions are unmistakably different"],
]
t2 = Table(nums, colWidths=[0.8*cm, 2.5*cm, 13.5*cm])
t2.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9.5),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),
    ("GRID",(0,0),(-1,-1),0.3,HexColor("#CBD5E1")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("FONTNAME",(1,1),(1,-1),"Helvetica-Bold"),
    ("TEXTCOLOR",(1,1),(1,-1),TEAL)]))
story.append(t2)

story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("Mark-claiming summary  (where in the pitch you earn each 10/10)", SLIDE))
mc = [
    ["Criterion", "Earned at", "What the judges see"],
    ["1. Model + technical rigor", "Slides 5–9",
     "Three models, 5-fold StratifiedKFold seed 42, GroupKFold, SHAP, six stress tests, CatBoost cross-check"],
    ["2. Adaptability", "Live demo at 8:30",
     "predict.py runs in 4 seconds at 10,000 rows/sec on any Zomato CSV — concrete production demo"],
    ["3. Understanding", "Slides 7 and 9 + Q&A",
     "Catches own data leak (month), defends every line, four backing PDFs, plain-English explanations"],
    ["4. Presentation", "Entire deck + handout",
     "10 slides, live numbers, three-layer narrative, single-page leave-behind, no [VALUE] placeholders"],
]
t3 = Table(mc, colWidths=[4.0*cm, 2.5*cm, 10.3*cm])
t3.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),
    ("GRID",(0,0),(-1,-1),0.3,HexColor("#CBD5E1")),
    ("VALIGN",(0,0),(-1,-1),"TOP")]))
story.append(t3)

story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "<b>One final reminder.</b> If a question stumps you, say “great question, let me defer to "
    "[P1/P2/P3]” — do NOT make something up. The qna_elite.pdf on your phone has 45+ Q&A pairs "
    "for the gnarly ones. Take the question, breathe, then answer in one sentence. Honesty over "
    "completeness.",
    body))


def hf(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEAL_L); canvas.rect(0, A4[1] - 0.3*cm, A4[0], 0.3*cm, fill=1, stroke=0)
    canvas.setFillColor(NAVY); canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(1.2*cm, 0.6*cm, "Team Hmmmmmmmmmm  ·  18:30 pitch script")
    canvas.setFillColor(GREY); canvas.setFont("Helvetica", 8)
    canvas.drawRightString(A4[0] - 1.2*cm, 0.6*cm,
                           f"Page {doc.page}  ·  github.com/TheClazer/Zomato-delivery-estimation")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                        leftMargin=1.3*cm, rightMargin=1.3*cm,
                        topMargin=0.9*cm, bottomMargin=1.0*cm,
                        title="Pitch Script - Regional Classification",
                        author="Team Hmmmmmmmmmm")
doc.build(story, onFirstPage=hf, onLaterPages=hf)
print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes)")
