import pandas as pd
from src.nfl import team_history, interpret_question, simple_outlook

def test_team_history():
    games = pd.DataFrame({"season":[2024,2024,2025], "home_team":["DET","GB","DET"],
        "away_team":["GB","DET","GB"], "home_score":[21,10,24], "away_score":[14,17,27]})
    h = team_history(games, "DET", 2024, 2025)
    assert h["wins"].tolist() == [2,0]
    assert h["win_pct"].tolist() == [100.0,0.0]

def test_intents():
    assert interpret_question("Which players have most passing yards?")["domain"] == "players"
    assert interpret_question("Lions win trends")["domain"] == "teams"

def test_baseline():
    assert len(simple_outlook(pd.Series([1,2,3,4,5,6]))) == 3
