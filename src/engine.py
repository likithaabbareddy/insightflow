"""Dataset-independent ingestion, profiling, chart suggestions, and baseline trends."""
from __future__ import annotations
from io import BytesIO
import numpy as np
import pandas as pd

def read_dataset(filename: str, content: bytes) -> pd.DataFrame:
    if len(content) > 20_000_000:
        raise ValueError("File exceeds 20 MB")
    ext = filename.lower().split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(BytesIO(content), nrows=100001)
    elif ext in {"xlsx", "xls"}:
        df = pd.read_excel(BytesIO(content), nrows=100001)
    else:
        raise ValueError("Supported formats: CSV, XLSX, XLS")
    if df.empty or len(df) > 100000:
        raise ValueError("Dataset must have 1–100,000 rows")
    df.columns = [str(c).strip() for c in df.columns]
    if len(set(df.columns)) != len(df.columns) or any(not c for c in df.columns):
        raise ValueError("Column names must be unique and nonempty")
    return df

def profile(df: pd.DataFrame) -> dict:
    data = df.copy()
    numeric, dates, categories = [], [], []
    for col in data.columns:
        s = data[col]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            numeric.append(col)
        elif pd.api.types.is_datetime64_any_dtype(s):
            dates.append(col)
        elif any(word in col.lower() for word in ("date", "timestamp", "datetime")):
            parsed = pd.to_datetime(s, errors="coerce")
            if parsed.notna().mean() >= 0.85:
                data[col] = parsed
                dates.append(col)
            else:
                categories.append(col)
        else:
            categories.append(col)
    return {"data": data, "numeric": numeric, "dates": dates,
            "categories": categories, "rows": len(data),
            "columns": len(data.columns), "missing": int(data.isna().sum().sum())}

def recommendations(p: dict) -> list[dict]:
    charts = []
    for d in p["dates"][:2]:
        for n in p["numeric"][:2]:
            charts.append({"kind": "line", "x": d, "y": n})
    for c in p["categories"][:3]:
        if p["data"][c].nunique(dropna=True) <= 30:
            for n in p["numeric"][:2]:
                charts.append({"kind": "bar", "x": c, "y": n})
            if not p["numeric"]:
                charts.append({"kind": "count", "x": c, "y": None})
    if len(p["numeric"]) >= 2:
        charts.append({"kind": "scatter", "x": p["numeric"][0], "y": p["numeric"][1]})
    for n in p["numeric"][:2]:
        charts.append({"kind": "hist", "x": n, "y": None})
    return charts[:8]

def time_series(df: pd.DataFrame, date_col: str, value_col: str, freq: str = "W") -> pd.Series:
    if freq not in {"D", "W", "MS"}:
        raise ValueError("Invalid frequency")
    t = df[[date_col, value_col]].copy()
    t[date_col] = pd.to_datetime(t[date_col], errors="coerce")
    t[value_col] = pd.to_numeric(t[value_col], errors="coerce")
    t = t.dropna()
    if t.empty:
        return pd.Series(dtype=float)
    return t.set_index(date_col)[value_col].sort_index().resample(freq).sum(min_count=1).dropna()

def forecast(series: pd.Series, horizon: int = 4) -> dict:
    y = series.to_numpy(dtype=float)
    if len(y) < 8 or not np.isfinite(y).all():
        raise ValueError("At least 8 valid time periods are required")
    if not 1 <= horizon <= 24:
        raise ValueError("Horizon must be between 1 and 24")
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    future = slope * np.arange(len(y), len(y) + horizon) + intercept
    return {"values": future.tolist(), "warning": "Illustrative linear extrapolation, not a validated prediction."}
