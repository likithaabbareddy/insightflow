import pandas as pd
import pytest
from src.agent_core import plan_question,audit_frame,business_insights

def test_route_modes():
    assert plan_question("How has population changed in India?","research")["data_route"]=="world_bank"
    assert plan_question("Which products have the highest sales?","business")["data_route"]=="uploaded_data_or_discovery"
    with pytest.raises(ValueError):plan_question(" ","research")

def test_business_metrics_and_quality():
    df=pd.DataFrame({"category":["A","B","A"],"sales":[10,20,30]})
    assert audit_frame(df)["rows"]==3
    result=business_insights(df,"sales","category")
    assert result["sum"]==60
    assert result["ranking"].iloc[0]["category"]=="A"
