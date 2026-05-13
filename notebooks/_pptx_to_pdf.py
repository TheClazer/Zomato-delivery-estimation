"""Convert .pptx → .pdf via the installed PowerPoint COM interface.
Windows-only; falls back to a hint if PowerPoint isn't available.
"""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"

targets = [REPORTS / "eda_2pm.pptx", REPORTS / "pitch_6pm.pptx"]
for t in targets:
    if not t.exists():
        print(f"skip {t.name} (missing)")

try:
    import comtypes.client
except ImportError:
    print("comtypes not available — install with `pip install comtypes`")
    sys.exit(1)

ppt = comtypes.client.CreateObject("PowerPoint.Application")
try:
    for t in targets:
        if not t.exists():
            continue
        pdf = t.with_suffix(".pdf")
        deck = ppt.Presentations.Open(str(t), WithWindow=False)
        deck.SaveAs(str(pdf), 32)  # ppSaveAsPDF = 32
        deck.Close()
        print(f"wrote {pdf.relative_to(ROOT)}  ({pdf.stat().st_size:,} bytes)")
finally:
    ppt.Quit()
