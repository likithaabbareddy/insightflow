import streamlit as st
st.set_page_config(page_title="InsightFlow | Research & Business Intelligence",page_icon="✨",layout="wide")
st.markdown("""<style>
.block-container{max-width:1120px;padding-top:3.5rem}
.hero{padding:45px;border-radius:26px;background:linear-gradient(115deg,#102a46,#106c6a);color:white;margin-bottom:28px}
.hero h1{color:white;font-size:3.4rem;letter-spacing:-.05em}
.hero p{color:#d7f4f0;font-size:1.15rem}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:20px}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>InsightFlow ✨</h1><p>One question. The right evidence. A story you can act on.</p></div>',unsafe_allow_html=True)
st.subheader("What would you like to accomplish?")
a,b=st.columns(2,gap="large")
with a:
    with st.container(border=True):
        st.markdown("## 🌍 Research")
        st.write("Explore public questions about society, economies, population, health and more. Discover indicators, compare history, and build visual reports.")
        st.page_link("pages/2_Research_Studio.py",label="Start research →",icon="🔎",use_container_width=True)
        st.caption("Source routing: trusted public indicators; currently World Bank.")
with b:
    with st.container(border=True):
        st.markdown("## 💼 Business Intelligence")
        st.write("Explore public market conditions or understand revenue, products, customers and other metrics from your own dataset.")
        st.page_link("pages/4_Business_Intelligence.py",label="Analyze business →",icon="📈",use_container_width=True)
        st.caption("Source routing: market indicators or uploaded business data.")
st.divider()
st.markdown("**More tools:**")
c,d=st.columns(2)
c.page_link("pages/1_Ask_NFL.py",label="🏈 Sports research")
d.page_link("pages/3_Dataset_Explorer.py",label="📊 Classic dataset explorer")
st.info("Prototype status: verified-source retrieval, descriptive analysis, baseline forecasts and visual report exports. Not yet a general autonomous LLM agent; coverage and capabilities depend on the chosen data source.")
