"""Export a sourced research brief in PDF, DOCX or PPTX."""
from __future__ import annotations
from io import BytesIO
import pandas as pd

def report_lines(title: str, question: str, stories: list[dict], provenance: dict, methods: str) -> list[str]:
    lines = [title, "Research question: " + question, "",
             "Executive findings"]
    for s in stories:
        change = f"{s['pct']:+.1f}%" if s["pct"] is not None else "n/a"
        lines.append(f"{s['country']}: {s['first']:,.2f} ({s['start_year']}) to {s['last']:,.2f} ({s['end_year']}); change {change}.")
    lines += ["", "Methods and limitations", methods, "", "Data provenance",
              "Provider: " + provenance["provider"],
              "Indicator: " + provenance["indicator"], "Source: " + provenance["url"],
              "Retrieved (UTC): " + provenance["retrieved_at"],
              "Observed records: " + str(provenance["observations"])]
    return lines

def pdf_bytes(lines: list[str]) -> bytes:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.utils import simpleSplit
    from xml.sax.saxutils import escape
    out = BytesIO()
    doc = SimpleDocTemplate(out, rightMargin=48, leftMargin=48, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    flow = []
    for i, line in enumerate(lines):
        style = styles["Title"] if i == 0 else styles["BodyText"]
        flow.append(Paragraph(escape(line or " "), style))
        flow.append(Spacer(1, 9))
    doc.build(flow)
    return out.getvalue()

def docx_bytes(lines: list[str]) -> bytes:
    from docx import Document
    doc = Document()
    doc.add_heading(lines[0], 0)
    for line in lines[1:]:
        doc.add_paragraph(line)
    out = BytesIO()
    doc.save(out)
    return out.getvalue()

def pptx_bytes(lines: list[str]) -> bytes:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()
    chunks = [lines[1:5], lines[5:10], lines[10:]]
    for i, chunk in enumerate(chunks):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = lines[0] if i == 0 else ("Findings" if i == 1 else "Methods and sources")
        body = slide.placeholders[1].text_frame
        body.clear()
        for j, line in enumerate(chunk):
            p = body.paragraphs[0] if j == 0 else body.add_paragraph()
            p.text = line
            p.font.size = Pt(16)
    out = BytesIO()
    prs.save(out)
    return out.getvalue()
