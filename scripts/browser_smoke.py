"""Playwright smoke test; screenshots and errors saved as GitHub Actions artifacts."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

out = Path("diagnostics")
out.mkdir(exist_ok=True)
url = "https://insightflow-cdeqpvxw4q2wo4ardrzl4a.streamlit.app/"
errors = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.on("pageerror", lambda err: errors.append(str(err)))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(15000)
        page.screenshot(path=str(out / "home.png"), full_page=True)
        (out / "home-text.txt").write_text(page.locator("body").inner_text()[:12000])
        if "InsightFlow" not in page.locator("body").inner_text():
            errors.append("InsightFlow heading not found (app may be sleeping or failed to load)")
        page.goto(url.rstrip("/") + "/Ask_NFL", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(12000)
        page.screenshot(path=str(out / "ask-nfl.png"), full_page=True)
        text = page.locator("body").inner_text()
        (out / "ask-nfl-text.txt").write_text(text[:12000])
        if "Ask NFL" not in text:
            errors.append("Ask NFL page not found")
    except Exception as exc:
        errors.append(str(exc))
        page.screenshot(path=str(out / "failure.png"), full_page=True)
    finally:
        (out / "browser-errors.json").write_text(json.dumps(errors, indent=2))
        browser.close()
if errors:
    raise SystemExit("Browser smoke test failed: " + "; ".join(errors))
print("Browser smoke test passed; screenshots saved to artifacts.")
