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

def chart_png(frame: pd.DataFrame, title: str, unit: str) -> bytes:
    """Create an export-friendly chart from observed data, without requiring browser screenshots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    for country, group in frame.groupby("Country"):
        group = group.sort_values("Year")
        ax.plot(group["Year"], group["Value"], label=country, linewidth=2.2)
    ax.set_title(title, fontsize=16, weight="bold", loc="left")
    ax.set_xlabel("Year")
    ax.set_ylabel(unit)
    ax.grid(alpha=.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    out=BytesIO()
    fig.savefig(out,format="png",dpi=170,bbox_inches="tight")
    plt.close(fig)
    return out.getvalue()

def pdf_with_chart(lines: list[str], chart: bytes) -> bytes:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from xml.sax.saxutils import escape
    out=BytesIO()
    doc=SimpleDocTemplate(out,rightMargin=48,leftMargin=48)
    styles=getSampleStyleSheet()
    flow=[]
    for i,line in enumerate(lines):
        flow.append(Paragraph(escape(line or " "),styles["Title"] if i==0 else styles["BodyText"]))
        flow.append(Spacer(1,9))
        if i==3:
            flow.append(Image(BytesIO(chart),width=475,height=238))
            flow.append(Spacer(1,12))
    doc.build(flow)
    return out.getvalue()

def docx_with_chart(lines: list[str], chart: bytes) -> bytes:
    from docx import Document
    from docx.shared import Inches
    doc=Document()
    doc.add_heading(lines[0],0)
    for i,line in enumerate(lines[1:]):
        doc.add_paragraph(line)
        if i==2: doc.add_picture(BytesIO(chart),width=Inches(6.1))
    out=BytesIO()
    doc.save(out)
    return out.getvalue()

def pptx_with_chart(lines: list[str], chart: bytes) -> bytes:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs=Presentation()
    slide=prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text=lines[0]
    slide.shapes.add_picture(BytesIO(chart), Inches(.8), Inches(1.5), width=Inches(8.4))
    for heading,items in [("Executive findings",lines[3:7]),("Methods and sources",lines[7:])]:
        slide=prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text=heading
        tf=slide.placeholders[1].text_frame
        tf.clear()
        for i,item in enumerate(items):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
            p.text=item
            p.font.size=Pt(15)
    out=BytesIO()
    prs.save(out)
    return out.getvalue()
