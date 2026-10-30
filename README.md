# InsightFlow 📊

**Generic data-to-dashboard MVP** — upload any tabular CSV or Excel dataset and automatically explore its fields, charts, and trends. NFL is only a test dataset, not a special case.

## Features
- Upload CSV/XLSX/XLS or load synthetic NFL, retail, and weather samples.
- Infer date, numeric, and categorical fields.
- Inspect missing values and preview data.
- Automatically recommend interactive Plotly charts.
- Explore measures by date or category.
- Produce simple exploratory linear trend projections where at least 8 periods exist.

**Status:** v0.1 is a rule-based prototype, **not yet an LLM-powered AI agent**. No API key required.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Run tests: `pytest -q`.

## Deploy for free
1. Sign into [Streamlit Community Cloud](https://share.streamlit.io/) using GitHub.
2. Create a new app from repository `likithaabbareddy/insightflow`, branch `main`.
3. Set the entrypoint to `app.py` and deploy.
4. Test the three built-in samples and upload an unrelated CSV or Excel file.

**Deployment has not been performed or verified yet.** Public demo users should not upload private or sensitive data.

## Testing with real NFL data
Download a games CSV from [nflverse](https://github.com/nflverse/nfldata) and upload it. The application uses exactly the same generic pipeline for NFL, retail, weather, or other structured data.

## Files
- `app.py` — Streamlit interface and Plotly charts.
- `src/engine.py` — generic ingestion, profiling, chart suggestions and forecasting.
- `sample_data/` — synthetic examples.
- `tests/` — basic engine tests.
- `docs/WALKTHROUGH.md` — usage walkthrough and screenshot checklist.

## Limitations and next steps
Single table, no live source refresh, no accounts or persistence, no LLM integration. Date inference relies on column names. Generic summation is not appropriate for every measure (e.g. temperature or scores); users must interpret charts critically. Forecasts are basic linear extrapolations, not calibrated predictions.

Next: browser smoke test and actual screenshots, semantic metric selection, optional LLM planner with validated calculations, live data connectors, and improved forecasting.
