"""
slack_scraper.py — Scrapes message history from a configured Slack channel
using the Slack Web API, runs them through Gemini for analysis, and saves them to the DB.

Requirements:
- SLACK_API_TOKEN (starts with xoxb-)
- SLACK_CHANNEL_ID (starts with C)
"""
import os
import sys
import json
import sqlite3
import time
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

# Load environment configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")
GEMINI_MODEL = "gemini-3.1-flash-lite"

JLR_KEYWORDS = [
    "jaguar", "land rover", "range rover", "landrover", "defender",
    "discovery", "f-pace", "i-pace", "e-pace", "velar", "evoque", "octa"
]
TATA_KEYWORDS = [
    "tata", "nexon", "punch ev", "curvv", "harrier", "safari",
    "tiago ev", "tigor ev", "altroz", "xpres", "sierra"
]

def is_automotive_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in JLR_KEYWORDS + TATA_KEYWORDS)

def detect_brand(text: str) -> str:
    text_lower = text.lower()
    tata_hits = sum(1 for kw in TATA_KEYWORDS if kw in text_lower)
    jlr_hits = sum(1 for kw in JLR_KEYWORDS if kw in text_lower)
    return "tata" if tata_hits > jlr_hits else "jlr"

def analyze_with_gemini(text: str, brand_hint: str) -> dict:
    """Classifies the Slack message details using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _default_analysis(brand_hint)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    brand_context = (
        "JLR: Jaguar (F-PACE, E-PACE, I-PACE), Range Rover (Range Rover, Sport, Velar, Evoque), "
        "Defender (90, 110, 130, OCTA), Discovery (Discovery, Discovery Sport)."
        if brand_hint == "jlr" else
        "Tata Motors: Tiago, Tiago EV, Tigor, Tigor EV, Altroz, Punch, Punch EV, "
        "Nexon, Nexon EV, Curvv, Curvv EV, Harrier, Harrier EV, Safari, Sierra, Sierra EV, XPRES."
    )

    prompt = f"""
Analyze this Slack channel message containing user/owner automotive feedback.
Brand context: {brand_context}

Return JSON with:
- "sentiment": "Positive", "Neutral", or "Negative"
- "brand": "{brand_hint}"
- "brand_group": For JLR: "Jaguar"/"Range Rover"/"Defender"/"Discovery"; For Tata: "SUV"/"EV"/"Hatchback"/"Sedan"
- "vehicle_model": specific model (e.g. "Defender 110", "Nexon EV"). Use "General" if unclear.
- "isUpcoming": true if about future/upcoming/launch vehicle
- "category_tag": one of: Performance, EV Range, Comfort, Infotainment, Build Quality, After-Sales, Pricing, Safety, Off-road, Design, General
- "priority_score": 1-5
- "action_insight": one actionable sentence for the product team

Text: "{text[:400]}"

JSON only (no markdown):
"""
    try:
        resp = httpx.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
            },
            timeout=20.0
        )
        if resp.status_code == 200:
            reply = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            import re
            match = re.search(r"\{.*\}", reply, re.DOTALL)
            if match:
                reply = match.group(0)
            return json.loads(reply)
    except Exception as e:
        print(f"[Slack Scraper] Gemini error: {e}")
    return _default_analysis(brand_hint)

def _default_analysis(brand_hint: str) -> dict:
    return {
        "sentiment": "Neutral",
        "brand": brand_hint,
        "brand_group": "Range Rover" if brand_hint == "jlr" else "SUV",
        "vehicle_model": "General",
        "isUpcoming": False,
        "priority_score": 1,
        "category_tag": "General",
        "action_insight": "No recommendation."
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
    # Ensure fields are aligned
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

def scrape_slack_history(limit: int = 40) -> int:
    token = os.getenv("SLACK_API_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    
    if not token or token == "your_slack_bot_token" or not channel_id:
        print("[Slack Scraper] Config missing. Skipping Slack ingestion.")
        return 0

    print(f"[Slack Scraper] Fetching history from channel: {channel_id}")
    url = "https://slack.com/api/conversations.history"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "channel": channel_id,
        "limit": limit
    }

    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=15.0)
        if resp.status_code != 200:
            print(f"[Slack Scraper] HTTP Error: {resp.status_code}")
            return 0
        
        data = resp.json()
        if not data.get("ok"):
            print(f"[Slack Scraper] Slack API Error: {data.get('error')}")
            return 0
            
        messages = data.get("messages", [])
        print(f"[Slack Scraper] Found {len(messages)} messages.")
    except Exception as e:
        print(f"[Slack Scraper] Request failed: {e}")
        return 0

    added = 0
    for msg in messages:
        # Ignore bot messages or system join messages
        if msg.get("subtype") or not msg.get("text"):
            continue
            
        text = msg["text"].strip()
        if len(text) < 15 or not is_automotive_relevant(text):
            continue

        msg_id = f"slack_{msg['ts'].replace('.', '_')}"
        user_id = msg.get("user", "SlackUser")
        
        # Format date from epoch float timestamp ts
        epoch = float(msg["ts"])
        date_str = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")
        
        detected_brand = detect_brand(text)
        print(f"[Slack] Processing message: {text[:50]}...")
        analysis = analyze_with_gemini(text, detected_brand)
        
        item = {
            "id": msg_id,
            "platform": "Slack",
            "author": f"@{user_id}",
            "date": date_str,
            "event": analysis.get("vehicle_model", "General"),
            "text": text[:500],
            "sentiment": analysis.get("sentiment", "Neutral"),
            "city": analysis.get("brand_group", "General"),
            "isUpcoming": bool(analysis.get("isUpcoming")),
            "parent_id": channel_id,
            "priority_score": int(analysis.get("priority_score", 1)),
            "category_tag": analysis.get("category_tag", "General"),
            "action_insight": analysis.get("action_insight", "No recommendation."),
            "brand": analysis.get("brand", detected_brand)
        }
        upsert_item(item)
        added += 1
        time.sleep(0.5)

    return added

if __name__ == "__main__":
    added = scrape_slack_history()
    print(f"[Slack Scraper] Finished. Ingested {added} reviews.")
