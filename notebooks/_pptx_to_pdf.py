"""Convert .pptx → .pdf via the installed PowerPoint COM interface.
Windows-only. Newer Office builds (Microsoft 365) reject WithWindow=False
silently, so we open with a real window then close immediately.
"""
import os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"

targets = [REPORTS / "eda_2pm.pptx", REPORTS / "pitch_6pm.pptx"]
for t in targets:
    if not t.exists():
        print(f"skip {t.name} (missing)")

import comtypes.client

ppt = comtypes.client.CreateObject("PowerPoint.Application")
# Cannot set Visible=False in newer Office — leave default and let it briefly show
try:
    for t in targets:
        if not t.exists():
            continue
        pdf = t.with_suffix(".pdf")
        deck = ppt.Presentations.Open(str(t.resolve()))
        deck.SaveAs(str(pdf.resolve()), 32)  # ppSaveAsPDF = 32
        deck.Close()
        print(f"wrote {pdf.relative_to(ROOT)}  ({pdf.stat().st_size:,} bytes)")
        time.sleep(0.2)
finally:
    try:
        ppt.Quit()
    except Exception:
        pass
