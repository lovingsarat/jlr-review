"""
autoportal_scraper.py — Scrape public automotive review portals for JLR and Tata Motors.
Sources: AutoExpress (UK, JLR), CarDekho (India, Tata), Zigwheels (India, Tata), Trustpilot JLR dealers.
Uses Playwright for JS-rendered pages. Run as subprocess from scraper.py.
"""
import os
import sys
import json
import sqlite3
import time
import re
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")
GEMINI_MODEL = "gemini-3.1-flash-lite"

# ─── Review source URLs ───────────────────────────────────────────────────────
# AutoExpress review pages (JLR) — public, no login
JLR_AUTOEXPRESS_URLS = [
    ("https://www.autoexpress.co.uk/land-rover/defender", "Defender General", "jlr"),
    ("https://www.autoexpress.co.uk/land-rover/range-rover", "Range Rover", "jlr"),
    ("https://www.autoexpress.co.uk/jaguar/f-pace", "F-PACE", "jlr"),
    ("https://www.autoexpress.co.uk/jaguar/i-pace", "I-PACE", "jlr"),
    ("https://www.autoexpress.co.uk/land-rover/discovery", "Discovery General", "jlr"),
]

# CarDekho user review pages (Tata) — public
TATA_CARDEKHO_URLS = [
    ("https://www.cardekho.com/tata/nexon-ev/user-reviews", "Nexon EV", "tata"),
    ("https://www.cardekho.com/tata/punch-ev/user-reviews", "Punch EV", "tata"),
    ("https://www.cardekho.com/tata/harrier/user-reviews", "Harrier", "tata"),
    ("https://www.cardekho.com/tata/safari/user-reviews", "Safari", "tata"),
    ("https://www.cardekho.com/tata/altroz/user-reviews", "Altroz", "tata"),
    ("https://www.cardekho.com/tata/tiago-ev/user-reviews", "Tiago EV", "tata"),
]


def analyze_with_gemini(text: str, brand_hint: str, vehicle_model: str = "General") -> dict:
    """Call Gemini to structure an automotive review."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key in ["MY_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"]:
        return _default_analysis(brand_hint, vehicle_model)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    brand_context = (
        "JLR: Jaguar (F-PACE, E-PACE, I-PACE), Range Rover (Range Rover, Sport, Velar, Evoque), "
        "Defender (90, 110, 130, OCTA), Discovery (Discovery, Discovery Sport)."
        if brand_hint == "jlr"
        else "Tata Motors: Nexon EV, Punch EV, Curvv EV, Harrier, Harrier EV, Safari, Tiago EV, Altroz."
    )

    prompt = f"""
Analyze this automotive review from a portal (AutoExpress/CarDekho).
Known vehicle: {vehicle_model}. Brand context: {brand_context}

Return JSON with:
- "sentiment": "Positive", "Neutral", or "Negative"
- "brand": "{brand_hint}"
- "brand_group": For JLR: "Jaguar"/"Range Rover"/"Defender"/"Discovery"; For Tata: "SUV"/"EV"/"Hatchback"/"Sedan"
- "vehicle_model": "{vehicle_model}" (use this unless review clearly mentions a different model)
- "isUpcoming": false (portal reviews are for existing vehicles unless clearly about a launch)
- "category_tag": one of: Performance, EV Range, Comfort, Infotainment, Build Quality, After-Sales, Pricing, Safety, Off-road, Design, General
- "priority_score": 1–5
- "action_insight": one actionable sentence for the brand team

Review: "{text[:600]}"

JSON only:
"""

    try:
        resp = httpx.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}},
            timeout=20.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            match = re.search(r"\{.*\}", reply, re.DOTALL)
            if match:
                reply = match.group(0)
            return json.loads(reply)
    except Exception as e:
        print(f"[WARN] Gemini error: {e}")
    return _default_analysis(brand_hint, vehicle_model)


def _default_analysis(brand_hint: str, vehicle_model: str = "General") -> dict:
    return {
        "sentiment": "Neutral",
        "brand": brand_hint,
        "brand_group": "Defender" if brand_hint == "jlr" else "SUV",
        "vehicle_model": vehicle_model,
        "isUpcoming": False,
        "priority_score": 1,
        "category_tag": "General",
        "action_insight": "No recommendation.",
    }


def upsert_item(item: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_items (
            id TEXT PRIMARY KEY, platform TEXT, author TEXT, date TEXT,
            event TEXT, text TEXT, sentiment TEXT, city TEXT, isUpcoming INTEGER,
            parent_id TEXT, priority_score INTEGER, category_tag TEXT,
            action_insight TEXT, brand TEXT
        )
    """)
    for col, col_type in [("brand", "TEXT"), ("priority_score", "INTEGER"),
                           ("category_tag", "TEXT"), ("action_insight", "TEXT"), ("parent_id", "TEXT")]:
        try:
            cursor.execute(f"ALTER TABLE feedback_items ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
        INSERT OR REPLACE INTO feedback_items
            (id, platform, author, date, event, text, sentiment, city,
             isUpcoming, parent_id, priority_score, category_tag, action_insight, brand)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["id"], item["platform"], item["author"], item["date"],
        item["event"], item["text"], item["sentiment"], item["city"],
        1 if item.get("isUpcoming") else 0, item.get("parent_id"),
        item.get("priority_score", 1), item.get("category_tag", "General"),
        item.get("action_insight", "No recommendation."), item.get("brand", "jlr"),
    ))
    conn.commit()
    conn.close()


def scrape_autoexpress_reviews(url: str, vehicle_model: str, brand_hint: str) -> int:
    """Scrape AutoExpress review page via Playwright and extract review snippets."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[WARN] Playwright not installed. Run: pip install playwright && playwright install chromium")
        return 0

    added = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

            print(f"[AutoExpress] Scraping {vehicle_model} reviews from {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Look for review text elements (AutoExpress article/review structure)
            review_elements = page.query_selector_all(".article-summary, .review-body, .verdict-text, p.intro")
            if not review_elements:
                review_elements = page.query_selector_all("article p, .review p, .content-body p")

            texts_seen = set()
            for elem in review_elements[:15]:
                text = elem.inner_text().strip()
                if len(text) < 60 or text in texts_seen:
                    continue
                if not any(kw in text.lower() for kw in ["drive", "engine", "power", "interior", "range", "charge",
                                                           "comfort", "space", "performance", "steering", "handling",
                                                           "ride", "fuel", "price", "value", "quality"]):
                    continue
                texts_seen.add(text)

                analysis = analyze_with_gemini(text, brand_hint, vehicle_model)
                time.sleep(0.5)

                item_id = f"autoexpress_{abs(hash(text))}"
                item = {
                    "id": item_id,
                    "platform": "AutoExpress",
                    "author": "AutoExpress Expert",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "event": analysis.get("vehicle_model", vehicle_model),
                    "text": text[:500],
                    "sentiment": analysis.get("sentiment", "Neutral"),
                    "city": analysis.get("brand_group", "General"),
                    "isUpcoming": bool(analysis.get("isUpcoming")),
                    "parent_id": url,
                    "priority_score": int(analysis.get("priority_score", 2)),
                    "category_tag": analysis.get("category_tag", "General"),
                    "action_insight": analysis.get("action_insight", "No recommendation."),
                    "brand": brand_hint,
                }
                upsert_item(item)
                added += 1
                print(f"  [SUCCESS] Added AutoExpress snippet: {text[:50]}...")

            browser.close()
    except Exception as e:
        print(f"[ERROR] AutoExpress scraping failed for {url}: {e}")

    return added


def scrape_cardekho_reviews(url: str, vehicle_model: str, brand_hint: str) -> int:
    """Scrape CarDekho user review page via Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[WARN] Playwright not installed.")
        return 0

    added = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-IN,en;q=0.9",
            })

            print(f"[CarDekho] Scraping {vehicle_model} user reviews from {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            # CarDekho review text selectors
            review_selectors = [
                ".userReviewContent", ".reviewContent", ".reviewText",
                "[data-track='review_text']", ".review-desc", ".ugcReviewContent"
            ]

            texts_seen = set()
            for selector in review_selectors:
                elements = page.query_selector_all(selector)
                for elem in elements[:12]:
                    text = elem.inner_text().strip()
                    if len(text) < 50 or text in texts_seen:
                        continue
                    texts_seen.add(text)

                    # Try to get reviewer name
                    try:
                        author_elem = elem.query_selector(".reviewerName, .username, .author")
                        author = author_elem.inner_text().strip() if author_elem else "CarDekho User"
                    except Exception:
                        author = "CarDekho User"

                    analysis = analyze_with_gemini(text, brand_hint, vehicle_model)
                    time.sleep(0.5)

                    item_id = f"cardekho_{abs(hash(text))}"
                    item = {
                        "id": item_id,
                        "platform": "CarDekho",
                        "author": author,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "event": analysis.get("vehicle_model", vehicle_model),
                        "text": text[:500],
                        "sentiment": analysis.get("sentiment", "Neutral"),
                        "city": analysis.get("brand_group", "EV"),
                        "isUpcoming": bool(analysis.get("isUpcoming")),
                        "parent_id": url,
                        "priority_score": int(analysis.get("priority_score", 1)),
                        "category_tag": analysis.get("category_tag", "General"),
                        "action_insight": analysis.get("action_insight", "No recommendation."),
                        "brand": brand_hint,
                    }
                    upsert_item(item)
                    added += 1
                    print(f"  [SUCCESS] Added CarDekho review: {text[:50]}...")

            browser.close()
    except Exception as e:
        print(f"[ERROR] CarDekho scraping failed for {url}: {e}")

    return added


def main():
    total = 0

    # JLR — AutoExpress
    print("\n=== Scraping AutoExpress (JLR) ===")
    for url, vehicle_model, brand_hint in JLR_AUTOEXPRESS_URLS:
        added = scrape_autoexpress_reviews(url, vehicle_model, brand_hint)
        total += added
        time.sleep(3)

    # Tata — CarDekho
    print("\n=== Scraping CarDekho (Tata) ===")
    for url, vehicle_model, brand_hint in TATA_CARDEKHO_URLS:
        added = scrape_cardekho_reviews(url, vehicle_model, brand_hint)
        total += added
        time.sleep(3)

    print(f"\n=== Automotive portal scraping complete: {total} items added ===")


if __name__ == "__main__":
    main()
