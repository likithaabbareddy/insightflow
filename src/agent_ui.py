"""Shared research report renderer for both user experiences."""
import streamlit as st
from src.web_agent import investigate
from src.service_health import show_health
from src.free_analysis import public_indicator
import pandas as pd
import plotly.express as px
from src.exports import pdf_bytes,docx_bytes,pptx_bytes

@st.cache_data(ttl=3600,show_spinner=False)
def run_investigation(question,mode,ai_mode):
    return investigate(question,mode,ai_mode)

def show_report(question: str,mode: str,key: str):
    ai_mode=st.radio("Research mode",["Free — source evidence","Automatic — use OpenAI when available"],horizontal=True,key=key+"_mode",help="Free mode uses Tavily search and source excerpts without calling OpenAI. Automatic mode uses OpenAI when available and falls back to excerpts if quota is exhausted.")
    if st.button("🔎 Investigate my question",type="primary",key=key):
        if not question.strip():st.warning("Enter a question first.")
        else:
            try:
                with st.spinner("Discovering sources, reading evidence and preparing your answer…"):
                    st.session_state[key+"_report"]=(question,run_investigation(question,mode,"free" if ai_mode.startswith("Free") else "auto"))
            except Exception as exc:
                import logging
                logging.exception("InsightFlow investigation failed")
                name=type(exc).__name__
                if name=="AuthenticationError":
                    detail="OpenAI authentication failed. Check your API key."
                elif name=="RateLimitError":
                    detail="API quota or rate limit reached. Check billing and usage."
                elif name=="NotFoundError":
                    detail="The configured AI model is unavailable."
                else:
                    detail="Research failed during retrieval or synthesis. Check diagnostics below."
                st.error(detail)
                st.caption("Error category: "+name+" (credentials are not displayed).")
    show_health()
    saved=st.session_state.get(key+"_report")
    if not saved or saved[0]!=question:return
    report=saved[1]
    st.markdown("""
    <style>
    .story-hero{padding:1.8rem 2rem;border-radius:20px;background:linear-gradient(120deg,#15334d,#115c61);color:white;margin:1rem 0 1.5rem}
    .story-kicker{font-size:.75rem;letter-spacing:.16em;text-transform:uppercase;color:#9de6e4;font-weight:700}
    .story-hero h2{color:white!important;margin:.5rem 0!important;line-height:1.25}
    .story-hero p{color:#e4f2f4;font-size:1.03rem}
    </style>
    """,unsafe_allow_html=True)
    import html
    title=html.escape(report["title"])
    summary=html.escape(report["summary"])
    st.markdown(f'<div class="story-hero"><div class="story-kicker">INSIGHTFLOW / RESEARCH BRIEFING</div><h2>{title}</h2><p>{summary}</p></div>',unsafe_allow_html=True)
    findings=report.get("findings",[])
    st.caption(f"Evidence-led presentation · {len(findings)} sourced highlights · charts shown only when verified data is available")
    chart=public_indicator(question)
    if chart:
        df=pd.DataFrame(chart["rows"]).sort_values("Year")
        first,last=df.iloc[0],df.iloc[-1]
        delta=last["Value"]-first["Value"]
        st.markdown("### 01 / The numbers behind the story")
        x,y,z=st.columns(3)
        x.metric("Latest observation",f"{last['Value']:,.1f}",help=chart["unit"])
        y.metric("First year",str(int(first["Year"])))
        z.metric("Change since first year",f"{delta:+,.1f}",help=f"Change in {chart['unit']}; not a growth rate")
        tab1,tab2=st.tabs(["📈 Long-term trend","📊 Year-by-year movement"])
        with tab1:
            fig=px.area(df,x="Year",y="Value",markers=True,labels={"Value":chart["unit"]},title=chart["title"])
            fig.update_layout(margin=dict(l=10,r=10,t=55,b=10),height=390)
            st.plotly_chart(fig,use_container_width=True)
        with tab2:
            changes=df.assign(Change=df["Value"].diff()).dropna(subset=["Change"])
            fig=px.bar(changes,x="Year",y="Change",labels={"Change":"Annual change ("+chart["unit"]+")"},title="How the indicator changed each year")
            fig.update_layout(margin=dict(l=10,r=10,t=55,b=10),height=390)
            st.plotly_chart(fig,use_container_width=True)
        st.markdown(f"**What the data shows:** Between {int(first['Year'])} and {int(last['Year'])}, this indicator moved from **{first['Value']:,.1f}** to **{last['Value']:,.1f}** ({chart['unit']}). This is a descriptive trend, not proof of why it changed.")
        st.caption(chart["note"])
        st.markdown("[Explore the original World Bank data]("+chart["source"]+")")
    else:
        st.info("No verified numerical series matched this question. A chart is not shown rather than inventing numbers.")
    st.markdown("### 02 / Evidence and the story")
    if findings:
        for index,finding in enumerate(findings):
            with st.container(border=True):
                col1,col2=st.columns([1,5])
                col1.markdown(f"## {index+1:02d}")
                with col2:
                    st.markdown("#### "+finding["heading"])
                    st.write(finding["text"])
                    st.markdown("**Verify:** "+", ".join(f"[Source {i+1}]({url})" for i,url in enumerate(finding.get("sources") or [finding["source"]])))
    else:
        st.warning("No question-specific statements were supported by retrieved sources.")
    st.markdown("### 03 / What this means for your decision")
    if report.get("intent")=="relocation and career":
        st.write("Before deciding on a move, compare verified job offers, immigration eligibility, take-home pay, housing, and healthcare. The chart above is context—not an estimate of your salary or living costs.")
    elif report.get("intent")=="business feasibility":
        st.write("Before investing, validate customer demand, competitor pricing, supplier costs, registration obligations and unit economics with local evidence. Broad economic indicators cannot establish demand for your specific business.")
    else:
        st.write("Use the sourced findings to identify what is known, then verify missing figures and assumptions before making a decision.")
    with st.expander("🔗 Sources, methodology and limitations"):
        if report.get("leads"):
            st.write("Additional starting points (not independently verified claims):")
            for lead in report["leads"]:
                st.markdown("- ["+lead["title"]+"]("+lead["url"]+")")
        st.write(report["limitations"])
        st.caption("Free mode selects source excerpts; it does not provide independent AI reasoning. Charts show observed data, not forecasts.")
    if not findings:
        st.caption("Report downloads require supported findings.")
        return
    st.markdown("### 04 / Take the briefing with you")
    lines=[report["title"],"Question: "+question,"",report["summary"],""]
    for f in report["findings"]:
        lines.extend([f["heading"],f["text"],"Source: "+f["source"],""])
    lines+=["Limitations",report["limitations"]]
    a,b,c=st.columns(3)
    a.download_button("📕 Download PDF",pdf_bytes(lines),file_name="insightflow-research.pdf",mime="application/pdf",key=key+"_pdf")
    b.download_button("📘 Download Word",docx_bytes(lines),file_name="insightflow-research.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",key=key+"_doc")
    c.download_button("📽️ Download PowerPoint",pptx_bytes(lines),file_name="insightflow-research.pptx",mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",key=key+"_ppt")
    st.caption("These qualitative research exports contain sourced text. Statistical charts are included only when supported numerical data is available through the indicator workflow.")
