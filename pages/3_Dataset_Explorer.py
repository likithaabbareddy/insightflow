import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.engine import read_dataset, profile, recommendations, time_series, forecast

st.set_page_config(page_title="InsightFlow", page_icon="📊", layout="wide")
st.title("📊 InsightFlow")
st.caption("Generic dataset → automatic dashboard. No coding or API key needed.")
with st.sidebar:
    st.header("Dataset")
    source = st.selectbox("Data source", ["Upload file", "NFL sample", "Retail sample", "Weather sample"])
    uploaded = st.file_uploader("CSV / Excel", type=["csv", "xlsx", "xls"]) if source == "Upload file" else None
    st.warning("Avoid sensitive data on a public demo.")

if source == "Upload file" and uploaded is None:
    st.info("Upload a CSV/Excel file or select a sample dataset.")
    st.stop()
try:
    if uploaded is not None:
        df = read_dataset(uploaded.name, uploaded.getvalue())
    else:
        path = {"NFL sample": "nfl.csv", "Retail sample": "retail.csv", "Weather sample": "weather.csv"}[source]
        df = pd.read_csv("sample_data/" + path)
    p = profile(df)
except Exception as exc:
    st.error(f"Could not load dataset: {exc}")
    st.stop()

a,b,c,d = st.columns(4)
a.metric("Rows", f"{p['rows']:,}")
b.metric("Columns", p["columns"])
c.metric("Numeric fields", len(p["numeric"]))
d.metric("Missing cells", p["missing"])
with st.expander("Dataset preview and inferred schema"):
    st.dataframe(p["data"].head(100), use_container_width=True)
    st.write({"Dates": p["dates"], "Numeric": p["numeric"], "Categories": p["categories"]})

st.header("Automatically suggested charts")
charts = recommendations(p)
if not charts:
    st.info("No suitable charts found for this dataset.")
for idx, cfg in enumerate(charts):
    kind, x, y = cfg["kind"], cfg["x"], cfg["y"]
    try:
        if kind == "line":
            frame = time_series(p["data"], x, y).reset_index()
            fig = px.line(frame, x=x, y=y, markers=True, title=f"{y} over time")
        elif kind == "bar":
            frame = p["data"].groupby(x, dropna=False)[y].sum().reset_index().sort_values(y, ascending=False).head(20)
            fig = px.bar(frame, x=x, y=y, title=f"Sum of {y} by {x}")
        elif kind == "count":
            frame = p["data"][x].value_counts(dropna=False).head(20).rename_axis(x).reset_index(name="count")
            fig = px.bar(frame, x=x, y="count", title=f"Count by {x}")
        elif kind == "scatter":
            fig = px.scatter(p["data"].sample(min(len(p["data"]), 3000), random_state=42), x=x, y=y)
        else:
            fig = px.histogram(p["data"], x=x, title=f"Distribution of {x}")
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
    except Exception as exc:
        st.warning(f"Could not draw {kind} chart: {exc}")

st.header("Explore")
if p["numeric"]:
    metric = st.selectbox("Measure", p["numeric"])
    dimension = st.selectbox("Group by", ["None"] + p["dates"] + p["categories"])
    if dimension != "None":
        if dimension in p["dates"]:
            frame = time_series(p["data"], dimension, metric).reset_index()
            st.plotly_chart(px.line(frame, x=dimension, y=metric, markers=True), use_container_width=True)
        else:
            frame = p["data"].groupby(dimension, dropna=False)[metric].sum().reset_index().head(40)
            st.plotly_chart(px.bar(frame, x=dimension, y=metric), use_container_width=True)

st.header("Exploratory forecast")
if p["dates"] and p["numeric"]:
    date = st.selectbox("Date field", p["dates"])
    value = st.selectbox("Measure to project", p["numeric"])
    freq = st.selectbox("Period", ["W", "MS", "D"], format_func=lambda f: {"W":"Weekly","MS":"Monthly","D":"Daily"}[f])
    series = time_series(p["data"], date, value, freq)
    if len(series) >= 8:
        prediction = forecast(series)
        next_dates = pd.date_range(series.index[-1], periods=5, freq=freq)[1:]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index, y=series.values, name="Observed"))
        fig.add_trace(go.Scatter(x=next_dates, y=prediction["values"], name="Projected", line={"dash":"dash"}))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(prediction["warning"])
    else:
        st.info(f"Need at least 8 nonempty periods; found {len(series)}.")
else:
    st.info("Forecast requires a date and numeric field.")
st.caption("v0.1 • Rule-based analytics MVP • Synthetic sample data • Not yet an AI agent")
