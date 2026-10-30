"""Curated public-source research. Never fabricate or silently substitute datasets."""
from __future__ import annotations
import re
import pandas as pd

CATALOG = {
 "Population": {"keywords": ["population", "people", "demographic"], "source": "World Bank", "indicator": "SP.POP.TOTL", "unit": "people"},
 "GDP per capita": {"keywords": ["gdp per capita", "income per person", "economic growth", "economy"], "source": "World Bank", "indicator": "NY.GDP.PCAP.CD", "unit": "current US$"},
 "Life expectancy": {"keywords": ["life expectancy", "longevity", "life span"], "source": "World Bank", "indicator": "SP.DYN.LE00.IN", "unit": "years"},
 "CO₂ emissions": {"keywords": ["carbon", "co2", "emissions", "climate"], "source": "World Bank", "indicator": "EN.GHG.CO2.MT.CE.AR5", "unit": "million tonnes CO₂e"},
 "Unemployment": {"keywords": ["unemployment", "jobless", "labor market"], "source": "World Bank", "indicator": "SL.UEM.TOTL.ZS", "unit": "% of labor force"},
}
COUNTRIES = {"United States": "USA", "United Kingdom": "GBR", "India": "IND", "China": "CHN",
             "Germany": "DEU", "Japan": "JPN", "Brazil": "BRA", "Canada": "CAN",
             "France": "FRA", "Australia": "AUS", "South Africa": "ZAF", "Mexico": "MEX"}

def match_topic(question: str) -> str | None:
    q = question.casefold()
    matches = [(len(word), topic) for topic, cfg in CATALOG.items() for word in cfg["keywords"] if word in q]
    return max(matches)[1] if matches else None

def infer_countries(question: str) -> list[str]:
    q = question.casefold()
    found = [code for name, code in COUNTRIES.items() if name.casefold() in q]
    return found or ["USA", "IND", "CHN"]

def fetch_world_bank(topic: str, countries: list[str]) -> tuple[pd.DataFrame, dict]:
    if topic not in CATALOG: raise ValueError("Unsupported research topic")
    allowed = set(COUNTRIES.values())
    if not countries or any(c not in allowed for c in countries): raise ValueError("Unsupported country")
    cfg = CATALOG[topic]
    indicator = cfg["indicator"]
    url = f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
    import requests
    response = requests.get(url, params={"format": "json", "per_page": 20000}, timeout=25)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        raise ValueError("No observations returned by World Bank")
    rows = []
    for record in payload[1]:
        try:
            if record["value"] is not None:
                rows.append({"Year": int(record["date"]), "Country": record["country"]["value"],
                             "Value": float(record["value"])})
        except (KeyError, ValueError, TypeError): continue
    frame = pd.DataFrame(rows)
    if frame.empty: raise ValueError("No valid observations found")
    frame = frame.sort_values(["Country", "Year"])
    return frame, {"provider": "World Bank", "url": url, "indicator": indicator, "unit": cfg["unit"],
                   "retrieved_at": pd.Timestamp.now(tz="UTC").isoformat(),
                   "observations": len(frame), "countries": sorted(frame["Country"].unique().tolist())}

def describe_trends(frame: pd.DataFrame, unit: str) -> list[dict]:
    stories = []
    for country, group in frame.groupby("Country"):
        group = group.sort_values("Year")
        first, last = group.iloc[0], group.iloc[-1]
        delta = float(last["Value"] - first["Value"])
        pct = 100 * delta / abs(float(first["Value"])) if first["Value"] else None
        stories.append({"country": country, "start_year": int(first["Year"]), "end_year": int(last["Year"]),
                        "first": float(first["Value"]), "last": float(last["Value"]),
                        "delta": delta, "pct": pct, "n": len(group), "unit": unit})
    return stories

def forecast_series(frame: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Compare naive and drift baselines on a chronological holdout; never claim universal best model."""
    import numpy as np
    if horizon < 1 or horizon > 10: raise ValueError("Invalid horizon")
    rows = []
    for country, group in frame.groupby("Country"):
        g = group.sort_values("Year").drop_duplicates("Year")
        if len(g) < 12: continue
        years = g["Year"].to_numpy(dtype=int)
        vals = g["Value"].to_numpy(dtype=float)
        # Restrict model to consecutive annual observations, avoiding false interpolation.
        if not np.all(np.diff(years) == 1): continue
        split = max(5, len(vals)-5)
        train, holdout = vals[:split], vals[split:]
        naive_pred = np.full(len(holdout), train[-1])
        slope = (train[-1]-train[0]) / (len(train)-1)
        drift_pred = train[-1] + slope*np.arange(1, len(holdout)+1)
        naive_mae = float(np.mean(np.abs(holdout-naive_pred)))
        drift_mae = float(np.mean(np.abs(holdout-drift_pred)))
        method = "Naive last value" if naive_mae <= drift_mae else "Drift trend"
        for step in range(1, horizon+1):
            estimate = vals[-1] if method == "Naive last value" else vals[-1]+(vals[-1]-vals[0])/(len(vals)-1)*step
            rows.append({"Country": country, "Year": int(years[-1]+step), "Value": float(estimate),
                         "Method": method, "Holdout MAE": min(naive_mae, drift_mae)})
    return pd.DataFrame(rows)

def discover_indicators(question: str, limit: int = 8) -> list[dict]:
    """Search live World Bank indicator metadata, ranking matches by query tokens.

    Discovery is broader than the curated catalog but does not claim web-wide coverage.
    """
    import requests
    import re
    stop = {"what","which","when","where","why","how","have","has","had","the","and","for","with",
            "over","last","years","year","trend","trends","compare","comparison","show","me",
            "in","of","to","is","are","data","about","change","changed","between","from","will"}
    terms = [t for t in re.findall(r"[a-z]{3,}", question.lower()) if t not in stop]
    if not terms: return []
    response = requests.get("https://api.worldbank.org/v2/indicator", params={"format":"json","per_page":20000}, timeout=35)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload)<2 or not payload[1]: return []
    ranked = []
    for item in payload[1]:
        name = str(item.get("name") or "")
        code = str(item.get("id") or "")
        source = str((item.get("source") or {}).get("value") or "")
        if not code or not name or not source: continue
        name_words = set(re.findall(r"[a-z]{3,}", name.lower()))
        score = sum(3 if t in name_words else 1 if t in name.lower() else 0 for t in terms)
        if score >= max(2, len(terms)//2):
            ranked.append((score, {"name":name,"indicator":code,"source":source}))
    ranked.sort(key=lambda pair: (-pair[0],len(pair[1]["name"])))
    return [item for _,item in ranked[:limit]]

def fetch_discovered_indicator(indicator: str, countries: list[str]) -> tuple[pd.DataFrame, dict]:
    """Retrieve an explicitly discovered World Bank indicator, preserving provenance."""
    import requests
    if not re.fullmatch(r"[A-Za-z0-9_.]+", indicator): raise ValueError("Invalid indicator code")
    if not countries or any(c not in set(COUNTRIES.values()) for c in countries): raise ValueError("Unsupported country")
    url = f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
    response = requests.get(url, params={"format":"json","per_page":20000}, timeout=25)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload,list) or len(payload)<2 or not payload[1]: raise ValueError("No data for this indicator and country selection")
    rows=[]
    for record in payload[1]:
        try:
            if record["value"] is not None:
                rows.append({"Year":int(record["date"]),"Country":record["country"]["value"],"Value":float(record["value"])})
        except (ValueError,TypeError,KeyError): continue
    frame=pd.DataFrame(rows)
    if frame.empty: raise ValueError("No numeric observations available")
    return frame.sort_values(["Country","Year"]), {"provider":"World Bank","url":url,"indicator":indicator,
       "unit":"indicator units (see source metadata)","retrieved_at":pd.Timestamp.now(tz="UTC").isoformat(),
       "observations":len(frame),"countries":sorted(frame["Country"].unique().tolist())}
