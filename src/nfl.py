"""Read-only public NFL data connector and question-oriented analytics."""
from __future__ import annotations
import pandas as pd

GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
PLAYERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_season.csv"

def load_games() -> pd.DataFrame:
    df = pd.read_csv(GAMES_URL, low_memory=False)
    if "season" not in df and "gameday" in df:
        df["season"] = pd.to_datetime(df["gameday"], errors="coerce").dt.year
    for c in ("home_score", "away_score", "season"):
        if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def load_players() -> pd.DataFrame:
    df = pd.read_csv(PLAYERS_URL, low_memory=False)
    if "season_type" in df:
        df = df[df["season_type"] == "REG"].copy()
    return df

def team_history(df: pd.DataFrame, team: str, start: int, end: int) -> pd.DataFrame:
    subset = df[df["season"].between(start, end)].copy()
    home = subset["home_team"].eq(team)
    away = subset["away_team"].eq(team)
    subset = subset[home | away].copy()
    if subset.empty: return pd.DataFrame(columns=["season", "games", "wins", "win_pct", "points_for", "points_against"])
    h = subset["home_team"].eq(team)
    subset["points_for"] = subset["home_score"].where(h, subset["away_score"])
    subset["points_against"] = subset["away_score"].where(h, subset["home_score"])
    subset = subset.dropna(subset=["points_for", "points_against"])
    subset["win"] = (subset["points_for"] > subset["points_against"]).astype(int)
    out = subset.groupby("season", as_index=False).agg(games=("win", "size"), wins=("win", "sum"),
                       points_for=("points_for", "sum"), points_against=("points_against", "sum"))
    out["win_pct"] = (out["wins"] / out["games"] * 100).round(1)
    return out

def interpret_question(question: str) -> dict:
    q = question.lower()
    if any(t in q for t in ("quarterback", "player", "passing", "rushing", "receiving", "touchdown")):
        return {"domain": "players", "metric": next((m for m in ("passing_yards", "rushing_yards", "receiving_yards", "passing_tds", "rushing_tds", "receiving_tds") if m.replace("_", " ") in q), "passing_yards")}
    return {"domain": "teams", "metric": "win_pct" if any(w in q for w in ("win", "success", "best", "performance")) else "points_for"}

def simple_outlook(values: pd.Series, periods: int = 3) -> list[float]:
    """Baseline only; no game outcome probabilities or calibrated uncertainty."""
    import numpy as np
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if len(arr) < 5: return []
    recent = arr[-min(8, len(arr)):]
    x = np.arange(len(recent))
    slope, intercept = np.polyfit(x, recent, 1)
    return [float(intercept + slope * (len(recent) + i)) for i in range(periods)]
