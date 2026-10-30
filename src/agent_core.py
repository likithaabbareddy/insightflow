"""Deterministic planning and data quality checks shared across both product paths."""
import re
import pandas as pd
from src.research import match_topic, infer_countries

def plan_question(question: str, mode: str) -> dict:
    q = question.strip()
    if not q: raise ValueError("Enter a question")
    if mode not in {"research", "business"}: raise ValueError("Unknown mode")
    topic = match_topic(q)
    return {"question": q, "mode": mode, "topic": topic,
            "countries": infer_countries(q),
            "data_route": "world_bank" if topic else ("uploaded_data_or_discovery" if mode=="business" else "indicator_discovery"),
            "steps": ["Identify the required measures and scope", "Collect data and record provenance",
                      "Audit missing values and historical coverage", "Calculate trends and compare groups",
                      "Validate any forecast on held-out observations", "Explain findings with caveats and export evidence"]}

def audit_frame(df: pd.DataFrame) -> dict:
    return {"rows": len(df), "columns": len(df.columns),
            "missing_cells": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "fields": list(map(str, df.columns))}

def business_insights(df: pd.DataFrame, metric: str, dimension: str | None = None) -> dict:
    if metric not in df or not pd.api.types.is_numeric_dtype(df[metric]):
        raise ValueError("Select a numeric metric")
    vals = pd.to_numeric(df[metric],errors="coerce").dropna()
    if vals.empty: raise ValueError("No valid metric values")
    result = {"count": int(vals.size), "sum": float(vals.sum()), "average": float(vals.mean()),
              "median": float(vals.median()), "min": float(vals.min()), "max": float(vals.max())}
    if dimension and dimension in df:
        grouped = df.groupby(dimension,dropna=False)[metric].sum().sort_values(ascending=False).head(15)
        result["ranking"] = grouped.reset_index()
    return result
