import pandas as pd
from src.research import match_topic, infer_countries, describe_trends, forecast_series
from src.exports import report_lines, pdf_bytes, docx_bytes, pptx_bytes

def test_routing():
    assert match_topic("How has life expectancy changed in India?") == "Life expectancy"
    assert infer_countries("India and Germany") == ["IND", "DEU"]
    assert match_topic("Tell me about chess") is None

def test_forecast():
    df = pd.DataFrame({"Country":["A"]*20,"Year":range(2000,2020),"Value":range(20)})
    assert len(forecast_series(df)) == 5
    df.loc[3, "Year"] = 1998
    assert forecast_series(df).empty

def test_exports():
    meta = {"provider":"World Bank","indicator":"SP.POP.TOTL","url":"https://example.org",
            "retrieved_at":"2026-10-30","observations":20}
    lines = report_lines("Research", "population?", [{"country":"India","pct":10,"first":1,"last":2,
        "start_year":2000,"end_year":2020}],meta,"Descriptive trend.")
    assert pdf_bytes(lines).startswith(b"%PDF")
    assert docx_bytes(lines).startswith(b"PK")
    assert pptx_bytes(lines).startswith(b"PK")
