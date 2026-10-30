import streamlit as st
import pandas as pd
import plotly.express as px
from src.research import CATALOG, COUNTRIES, match_topic, infer_countries, fetch_world_bank, describe_trends, forecast_series, discover_indicators, fetch_discovered_indicator
from src.story_report import narrative, charts, export_pdf, export_docx, export_pptx
from src.question_guidance import guidance

st.set_page_config(page_title="Research Studio | InsightFlow", page_icon="🌐", layout="wide")
st.markdown("""<style>
.block-container{max-width:1240px;padding-top:2rem}
[data-testid="stMetric"]{background:#14253b;border:1px solid #30465e;border-radius:16px;padding:14px}
h1,h2,h3{letter-spacing:-.035em}
.hero{padding:30px;border-radius:22px;background:linear-gradient(120deg,#162b47,#135a63);color:white;margin-bottom:20px}
.hero h1{color:white;margin:0}.hero p{color:#d7f3f5}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🌐 Research Studio</h1><p>Ask a question. Explore trusted public data. Discover the story behind the numbers.</p></div>', unsafe_allow_html=True)
question = st.text_input("What do you want to understand?", placeholder="How has life expectancy changed in India and the United States over 40 years?")
suggested = match_topic(question)
with st.expander("⚙️ Optional research controls", expanded=False):
    years = st.slider("Years of history", 10, 60, 40, step=5)
    default_countries = infer_countries(question) if question else ["USA", "IND", "CHN"]
    countries = st.multiselect("Countries to compare", list(COUNTRIES.values()), default=default_countries)
    st.caption("These controls are optional. You can simply enter a question and press Research.")
st.caption("Start with a question — no topic dropdown required. We search the connected indicator catalog when needed.")
run = st.button("✨ Research my question", type="primary", use_container_width=True)
@st.cache_data(ttl=21600, show_spinner=False)
def load(topic, codes): return fetch_world_bank(topic, list(codes))
@st.cache_data(ttl=21600, show_spinner=False)
def find_indicators(q): return discover_indicators(q)
@st.cache_data(ttl=21600, show_spinner=False)
def load_discovered(code, codes): return fetch_discovered_indicator(code, list(codes))
if run:
    st.session_state.pop("research_result", None)
    st.session_state.pop("research_candidates", None)
    st.session_state.pop("research_guide", None)
    if not question.strip():
        st.info("Enter a research question to begin.")
    elif not countries:
        st.error("Choose at least one country in optional controls.")
    elif suggested:
        try:
            with st.spinner("Collecting verified observations…"):
                frame, provenance = load(suggested, tuple(countries))
            st.session_state["research_result"] = (suggested, question, frame, provenance, years)
        except Exception as exc: st.error(f"Data collection failed: {exc}")
    else:
        st.session_state["research_guide"] = (question, guidance(question))
if "research_guide" in st.session_state and "research_result" not in st.session_state:
    asked, guide = st.session_state["research_guide"]
    if asked == question:
        st.subheader(guide["title"])
        st.write(guide["intro"])
        for heading, body in guide["sections"]:
            st.markdown("#### " + heading)
            st.write(body)
        st.warning(guide["limitations"])
if "research_result" not in st.session_state:
    st.info("Ask any question to search our connected World Bank indicator catalog. Coverage is broader than the five curated topics, but not yet the entire internet.")
    st.stop()
topic, question, frame, provenance, years = st.session_state["research_result"]
last_year = int(frame["Year"].max())
frame = frame[frame["Year"] >= last_year-years+1].copy()
if frame.empty: st.warning("No observations for this period."); st.stop()
unit = provenance["unit"]
stories = describe_trends(frame, unit)
st.caption(f"Verified provider: {provenance['provider']} · Indicator: {provenance['indicator']} · Retrieved: {provenance['retrieved_at'][:10]} · Available through {last_year}")
st.subheader("01 / The big picture")
a,b,c = st.columns(3)
a.metric("Countries compared", frame["Country"].nunique())
b.metric("Years in scope", f"{int(frame['Year'].min())}–{int(frame['Year'].max())}")
c.metric("Observations", f"{len(frame):,}")
st.plotly_chart(px.line(frame, x="Year", y="Value", color="Country", markers=False,
                        title=f"{topic} — historical trajectories", labels={"Value":unit},
                        template="plotly_dark"), use_container_width=True)
st.subheader("02 / What changed?")
st.markdown("### The story behind the curve")
st.write("Each line traces observed change over time. Compare the beginning and end of the period, then look for turning points, sustained rises or declines, and differences between countries. A visual relationship does not establish a cause.")
for s in stories:
    change = f"{s['pct']:+.1f}%" if s["pct"] is not None else "not measurable as a percentage"
    st.markdown(f"**{s['country']}** moved from **{s['first']:,.2f}** in {s['start_year']} to **{s['last']:,.2f}** in {s['end_year']} ({change}). This is an observed change, not evidence of causation.")
latest = frame.sort_values("Year").groupby("Country").tail(1)
st.plotly_chart(px.bar(latest, x="Country", y="Value", color="Country", title="Latest available observation by country",
                       labels={"Value":unit}, template="plotly_dark"), use_container_width=True)
st.subheader("03 / Where might the trend go?")
pred = forecast_series(frame)
if not pred.empty:
    st.caption("Model selection: naive last-value vs. drift trend; evaluated using a chronological holdout and mean absolute error (MAE).")
    combined = pd.concat([frame.assign(Series="Observed"), pred.assign(Series="Illustrative projection")], ignore_index=True)
    fig = px.line(combined, x="Year", y="Value", color="Country", line_dash="Series",
                  title="Historical observations and baseline projections", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pred[["Country", "Year", "Value", "Method", "Holdout MAE"]], hide_index=True, use_container_width=True)
    st.warning("Projection is exploratory. No confidence intervals are claimed; holdout MAE measures past error, not future certainty. Structural changes can invalidate trends.")
else:
    st.info("Not enough consecutive annual observations for a defensible baseline forecast. No prediction shown.")
st.subheader("04 / Evidence & downloads")
methods = ("Descriptive comparisons use observed World Bank indicator values. Forecasts, where available, compare "
           "naive persistence against linear drift using the final five historical observations as a chronological "
           "holdout, selecting lower mean absolute error. These simple baselines are not universal best models. "
           "Missing years are not imputed; no causal claims are made.")
st.markdown(f"**Source:** [World Bank Indicators API]({provenance['url']}) · **Method:** {methods}")
story = narrative(topic, stories, pred)
pictures = charts(frame, pred, topic, unit)
st.markdown("### Your research story")
for paragraph in story[2:]:
    st.write(paragraph)
st.caption("Reports include the historical chart, latest-value comparison, and forecast visualization when available.")
c1,c2,c3 = st.columns(3)
c1.download_button("📕 Download illustrated PDF", export_pdf(topic, story, pictures, provenance, methods), file_name="insightflow-research.pdf", mime="application/pdf", use_container_width=True)
c2.download_button("📘 Download illustrated Word", export_docx(topic, story, pictures, provenance, methods), file_name="insightflow-research.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
c3.download_button("📽️ Download illustrated PowerPoint", export_pptx(topic, story, pictures, provenance, methods), file_name="insightflow-research.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
st.download_button("⬇️ Download source observations (CSV)", frame.to_csv(index=False), file_name="insightflow-source-data.csv", mime="text/csv")
