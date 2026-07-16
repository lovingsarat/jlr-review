"""
reddit_scraper.py — Scrape public Reddit subreddits for JLR and Tata Motors reviews.
Uses Reddit's public JSON API (no authentication required).
Subreddits: r/landrover, r/jaguar, r/RangeRover, r/Defender, r/IndiaCars, r/TataMotors
"""
import os
import sys
import json
import sqlite3
import time
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")
GEMINI_MODEL = "gemini-3.1-flash-lite"

# Subreddits to scrape, with brand mapping
SUBREDDITS = {
    "landrover":    "jlr",
    "jaguar":       "jlr",
    "RangeRover":   "jlr",
    "Defender":     "jlr",
    "IndiaCars":    "tata",
    "TataMotors":   "tata",
    "indiancars":   "tata",
}

HEADERS = {
    "User-Agent": os.getenv("REDDIT_USER_AGENT", "JLRTataReviewBot/1.0 (by u/AutoReviewBot)")
}

JLR_KEYWORDS = [
    "jaguar", "land rover", "range rover", "landrover", "defender",
    "discovery", "f-pace", "fpace", "i-pace", "ipace", "e-pace", "epace",
    "velar", "evoque", "octa", "jlr",
]
TATA_KEYWORDS = [
    "tata", "nexon", "punch ev", "curvv", "harrier", "safari",
    "tiago ev", "tigor ev", "altroz", "xpres", "sierra ev",
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
    """Call Gemini to extract structured automotive review data."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key in ["MY_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"]:
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
Analyze this automotive Reddit post/review about {brand_hint.upper()}.
Brand context: {brand_context}

Return JSON with:
- "sentiment": "Positive", "Neutral", or "Negative"
- "brand": "jlr" or "tata"
- "brand_group": For JLR: "Jaguar"/"Range Rover"/"Defender"/"Discovery"; For Tata: "SUV"/"EV"/"Hatchback"/"Sedan"
- "vehicle_model": specific model (e.g. "Defender 110", "Nexon EV"). Use "General" if unclear.
- "isUpcoming": true if about future/upcoming/launch vehicle
- "category_tag": one of: Performance, EV Range, Comfort, Infotainment, Build Quality, After-Sales, Pricing, Safety, Off-road, Design, General
- "priority_score": 1–5 (1=minor comment, 5=critical safety issue)
- "action_insight": one actionable sentence for the brand's product/after-sales team

Text: "{text[:500]}"

JSON only (no markdown):
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
            import re
            match = re.search(r"\{.*\}", reply, re.DOTALL)
            if match:
                reply = match.group(0)
            return json.loads(reply)
    except Exception as e:
        print(f"[WARN] Gemini error: {e}")
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


def scrape_subreddit(subreddit: str, brand_hint: str, limit: int = 25) -> int:
    """Fetch top/new posts from a subreddit via public JSON endpoint."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json"
    params = {"limit": limit, "raw_json": 1}

    try:
        resp = httpx.get(url, headers=HEADERS, params=params, timeout=15.0, follow_redirects=True)
        if resp.status_code != 200:
            print(f"[WARN] Reddit r/{subreddit} returned HTTP {resp.status_code}")
            return 0
    except Exception as e:
        print(f"[ERROR] Failed to fetch r/{subreddit}: {e}")
        return 0

    posts = resp.json().get("data", {}).get("children", [])
    added = 0

    for post_wrapper in posts:
        post = post_wrapper.get("data", {})
        post_id = post.get("id", "")
        if not post_id:
            continue

        title = post.get("title", "")
        body = post.get("selftext", "")
        combined_text = f"{title}. {body}".strip()[:1000]

        # Skip very short or irrelevant posts
        if len(combined_text) < 30:
            continue
        if not is_automotive_relevant(combined_text):
            continue

        detected_brand = detect_brand(combined_text) if brand_hint == "auto" else brand_hint

        author = post.get("author", "RedditUser")
        created_utc = post.get("created_utc", 0)
        try:
            date_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            date_str = datetime.now().strftime("%Y-%m-%d")

        print(f"[Reddit] r/{subreddit}: {title[:60]}...")
        analysis = analyze_with_gemini(combined_text, detected_brand)
        time.sleep(0.5)  # Rate limit Gemini calls

        item = {
            "id": f"reddit_{post_id}",
            "platform": "Reddit",
            "author": f"u/{author}",
            "date": date_str,
            "event": analysis.get("vehicle_model", "General"),
            "text": combined_text[:500],
            "sentiment": analysis.get("sentiment", "Neutral"),
            "city": analysis.get("brand_group", "General"),
            "isUpcoming": bool(analysis.get("isUpcoming")),
            "parent_id": f"r/{subreddit}",
            "priority_score": int(analysis.get("priority_score", 1)),
            "category_tag": analysis.get("category_tag", "General"),
            "action_insight": analysis.get("action_insight", "No recommendation."),
            "brand": analysis.get("brand", detected_brand),
        }
        upsert_item(item)
        added += 1
        print(f"  [SUCCESS] Added Reddit post: reddit_{post_id}")

    return added


def also_scrape_comments(subreddit: str, brand_hint: str, post_limit: int = 5) -> int:
    """Fetch top comments from recent posts to capture owner experiences."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json"
    params = {"limit": post_limit, "raw_json": 1}
    added = 0

    try:
        resp = httpx.get(url, headers=HEADERS, params=params, timeout=15.0, follow_redirects=True)
        if resp.status_code != 200:
            return 0
        posts = resp.json().get("data", {}).get("children", [])
    except Exception:
        return 0

    for post_wrapper in posts[:post_limit]:
        post = post_wrapper.get("data", {})
        post_id = post.get("id", "")
        if not post_id:
            continue

        comments_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
        try:
            cresp = httpx.get(comments_url, headers=HEADERS, params={"raw_json": 1}, timeout=15.0, follow_redirects=True)
            if cresp.status_code != 200:
                continue
            data = cresp.json()
            if len(data) < 2:
                continue

            comments = data[1].get("data", {}).get("children", [])
            for c in comments[:8]:
                cdata = c.get("data", {})
                body = cdata.get("body", "").strip()
                if len(body) < 40 or not is_automotive_relevant(body):
                    continue

                detected_brand = detect_brand(body) if brand_hint == "auto" else brand_hint
                cid = cdata.get("id", "")
                author = cdata.get("author", "RedditUser")
                created_utc = cdata.get("created_utc", 0)
                try:
                    date_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")
                except Exception:
                    date_str = datetime.now().strftime("%Y-%m-%d")

                print(f"  [Comment] r/{subreddit}: {body[:50]}...")
                analysis = analyze_with_gemini(body, detected_brand)
                time.sleep(0.5)

                item = {
                    "id": f"reddit_c_{cid}",
                    "platform": "Reddit",
                    "author": f"u/{author}",
                    "date": date_str,
                    "event": analysis.get("vehicle_model", "General"),
                    "text": body[:500],
                    "sentiment": analysis.get("sentiment", "Neutral"),
                    "city": analysis.get("brand_group", "General"),
                    "isUpcoming": bool(analysis.get("isUpcoming")),
                    "parent_id": f"reddit_{post_id}",
                    "priority_score": int(analysis.get("priority_score", 1)),
                    "category_tag": analysis.get("category_tag", "General"),
                    "action_insight": analysis.get("action_insight", "No recommendation."),
                    "brand": analysis.get("brand", detected_brand),
                }
                upsert_item(item)
                added += 1

        except Exception as e:
            print(f"[WARN] Error fetching comments for {post_id}: {e}")
        time.sleep(1)  # Be polite to Reddit's servers

    return added


def main():
    total = 0
    for subreddit, brand_hint in SUBREDDITS.items():
        print(f"\n=== Scraping r/{subreddit} (brand: {brand_hint}) ===")
        added = scrape_subreddit(subreddit, brand_hint, limit=25)
        total += added
        # Also grab top comments for richer owner feedback
        added_c = also_scrape_comments(subreddit, brand_hint, post_limit=5)
        total += added_c
        time.sleep(2)  # Respect Reddit rate limits

    print(f"\n=== Reddit scraping complete: {total} items added ===")


if __name__ == "__main__":
    main()
