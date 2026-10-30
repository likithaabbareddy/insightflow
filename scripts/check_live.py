"""Read-only availability probe for the public Streamlit deployment.

Writes a GitHub Actions-friendly report that can be retrieved remotely.
This is not an interactive browser test.
"""
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://insightflow-cdeqpvxw4q2wo4ardrzl4a.streamlit.app"
REPORT_DIR = Path("diagnostics")
REPORT_DIR.mkdir(exist_ok=True)
results = []
for path in ("/", "/_stcore/health"):
    result = {"url": BASE + path, "ok": False}
    try:
        req = Request(BASE + path, headers={"User-Agent": "InsightFlow-CI-Smoke-Test/1.0"})
        with urlopen(req, timeout=30) as response:
            body = response.read(100000).decode("utf-8", errors="replace")
            result.update(status=response.status, ok=response.status == 200,
                          body_excerpt=body[:500])
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        result["error"] = str(exc)
    results.append(result)
    print(f"{result['url']}: status={result.get('status', 'error')}, ok={result['ok']}")
report = {"target": BASE, "checks": results,
          "note": "Streamlit may sleep or require wake-up. HTTP success does not prove dashboard renders correctly."}
(REPORT_DIR / "live-status.json").write_text(json.dumps(report, indent=2))
summary = "## InsightFlow live deployment check\n\n"
for item in results:
    summary += f"- `{item['url']}`: **{'OK' if item['ok'] else 'FAILED'}** (HTTP {item.get('status', 'n/a')})\n"
summary += "\nThis is a network availability check, not full interactive UI verification.\n"
(REPORT_DIR / "summary.md").write_text(summary)
if os.getenv("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(summary)
if not all(r["ok"] for r in results):
    raise SystemExit("One or more live endpoints are unavailable; see diagnostics.")
