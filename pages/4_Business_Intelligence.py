import streamlit as st
import pandas as pd
import plotly.express as px
from src.engine import read_dataset
from src.agent_core import plan_question, audit_frame, business_insights
from src.research import match_topic, fetch_world_bank, describe_trends, forecast_series
from src.story_report import narrative, charts, export_pdf, export_docx, export_pptx
from src.agent_ui import show_report

st.set_page_config(page_title="InsightFlow | Business Intelligence",page_icon="💼",layout="wide")
st.markdown("""<style>.block-container{max-width:1200px;padding-top:2rem}
.hero{padding:28px;border-radius:22px;background:linear-gradient(110deg,#152f49,#14635c);color:white}
.hero h1{color:white}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>💼 Business Intelligence</h1><p>Understand your market or analyze your own business performance.</p></div>',unsafe_allow_html=True)
question=st.text_area("What business decision are you exploring?",placeholder="How has unemployment changed in the United States? Or: Which product category generates the most revenue?")
st.caption("Ask your question first. InsightFlow selects a research route automatically; upload your own data only when you want to analyze private business metrics.")
show_report(question,"business","business_agent")
st.divider()
with st.expander("📂 Advanced: analyze a dataset or statistical indicator",expanded=False):
    source=st.radio("Data workflow",["Research only","Public market indicators","My business dataset"],horizontal=True)
if source=="Public market indicators":
    st.caption("Connected source: World Bank economic and demographic indicators. Other business providers are not connected yet.")
    st.page_link("pages/2_Research_Studio.py",label="Explore broader public research →",icon="🌐")
    if st.button("Investigate public market question",type="primary"):
        if not question.strip(): st.warning("Enter a question.")
        else:
            plan=plan_question(question,"business")
            st.session_state["business_plan"]=plan
            if not plan["topic"]:
                st.info("This question calls for a business feasibility study, not just one economic indicator. Here is a useful starting roadmap.")
                st.markdown("### Your business research roadmap")
                st.write(f"**Your question:** {question}")
                st.markdown("**1. Market demand:** Identify customer segments, local competitors, event types and seasonal demand.")
                st.markdown("**2. Business model:** Compare weddings, corporate events and private celebrations. Choose a niche and service scope.")
                st.markdown("**3. Unit economics:** Estimate revenue per event, vendor and venue costs, staffing, marketing and working capital.")
                st.markdown("**4. Local requirements:** Verify registration, taxes, contracts, insurance and applicable permits using authoritative local sources.")
                st.markdown("**5. Validation:** Interview customers, request supplier quotes and test a pilot before projecting demand.")
                st.caption("This is a research plan, not a completed market study. No unsupported market figures or regulatory claims are presented.")
                st.page_link("pages/2_Research_Studio.py",label="Explore related public indicators →")
            else:
                try:
                    with st.spinner("Collecting trusted market indicators…"):
                        frame,meta=fetch_world_bank(plan["topic"],plan["countries"])
                    st.session_state["business_public"]=(frame,meta,plan)
                except Exception as exc:st.error(f"Data retrieval failed: {exc}")
    if "business_public" in st.session_state:
        frame,meta,plan=st.session_state["business_public"]
        st.subheader("Market evidence")
        st.caption(f"Source: {meta['provider']} · Indicator: {meta['indicator']} · Retrieved: {meta['retrieved_at'][:10]}")
        st.plotly_chart(px.line(frame,x="Year",y="Value",color="Country",title=plan["topic"]),use_container_width=True)
        stories=describe_trends(frame,meta["unit"]);pred=forecast_series(frame)
        paragraphs=narrative(plan["topic"],stories,pred)
        for line in paragraphs[2:]:st.write(line)
        pictures=charts(frame,pred,plan["topic"],meta["unit"])
        methods="World Bank observations; descriptive trends. Exploratory forecasts compare naive and drift baselines using a chronological holdout and MAE. No causal inference or guaranteed projections."
        a,b,c=st.columns(3)
        a.download_button("📕 PDF",export_pdf(plan["topic"],paragraphs,pictures,meta,methods),file_name="market-research.pdf",mime="application/pdf")
        b.download_button("📘 Word",export_docx(plan["topic"],paragraphs,pictures,meta,methods),file_name="market-research.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        c.download_button("📽️ PowerPoint",export_pptx(plan["topic"],paragraphs,pictures,meta,methods),file_name="market-research.pptx",mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
elif source=="My business dataset":
    st.info("Upload only non-sensitive, appropriately shared business data. This prototype does not provide enterprise-grade access controls.")
    upload=st.file_uploader("Upload business CSV or Excel",type=["csv","xlsx","xls"])
    if upload:
        try:
            df=read_dataset(upload.name,upload.getvalue())
            audit=audit_frame(df)
            st.subheader("01 / Data quality")
            a,b,c=st.columns(3);a.metric("Rows",audit["rows"]);b.metric("Missing cells",audit["missing_cells"]);c.metric("Duplicate rows",audit["duplicate_rows"])
            with st.expander("Inspect source data"):st.dataframe(df.head(100),use_container_width=True)
            metrics=df.select_dtypes(include="number").columns.tolist()
            if not metrics:st.warning("The uploaded file has no numeric measures to analyze.");st.stop()
            metric=st.selectbox("Measure to analyze",metrics)
            dimension=st.selectbox("Compare by",["No grouping"]+[col for col in df.columns if col!=metric])
            if st.button("Build business analysis",type="primary"):
                if question.strip():st.session_state["business_plan"]=plan_question(question,"business")
                result=business_insights(df,metric,None if dimension=="No grouping" else dimension)
                st.session_state["business_result"]=(result,metric,dimension,upload.name)
            if "business_result" in st.session_state:
                result,m,d,name=st.session_state["business_result"]
                if name!=upload.name or m!=metric or d!=dimension:
                    st.info("Click Build business analysis to refresh the results for your current selection.")
                else:
                    st.subheader("02 / What the numbers reveal")
                    a,b,c=st.columns(3);a.metric("Total",f"{result['sum']:,.2f}");b.metric("Average",f"{result['average']:,.2f}");c.metric("Median",f"{result['median']:,.2f}")
                    st.write(f"Across {result['count']:,} valid records, {metric} totals {result['sum']:,.2f}. The observed average is {result['average']:,.2f} and median is {result['median']:,.2f}. These are descriptive findings, not causal conclusions.")
                    if "ranking" in result:
                        ranked=result["ranking"]
                        st.plotly_chart(px.bar(ranked,x=d,y=metric,title=f"{metric} by {d}"),use_container_width=True)
                        st.write(f"The largest aggregate {metric} belongs to {ranked.iloc[0][d]}. Aggregated totals can reflect differences in group size.")
                    st.subheader("03 / Evidence and next steps")
                    st.write("Investigate the largest and smallest groups, check for missing records, and compare equivalent time periods before making a business decision.")
                    st.download_button("Download analyzed data (CSV)",df.to_csv(index=False),file_name="business-analysis.csv",mime="text/csv")
                    st.caption("Business dataset reporting is currently descriptive; multi-chart PDF/Word/PowerPoint exports for uploaded data are a future enhancement.")
        except Exception as exc:st.error(f"Unable to analyze dataset: {exc}")
with st.expander("About the evidence"):
    st.write("Public market analysis uses available World Bank indicators. Uploaded business data is analyzed in the app session. Broader feasibility questions currently receive a structured research roadmap, not invented market statistics.")
    st.caption("Autonomous multi-source web research and LLM investigation are planned, not yet available.")
