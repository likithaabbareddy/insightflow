import streamlit as st
st.set_page_config(page_title="InsightFlow | Research intelligence", page_icon="✨", layout="wide")
st.markdown("""<style>
.block-container{max-width:1100px;padding-top:4rem}
h1{font-size:3.6rem!important;letter-spacing:-.055em}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:18px}
.hero{padding:40px 44px;border-radius:25px;background:linear-gradient(120deg,#173d5b,#116b67);color:white;margin-bottom:26px}
.hero h1{color:white;margin-bottom:10px}
.hero p{font-size:1.25rem;color:#e5f5f4}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>InsightFlow ✨</h1><p>From curiosity to evidence. Ask better questions, explore trusted data, and share a story worth telling.</p></div>',unsafe_allow_html=True)
st.caption("Research-first analytics · Source transparency · Interactive visuals · Downloadable reports")
st.subheader("Where would you like to begin?")
a,b = st.columns(2)
with a:
    with st.container(border=True):
        st.markdown("### 🌐 Research Studio")
        st.write("Investigate population, economic trends, life expectancy, unemployment and emissions across countries. We retrieve public World Bank data for you.")
        st.page_link("pages/2_Research_Studio.py", label="Open Research Studio →", icon="🔎")
with b:
    with st.container(border=True):
        st.markdown("### 🏈 NFL Research")
        st.write("Explore historical team performance and player statistics with interactive charts and source-aware baselines.")
        st.page_link("pages/1_Ask_NFL.py", label="Explore NFL data →", icon="🏈")
with st.container(border=True):
    st.markdown("### 📁 Your own data")
    st.write("Upload CSV or Excel to explore custom datasets with the original generic dashboard.")
    st.page_link("pages/3_Dataset_Explorer.py", label="Open Dataset Explorer →", icon="📊")
st.info("Research Studio currently supports five verified World Bank indicators, not unrestricted web research. Unsupported questions are clearly flagged rather than answered with invented numbers.")
st.caption("InsightFlow is a research prototype. Forecasts are exploratory, not investment, medical or other professional advice.")
