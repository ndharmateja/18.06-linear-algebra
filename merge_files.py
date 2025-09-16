#!/usr/bin/env python3
"""
merge_sessions_with_dot.py

==============================================================
📘 PURPOSE
--------------------------------------------------------------
This script merges session PDFs into a single combined PDF with
the following rules:

1. Input folders:
   - Summary PDFs are located in:      lecturenotes/
   - Problem PDFs are located in:      problemsets/
   Each file must be named like: Ses1.1sum.pdf or Ses1.1prob.pdf

2. For each session:
   - First include the `sum` PDF (if missing, skip the session).
   - Then include the `prob` PDF (if it exists).
   - In each file, the **last page is dropped**.

3. Page count rule:
   - Each session’s pages (sum + prob) must be **even**.
   - If odd, a filler page is added (with a tiny "." so printers won’t skip it).

4. Output file:
   - The merged document is saved as merged.pdf

==============================================================
"""

import io
import os
import re

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# -------------------------------------------------------------
# Helper function: create a single-page PDF with a visible "."
# -------------------------------------------------------------
def create_dot_page(width_pts, height_pts):
    """
    Create a one-page PDF in memory (BytesIO) that has a small black dot.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width_pts, height_pts))
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(20, 20, ".")
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# -------------------------------------------------------------
# STEP 1: Collect session files from two folders
# -------------------------------------------------------------
pattern = re.compile(r"Ses(\d+\.\d+)(sum|prob)\.pdf", re.IGNORECASE)


def collect_files_from(folder):
    """Return {session_number: filepath} for all PDFs in a folder."""
    mapping = {}
    if not os.path.isdir(folder):
        return mapping
    for f in os.listdir(folder):
        m = pattern.match(f)
        if not m:
            continue
        sesnum, kind = m.groups()
        kind = kind.lower()
        mapping.setdefault(sesnum, {})[kind] = os.path.join(folder, f)
    return mapping


# Collect summaries and problems separately
sessions = {}
sum_files = collect_files_from("lecturenotes")
prob_files = collect_files_from("problemsets")

# Merge dictionaries: sessions = { "1.1": {"sum": "...", "prob": "..."} }
for sesnum, entry in sum_files.items():
    sessions.setdefault(sesnum, {}).update(entry)
for sesnum, entry in prob_files.items():
    sessions.setdefault(sesnum, {}).update(entry)

if not sessions:
    print("No Ses*.pdf files found in 'lecturenotes/' or 'problemsets/'. Exiting.")
    raise SystemExit(1)

# -------------------------------------------------------------
# STEP 2: Merge PDFs according to constraints
# -------------------------------------------------------------
out = PdfWriter()

for ses in sorted(sessions.keys(), key=lambda s: [int(x) for x in s.split(".")]):
    pair = sessions[ses]
    print(f"\n📘 Processing Session {ses}")

    page_width = None
    page_height = None
    start_page_count = len(out.pages)

    # ----- Include SUM first -----
    if "sum" in pair:
        sum_file = pair["sum"]
        print(f"   ✅ SUM: {sum_file}")
        r = PdfReader(sum_file)

        # Get page size from first page
        if len(r.pages) > 0:
            p0 = r.pages[0]
            page_width = float(p0.mediabox.width)
            page_height = float(p0.mediabox.height)

        # Copy all pages except last
        for i in range(max(0, len(r.pages) - 1)):
            out.add_page(r.pages[i])
    else:
        print("   ❌ SUM missing for this session. Skipping session.")
        continue

    # ----- Include PROB if exists -----
    if "prob" in pair:
        prob_file = pair["prob"]
        print(f"   ✅ PROB: {prob_file}")
        r = PdfReader(prob_file)

        if page_width is None and len(r.pages) > 0:
            p0 = r.pages[0]
            page_width = float(p0.mediabox.width)
            page_height = float(p0.mediabox.height)

        for i in range(max(0, len(r.pages) - 1)):
            out.add_page(r.pages[i])
    else:
        print("   ⚠️ PROB missing for this session.")

    # ----- Ensure even number of pages -----
    pages_added = len(out.pages) - start_page_count
    if pages_added % 2 != 0:
        if page_width is None or page_height is None:
            page_width, page_height = A4
        print("   ➕ Adding filler page with a '.' to make page count even.")
        filler_page = create_dot_page(page_width, page_height)
        out.add_page(filler_page)

# -------------------------------------------------------------
# STEP 3: Save final merged output
# -------------------------------------------------------------
out_path = "merged.pdf"
with open(out_path, "wb") as fo:
    out.write(fo)

print(f"\n✅ Done. Merged PDF saved to {out_path}")
