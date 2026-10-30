"""Visual multi-chart research reports for PDF, Word, and PowerPoint."""
from io import BytesIO
from xml.sax.saxutils import escape

def narrative(topic, stories, pred):
    paragraphs = [f"THE STORY | {topic}", "What the historical evidence reveals"]
    for s in stories:
        change = f"{s['pct']:+.1f}%" if s['pct'] is not None else "not available"
        paragraphs.append(f"{s['country']}: Between {s['start_year']} and {s['end_year']}, the observed measure moved from {s['first']:,.2f} to {s['last']:,.2f} ({change}). This describes an observed change, not its cause.")
    if pred is not None and not pred.empty:
        for country, g in pred.groupby("Country"):
            row = g.sort_values("Year").iloc[-1]
            paragraphs.append(f"OUTLOOK | {country}: {row['Year']} illustrative estimate {row['Value']:,.2f}, using {row['Method']} (historical holdout MAE {row['Holdout MAE']:,.2f}). Not a guaranteed outcome.")
    else:
        paragraphs.append("OUTLOOK | No projection was generated because the available annual history was insufficient.")
    return paragraphs

def charts(frame, pred, topic, unit):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pictures=[]
    def save(fig):
        b=BytesIO();fig.savefig(b,format="png",dpi=160,bbox_inches="tight",facecolor="white");plt.close(fig);pictures.append(b.getvalue())
    fig,ax=plt.subplots(figsize=(10,5))
    for name,g in frame.groupby("Country"):
        g=g.sort_values("Year");ax.plot(g["Year"],g["Value"],label=name,linewidth=2.5)
    ax.set(title=f"{topic} | The long view",xlabel="Year",ylabel=unit);ax.grid(alpha=.2);ax.legend();fig.tight_layout();save(fig)
    fig,ax=plt.subplots(figsize=(10,5))
    latest=frame.sort_values("Year").groupby("Country").tail(1)
    ax.bar(latest["Country"],latest["Value"]);ax.set(title="Where things stand | Latest observations",ylabel=unit)
    ax.tick_params(axis="x",labelrotation=20);fig.tight_layout();save(fig)
    if pred is not None and not pred.empty:
        fig,ax=plt.subplots(figsize=(10,5))
        for name,g in frame.groupby("Country"):
            g=g.sort_values("Year");ax.plot(g["Year"],g["Value"],label=f"{name} observed",linewidth=2)
        for name,g in pred.groupby("Country"):
            g=g.sort_values("Year");ax.plot(g["Year"],g["Value"],linestyle="--",marker="o",label=f"{name} illustrative forecast")
        ax.set(title="Looking ahead | Baseline scenarios, not certainty",xlabel="Year",ylabel=unit)
        ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout();save(fig)
    return pictures

def export_pdf(title, paragraphs, pictures, provenance, methods):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    out=BytesIO();doc=SimpleDocTemplate(out,pagesize=(612,792),leftMargin=48,rightMargin=48,topMargin=45,bottomMargin=45)
    styles=getSampleStyleSheet();flow=[Paragraph(escape(title),styles["Title"]),Spacer(1,15)]
    for paragraph in paragraphs:
        flow.extend([Paragraph(escape(paragraph),styles["BodyText"]),Spacer(1,10)])
    for i,pic in enumerate(pictures):
        flow.extend([Spacer(1,16),Image(BytesIO(pic),width=490,height=245),Spacer(1,12)])
    flow.extend([Paragraph("Evidence, methods and limitations",styles["Heading2"]),
                 Paragraph(escape(methods),styles["BodyText"]),Spacer(1,12),
                 Paragraph(escape("Source: "+provenance["url"]),styles["BodyText"]),
                 Paragraph(escape("Retrieved: "+provenance["retrieved_at"]),styles["BodyText"])])
    doc.build(flow);return out.getvalue()

def export_docx(title, paragraphs, pictures, provenance, methods):
    from docx import Document
    from docx.shared import Inches
    doc=Document();doc.add_heading(title,0)
    for p in paragraphs: doc.add_paragraph(p)
    for pic in pictures: doc.add_picture(BytesIO(pic),width=Inches(6.2))
    doc.add_heading("Evidence and methods",level=2);doc.add_paragraph(methods)
    doc.add_paragraph("Source: "+provenance["url"]);doc.add_paragraph("Retrieved: "+provenance["retrieved_at"])
    out=BytesIO();doc.save(out);return out.getvalue()

def export_pptx(title, paragraphs, pictures, provenance, methods):
    from pptx import Presentation
    from pptx.util import Inches,Pt
    prs=Presentation();prs.slide_width=Inches(13.33);prs.slide_height=Inches(7.5)
    def slide(title,body=None,picture=None):
        s=prs.slides.add_slide(prs.slide_layouts[6])
        box=s.shapes.add_textbox(Inches(.7),Inches(.4),Inches(12),Inches(.8))
        box.text_frame.text=title;box.text_frame.paragraphs[0].font.size=Pt(27)
        if picture: s.shapes.add_picture(BytesIO(picture),Inches(1),Inches(1.4),width=Inches(11))
        if body:
            box=s.shapes.add_textbox(Inches(.9),Inches(1.6),Inches(11.5),Inches(5.2))
            tf=box.text_frame;tf.word_wrap=True
            for i,p in enumerate(body):
                par=tf.paragraphs[0] if i==0 else tf.add_paragraph()
                par.text=p;par.font.size=Pt(18)
    slide(title,paragraphs[:3])
    for i,pic in enumerate(pictures):slide(["Historical trajectory","Current comparison","Forecast scenarios"][min(i,2)],picture=pic)
    slide("What the data tells us",paragraphs[2:])
    slide("Sources and methodology",[methods,"Source: "+provenance["url"],"Retrieved: "+provenance["retrieved_at"]])
    out=BytesIO();prs.save(out);return out.getvalue()
