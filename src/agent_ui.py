"""Shared research report renderer for both user experiences."""
import streamlit as st
from src.web_agent import investigate
from src.exports import pdf_bytes,docx_bytes,pptx_bytes

@st.cache_data(ttl=3600,show_spinner=False)
def run_investigation(question,mode):
    return investigate(question,mode)

def show_report(question: str,mode: str,key: str):
    if st.button("🔎 Investigate my question",type="primary",key=key):
        if not question.strip():st.warning("Enter a question first.")
        else:
            try:
                with st.spinner("Discovering sources, reading evidence and preparing your answer…"):
                    st.session_state[key+"_report"]=(question,run_investigation(question,mode))
            except Exception as exc:
                st.error("Research retrieval is temporarily unavailable. Please try again.")
                st.caption("No unsupported findings were generated.")
    saved=st.session_state.get(key+"_report")
    if not saved or saved[0]!=question:return
    report=saved[1]
    st.subheader(report["title"])
    st.write(report["summary"])
    for finding in report["findings"]:
        with st.container(border=True):
            st.markdown("### "+finding["heading"])
            st.write(finding["text"])
            st.markdown("**Evidence:** "+", ".join(f"[Source {i+1}]({url})" for i,url in enumerate(finding.get("sources") or [finding["source"]])))
    if report.get("leads"):
        st.markdown("### Official starting points")
        st.write("These are relevant official websites, not verified answers to the question.")
        for lead in report["leads"]:
            st.markdown("- [" + lead["title"] + "](" + lead["url"] + ")")
    st.info(report["limitations"])
    if not report["findings"]:
        st.warning("No supported answer was generated. Try a narrower question or check again when more sources are available.")
    if not report["findings"]:
        st.caption("Report downloads will appear when there is enough retrieved evidence to produce a substantive report.")
        return
    lines=[report["title"],"Question: "+question,"",report["summary"],""]
    for f in report["findings"]:
        lines.extend([f["heading"],f["text"],"Source: "+f["source"],""])
    lines+=["Limitations",report["limitations"]]
    a,b,c=st.columns(3)
    a.download_button("📕 Download PDF",pdf_bytes(lines),file_name="insightflow-research.pdf",mime="application/pdf",key=key+"_pdf")
    b.download_button("📘 Download Word",docx_bytes(lines),file_name="insightflow-research.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",key=key+"_doc")
    c.download_button("📽️ Download PowerPoint",pptx_bytes(lines),file_name="insightflow-research.pptx",mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",key=key+"_ppt")
    st.caption("These qualitative research exports contain sourced text. Statistical charts are included only when supported numerical data is available through the indicator workflow.")
