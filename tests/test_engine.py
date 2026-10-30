import pandas as pd
import pytest
from src.engine import read_dataset, profile, recommendations, forecast

def test_schema_and_charts():
    p = profile(pd.DataFrame({"event_date":["2025-01-01","2025-01-02"],"value":[2,3],"group":["a","b"]}))
    assert p["dates"] == ["event_date"]
    assert p["numeric"] == ["value"]
    assert recommendations(p)

def test_csv():
    assert len(read_dataset("test.csv", b"name,amount\na,2\nb,3\n")) == 2

def test_forecast_validation():
    with pytest.raises(ValueError):
        forecast(pd.Series([1,2,3]))
