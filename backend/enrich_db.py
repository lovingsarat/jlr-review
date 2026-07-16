"""
enrich_db.py — Re-analyse all existing DB rows with Gemini that have 'Neutral' sentiment
and no category_tag (i.e., they got the default_analysis fallback).
Run after scraper.py to ensure all tweets get proper Gemini analysis.
"""
import os
import sqlite3
import time
import json
import httpx
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")
GEMINI_MODEL = "gemini-3.1-flash-lite"

JLR_CONTEXT = (
    "JLR: Jaguar (F-PACE, E-PACE, I-PACE), Range Rover (Range Rover, Sport, Velar, Evoque), "
    "Defender (90, 110, 130, OCTA), Discovery (Discovery, Discovery Sport)."
)
TATA_CONTEXT = (
    "Tata Motors: Tiago, Tiago EV, Tigor, Tigor EV, Altroz, Punch, Punch EV, "
    "Nexon, Nexon EV, Curvv, Curvv EV, Harrier, Harrier EV, Safari, Sierra, Sierra EV, XPRES."
)


def analyze(text: str, brand: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {}

    ctx = JLR_CONTEXT if brand == "jlr" else TATA_CONTEXT
    prompt = f"""
Analyze this automotive social media post/tweet from {brand.upper()}.
Brand context: {ctx}

Return JSON with ONLY these keys:
- "sentiment": "Positive", "Neutral", or "Negative"
- "brand_group": For JLR: "Jaguar"/"Range Rover"/"Defender"/"Discovery"; For Tata: "SUV"/"EV"/"Hatchback"/"Sedan"
- "vehicle_model": specific model (e.g. "Defender 110", "Nexon EV"). Use "General" if unclear.
- "isUpcoming": true if about future/upcoming/launch vehicle
- "category_tag": one of: Performance, EV Range, Comfort, Infotainment, Build Quality, After-Sales, Pricing, Safety, Off-road, Design, General
- "priority_score": 1-5
- "action_insight": one actionable sentence for the brand team

Text: "{text[:400]}"

JSON only (no markdown):
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    try:
        resp = httpx.post(url, json={"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}},
                          timeout=25.0)
        if resp.status_code == 200:
            data = resp.json()
            reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            match = re.search(r"\{.*\}", reply, re.DOTALL)
            if match:
                return json.loads(match.group(0))
    except Exception as e:
        print(f"  [WARN] Gemini error: {e}")
    return {}


def enrich():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get rows that got default analysis (Neutral + General category_tag)
    cursor.execute("""
        SELECT id, text, brand, city, event
        FROM feedback_items
        WHERE sentiment = 'Neutral'
        AND (category_tag IS NULL OR category_tag = 'General')
        ORDER BY id
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} rows to enrich with Gemini...")

    enriched = 0
    skipped = 0
    for row in rows:
        result = analyze(row["text"], row["brand"] or "jlr")
        if not result:
            skipped += 1
            continue

        cursor.execute("""
            UPDATE feedback_items
            SET sentiment=?, city=?, event=?, isUpcoming=?,
                priority_score=?, category_tag=?, action_insight=?
            WHERE id=?
        """, (
            result.get("sentiment", "Neutral"),
            result.get("brand_group", row["city"] or "General"),
            result.get("vehicle_model", row["event"] or "General"),
            1 if result.get("isUpcoming") else 0,
            int(result.get("priority_score", 1)),
            result.get("category_tag", "General"),
            result.get("action_insight", "No recommendation."),
            row["id"]
        ))
        conn.commit()
        enriched += 1
        s = result.get("sentiment", "Neutral")
        m = result.get("vehicle_model", "?")
        ct = result.get("category_tag", "?")
        print(f"  [{enriched}] {row['id'][:30]} -> {s} | {m} | #{ct}")
        time.sleep(0.6)  # Rate limit: ~100 RPM on free tier

    conn.close()
    print(f"\nEnrichment complete: {enriched} enriched, {skipped} skipped.")

    # Re-run export
    print("\nRunning export_data.py...")
    import subprocess, sys
    export_script = os.path.join(os.path.dirname(__file__), "export_data.py")
    subprocess.run([sys.executable, export_script], cwd=os.path.dirname(__file__))


if __name__ == "__main__":
    enrich()
