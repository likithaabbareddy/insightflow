import streamlit as st
import pandas as pd
import plotly.express as px
from src.nfl import load_games, load_players, team_history, interpret_question, simple_outlook

st.set_page_config(page_title="Ask NFL | InsightFlow", page_icon="🏈", layout="wide")
st.title("🏈 Ask NFL")
st.caption("Ask a question. InsightFlow retrieves public NFL data and builds an interactive analysis.")
st.info("This is a question-guided analytics prototype, not an LLM. It recognizes a limited set of question patterns. All analysis is based on retrieved public data.")
question = st.text_input("What would you like to investigate?", placeholder="How have the Detroit Lions performed over the last 30 years?")
with st.expander("Try these questions"):
    st.markdown("• Which teams have the best win rates over 30 years?\n\n• How have the Lions performed over 20 years?\n\n• Who leads in passing yards in recent seasons?")
@st.cache_data(ttl=21600, show_spinner=False)
def games(): return load_games()
@st.cache_data(ttl=21600, show_spinner=False)
def players(): return load_players()

if not question.strip():
    st.stop()
intent = interpret_question(question)
with st.spinner("Retrieving public data and preparing analysis…"):
    try:
        if intent["domain"] == "players":
            data = players()
        else:
            data = games()
    except Exception as exc:
        st.error(f"Data provider unavailable: {exc}. Please retry later.")
        st.stop()

if intent["domain"] == "players":
    st.subheader("Player trends")
    st.caption("Source: nflverse player season statistics. Availability varies by season and metric.")
    metric = intent["metric"]
    numeric = [c for c in data.select_dtypes(include="number").columns if c not in ("season", "week")]
    if not numeric:
        st.warning("No numeric player measures found in the source.")
        st.stop()
    metric = st.selectbox("Metric", numeric, index=numeric.index(metric) if metric in numeric else 0)
    if "season" not in data or "player_name" not in data:
        st.warning("Player data schema changed; cannot display player history.")
        st.stop()
    seasons = sorted(data["season"].dropna().unique().astype(int))
    window = st.slider("Seasons to show", 1, min(25, len(seasons)), min(8, len(seasons)))
    frame = data[data["season"].isin(seasons[-window:])].copy()
    leaders = frame.groupby("player_name", as_index=False)[metric].sum().nlargest(12, metric)
    st.plotly_chart(px.bar(leaders.sort_values(metric), x=metric, y="player_name", orientation="h",
                           title=f"Top players by {metric.replace('_',' ')}"), use_container_width=True)
    names = leaders["player_name"].tolist()
    selected = st.multiselect("Compare players", names, default=names[:3])
    if selected:
        history = frame[frame["player_name"].isin(selected)].groupby(["season", "player_name"], as_index=False)[metric].sum()
        st.plotly_chart(px.line(history, x="season", y=metric, color="player_name", markers=True,
                                title="Season-by-season comparison"), use_container_width=True)
    st.dataframe(leaders, use_container_width=True)
else:
    st.subheader("Team history: decades of NFL results")
    st.caption("Source: nflverse/nfldata games.csv. Historical team abbreviations may differ following relocations.")
    if "season" not in data:
        st.error("Game dataset does not contain season information.")
        st.stop()
    seasons = pd.to_numeric(data["season"], errors="coerce").dropna().astype(int)
    if seasons.empty:
        st.error("No seasons found.")
        st.stop()
    last = int(seasons.max())
    years = st.slider("Historical window (years)", 5, 50, 30)
    teams = sorted(set(data["home_team"].dropna()) | set(data["away_team"].dropna()))
    guessed = next((t for t in teams if t.lower() in question.lower().split()), None)
    if not guessed:
        team_aliases = {"lions": "DET", "packers": "GB", "chiefs": "KC", "cowboys": "DAL", "bears": "CHI", "patriots": "NE", "eagles": "PHI", "49ers": "SF", "steelers": "PIT", "bills": "BUF", "vikings": "MIN", "ravens": "BAL", "dolphins": "MIA", "jets": "NYJ", "giants": "NYG"}
        guessed = next((abbr for name, abbr in team_aliases.items() if name in question.lower() and abbr in teams), None)
    default = teams.index(guessed) if guessed in teams else 0
    team = st.selectbox("Team", teams, index=default)
    history = team_history(data, team, last-years+1, last)
    if history.empty:
        st.warning("No completed games for this team in the selected window.")
        st.stop()
    a,b,c = st.columns(3)
    a.metric("Seasons covered", len(history))
    b.metric("Total wins", int(history["wins"].sum()))
    c.metric("Overall win rate", f"{100*history['wins'].sum()/history['games'].sum():.1f}%")
    st.plotly_chart(px.line(history, x="season", y="win_pct", markers=True,
                            title=f"{team} winning percentage by season"), use_container_width=True)
    long = history.melt(id_vars="season", value_vars=["points_for","points_against"],
                        var_name="Measure", value_name="Points")
    st.plotly_chart(px.area(long, x="season", y="Points", color="Measure",
                            title="Points scored and conceded over time"), use_container_width=True)
    st.plotly_chart(px.scatter(history, x="points_for", y="win_pct", size="games",
                               hover_data=["season"], title="Does scoring more correlate with winning?"),
                    use_container_width=True)
    st.subheader("Exploratory outlook")
    prediction = simple_outlook(history["win_pct"])
    if prediction:
        outlook = pd.DataFrame({"season": range(int(history["season"].max())+1, int(history["season"].max())+1+len(prediction)),
                                "projected_win_pct": [max(0, min(100, v)) for v in prediction]})
        st.plotly_chart(px.line(outlook, x="season", y="projected_win_pct", markers=True,
                                title="Illustrative win-rate trend (not a game prediction)"), use_container_width=True)
        st.warning("This is an unvalidated linear trend, not a calibrated forecast. It does not account for rosters, injuries, schedule, or coaching changes.")
    st.dataframe(history.sort_values("season", ascending=False), use_container_width=True)
st.caption("Public data from nflverse; attribution: nflverse contributors (CC BY 4.0 where applicable). Refresh cache every 6 hours.")
