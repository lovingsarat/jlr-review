import os
import sys
import asyncio
import json
import sqlite3
from datetime import datetime
from twikit import Client
import httpx
from dotenv import load_dotenv

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")

# Official brand accounts to monitor on Twitter/X (verified handles)
JLR_ACCOUNTS = [
    "LandRover",       # @LandRover — official global
    "Jaguar",          # @Jaguar — official global
    "RangeRoverUSA",   # @RangeRoverUSA — US Range Rover official
    "LandRoverNA",     # @LandRoverNA — North America
    "Defender",        # @Defender — Defender official
]
TATA_ACCOUNTS = [
    "TataMotors",      # @TataMotors — official
    "TataMotorsCars",  # @TataMotorsCars — passenger vehicles
    "TataNexonEV",     # @TataNexonEV
    "TataMotorsAlert", # @TataMotorsAlert — announcements
]
ALL_BRAND_ACCOUNTS = JLR_ACCOUNTS + TATA_ACCOUNTS

# Load environment
load_dotenv(dotenv_path="../.env")
load_dotenv()

# Initialize Twikit Client
GEMINI_MODEL = "gemini-3.1-flash-lite"
client = Client("en-US")

# ─── JLR / Tata relevance keywords ──────────────────────────────────────────
JLR_KEYWORDS = [
    "jaguar", "land rover", "range rover", "landrover", "defender",
    "discovery", "f-pace", "fpace", "i-pace", "ipace", "e-pace", "epace",
    "velar", "evoque", "octa", "jlr", "freelander",
]
TATA_KEYWORDS = [
    "tata motors", "tata nexon", "nexon ev", "tata punch", "punch ev",
    "curvv", "tata harrier", "harrier ev", "tata safari", "tiago ev",
    "tata tiago", "tigor ev", "tata tigor", "altroz", "tata altroz",
    "xpres-t", "xpres ev", "sierra ev", "tata sierra",
]
ALL_AUTOMOTIVE_KEYWORDS = JLR_KEYWORDS + TATA_KEYWORDS


def is_automotive_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in ALL_AUTOMOTIVE_KEYWORDS)


def detect_brand(text: str) -> str:
    """Return 'jlr' or 'tata' based on keyword presence, default 'jlr'."""
    text_lower = text.lower()
    jlr_hits = sum(1 for kw in JLR_KEYWORDS if kw in text_lower)
    tata_hits = sum(1 for kw in TATA_KEYWORDS if kw in text_lower)
    return "tata" if tata_hits > jlr_hits else "jlr"


# ─── Twitter session loading ─────────────────────────────────────────────────
def load_twitter_session():
    """Load Twitter session using env cookies, cookies.json, or login fallback.
    Returns True if session is ready, False otherwise."""
    auth_token = os.getenv("TWITTER_AUTH_TOKEN", "")
    ct0 = os.getenv("TWITTER_CT0", "")
    if auth_token and ct0 and auth_token != "your_auth_token" and ct0 != "your_ct0":
        try:
            client.set_cookies({"auth_token": auth_token, "ct0": ct0})
            print("Loaded Twitter session from .env cookies (auth_token + ct0).")
            return True
        except Exception as e:
            print(f"[WARN] Failed to set cookies from .env: {e}")

    cookies_file = "cookies.json"
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, "r") as f:
                cookies_data = json.load(f)
            if isinstance(cookies_data, list):
                cookies_dict = {c["name"]: c["value"] for c in cookies_data if "name" in c and "value" in c}
                client.set_cookies(cookies_dict)
                print("Loaded Twitter session from cookies.json (array format).")
                return True
            elif isinstance(cookies_data, dict):
                if "ct0" in cookies_data or "auth_token" in cookies_data:
                    client.set_cookies(cookies_data)
                    print("Loaded Twitter session from cookies.json (dict format).")
                    return True
        except Exception as e:
            print(f"[WARN] Failed to load cookies.json: {e}")

    username = os.getenv("TWITTER_USERNAME")
    email = os.getenv("TWITTER_EMAIL")
    password = os.getenv("TWITTER_PASSWORD")
    if username and username != "your_username":
        print(f"Attempting X login with username: {username}...")
        try:
            asyncio.get_event_loop().run_until_complete(
                client.login(auth_info_1=username, auth_info_2=email, password=password)
            )
            client.save_cookies(cookies_file)
            print("Successfully logged in and saved session.")
            return True
        except Exception as e:
            print(f"[ERROR] X login failed: {e}")
    else:
        print("[WARNING] No Twitter credentials or cookies found. Skipping X scraping.")
    return False


# ─── Gemini JSON extraction helpers ─────────────────────────────────────────
def make_json_valid(s: str) -> str:
    """Extract the first valid JSON object from a string."""
    import re
    s = s.strip()
    match = re.search(r"\{.*\}", s, re.DOTALL)
    if not match:
        return s
    candidate = match.group(0)
    while candidate.endswith("}"):
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError as e:
            if "Extra data" in str(e) or "Expecting" in str(e):
                candidate = candidate.rstrip()
                last_brace = candidate.rfind("}")
                if last_brace == -1:
                    break
                candidate = candidate[:last_brace].rstrip()
            else:
                break
    return s


# ─── Gemini Automotive Analysis ──────────────────────────────────────────────
def analyze_review_with_gemini(text: str, brand_hint: str = "jlr") -> dict:
    """
    Analyze an automotive review/social post using Gemini.
    brand_hint: 'jlr' or 'tata' — provides context to the model.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key in ["MY_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"]:
        return _default_analysis(brand_hint, text)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    brand_context = (
        "JLR (Jaguar Land Rover) brands: Jaguar (F-PACE, E-PACE, I-PACE and upcoming EVs), "
        "Range Rover (Range Rover, Range Rover Sport, Velar, Evoque), "
        "Defender (Defender 90, 110, 130, OCTA), Discovery (Discovery, Discovery Sport)."
        if brand_hint == "jlr" else
        "Tata Motors brands: Tiago, Tiago EV, Tigor, Tigor EV, Altroz, Punch, Punch EV, "
        "Nexon, Nexon EV, Curvv, Curvv EV, Harrier, Harrier EV, Safari, Sierra, Sierra EV, XPRES (fleet EV)."
    )

    prompt = f"""
    Analyze the following social media post or review about an automotive brand ({brand_hint.upper()}).
    Brand context: {brand_context}

    Extract the following in strict JSON format:

    1. "sentiment": Must be "Positive", "Neutral", or "Negative".
       - "Negative" only if there is explicit complaint, reliability issue, safety concern, or significant dissatisfaction.
       - "Positive" for praise, satisfaction, excitement, or community enthusiasm.
       - "Neutral" for factual questions, news, or balanced observations.

    2. "brand": Must be "jlr" or "tata" — which automotive group this review belongs to.

    3. "brand_group": The sub-brand or segment:
       - For JLR: "Jaguar", "Range Rover", "Defender", or "Discovery"
       - For Tata: "SUV", "EV", "Hatchback", or "Sedan"
       - If unclear, use the most likely based on model name.

    4. "vehicle_model": The specific model name mentioned (e.g., "Defender 110", "Nexon EV", "Range Rover Sport").
       If no specific model is mentioned, use the brand_group + " General" (e.g., "Defender General").

    5. "isUpcoming": true if this is about a future/upcoming/launch vehicle or pre-release model,
       false if it's about an existing production vehicle.

    6. "category_tag": The single most relevant review theme from this list ONLY:
       "Performance", "EV Range", "Comfort", "Infotainment", "Build Quality",
       "After-Sales", "Pricing", "Safety", "Off-road", "Design", "General"

    7. "priority_score": Integer 1–5 indicating urgency/importance:
       1 = general comment or praise
       2 = minor concern or question
       3 = moderate complaint or issue
       4 = significant defect, safety concern, or viral negative post
       5 = critical safety recall, severe reliability failure, or PR risk

    8. "action_insight": A single actionable sentence for the product or after-sales team
       based on this review. If positive, suggest how to sustain or amplify.

    Review Text:
    "{text}"

    Output JSON directly (no markdown, no wrapping):
    """

    try:
        response = httpx.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
            },
            timeout=20.0,
        )
        if response.status_code == 200:
            res_data = response.json()
            reply = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()

            import re
            match = re.search(r"\{.*\}", reply, re.DOTALL)
            if match:
                reply = match.group(0)

            reply = make_json_valid(reply)
            return json.loads(reply)
    except Exception as e:
        print(f"Error parsing review with Gemini: {e}. Raw reply: {reply if 'reply' in locals() else 'None'}")

    return _default_analysis(brand_hint, text)


def _default_analysis(brand_hint: str, text: str = "") -> dict:
    """Fallback analysis when Gemini API is unavailable."""
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


# ─── Slack Notification for Critical Issues ───────────────────────────────
def send_slack_alert(item: dict):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url or webhook_url == "your_slack_webhook_url":
        return

    brand_name = "JLR (Jaguar Land Rover)" if item.get("brand") == "jlr" else "Tata Motors"
    emoji = "🚨" if item.get("priority_score", 1) == 5 else "⚠️"
    
    payload = {
        "text": f"{emoji} *CRITICAL FEEDBACK DETECTED — {brand_name.upper()}*",
        "attachments": [
            {
                "color": "#ef4444" if item.get("priority_score", 1) == 5 else "#f59e0b",
                "fields": [
                    {"title": "Vehicle Model", "value": item.get("event", "General"), "short": True},
                    {"title": "Platform", "value": item.get("platform", "Unknown"), "short": True},
                    {"title": "Author", "value": item.get("author", "Anonymous"), "short": True},
                    {"title": "Theme", "value": item.get("category_tag", "General"), "short": True},
                    {"title": "Priority Score", "value": "★" * item.get("priority_score", 1), "short": True},
                    {"title": "Actionable Insight", "value": item.get("action_insight", "None"), "short": False}
                ],
                "text": f"*{item.get('author')}:* {item.get('text')}"
            }
        ]
    }
    
    try:
        # Use simple httpx request to send webhook
        resp = httpx.post(webhook_url, json=payload, timeout=5.0)
        if resp.status_code == 200:
            print(f"[Slack] Successfully sent alert for priority {item.get('priority_score')}")
        else:
            print(f"[Slack] Failed to send alert: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[Slack] Error sending webhook: {e}")


# ─── SQLite upsert ───────────────────────────────────────────────────────────
def upsert_feedback_local(item: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_items (
            id TEXT PRIMARY KEY,
            platform TEXT,
            author TEXT,
            date TEXT,
            event TEXT,
            text TEXT,
            sentiment TEXT,
            city TEXT,
            isUpcoming INTEGER,
            parent_id TEXT,
            priority_score INTEGER,
            category_tag TEXT,
            action_insight TEXT
        )
    """)
    # Add brand column if it doesn't exist (safe migration)
    for col, col_type in [
        ("parent_id", "TEXT"),
        ("priority_score", "INTEGER"),
        ("category_tag", "TEXT"),
        ("action_insight", "TEXT"),
        ("brand", "TEXT"),
    ]:
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
        item["event"], item["text"], item["sentiment"],
        item["city"],                          # brand_group stored here
        1 if item.get("isUpcoming") else 0,
        item.get("parent_id"),
        item.get("priority_score", 1),
        item.get("category_tag", "General"),
        item.get("action_insight", "No recommendation."),
        item.get("brand", "jlr"),
    ))
    conn.commit()
    conn.close()

    # Trigger Slack alert for Priority 5 critical issues
    if int(item.get("priority_score", 1)) == 5:
        send_slack_alert(item)


# ─── Scraper 1: Official Twitter API v2 ─────────────────────────────────────
async def run_official_api_scraper(bearer_token: str):
    headers = {"Authorization": f"Bearer {bearer_token}"}

    JLR_QUERY = (
        '("Range Rover" OR "Defender" OR "Jaguar" OR "Discovery" OR "I-PACE" OR "Defender 110" OR "F-PACE") '
        "lang:en -is:retweet"
    )
    TATA_QUERY = (
        '("Nexon EV" OR "Tata Punch" OR "Curvv EV" OR "Tata Harrier" OR "Tata Safari" OR "Tiago EV" OR "Sierra EV") '
        "lang:en -is:retweet"
    )

    queries = {
        "jlr_reviews": (JLR_QUERY, "jlr"),
        "tata_reviews": (TATA_QUERY, "tata"),
        "brand_mentions": (
            " OR ".join([f"@{acc}" for acc in ALL_BRAND_ACCOUNTS]) + " lang:en -is:retweet",
            "auto"
        ),
    }

    total_added = 0
    async with httpx.AsyncClient() as http_client:
        for category, (query_string, brand_hint) in queries.items():
            print(f"\n--- Fetching category: {category} (Official API) ---")
            url = "https://api.twitter.com/2/tweets/search/recent"
            params = {
                "query": query_string,
                "tweet.fields": "created_at",
                "expansions": "author_id",
                "user.fields": "username,name",
                "max_results": 10,
            }
            try:
                response = await http_client.get(url, headers=headers, params=params, timeout=15.0)
                if response.status_code == 429:
                    print("[ERROR] Official X API Rate Limited. Please wait.")
                    break
                if response.status_code != 200:
                    print(f"[ERROR] Official X API returned {response.status_code}: {response.text}")
                    continue

                resp_json = response.json()
                tweets = resp_json.get("data", [])
                users = {u["id"]: u for u in resp_json.get("includes", {}).get("users", [])}

                for tweet in tweets:
                    tweet_id = f"twitter_{tweet['id']}"
                    author_id = tweet.get("author_id")
                    user_info = users.get(author_id, {})
                    screen_name = user_info.get("username", "XUser")

                    # Automotive relevance gate
                    detected_brand = detect_brand(tweet["text"]) if brand_hint == "auto" else brand_hint
                    if not is_automotive_relevant(tweet["text"]):
                        print(f"[SKIP] Non-automotive content from @{screen_name}")
                        continue

                    print(f"Found tweet by: {user_info.get('name', 'User')} (@{screen_name})")
                    analysis = analyze_review_with_gemini(tweet["text"], detected_brand)

                    try:
                        date_str = tweet["created_at"][:10]
                    except Exception:
                        date_str = datetime.now().strftime("%Y-%m-%d")

                    new_item = {
                        "id": tweet_id,
                        "platform": "Twitter",
                        "author": f"@{screen_name}",
                        "date": date_str,
                        "event": analysis.get("vehicle_model", "General"),
                        "text": tweet["text"],
                        "sentiment": analysis.get("sentiment", "Neutral"),
                        "city": analysis.get("brand_group", "General"),
                        "isUpcoming": bool(analysis.get("isUpcoming")),
                        "parent_id": None,
                        "priority_score": int(analysis.get("priority_score", 1)),
                        "category_tag": analysis.get("category_tag", "General"),
                        "action_insight": analysis.get("action_insight", "No recommendation."),
                        "brand": analysis.get("brand", detected_brand),
                    }
                    upsert_feedback_local(new_item)
                    total_added += 1
                    print(f"[SUCCESS] Added tweet: {tweet['id']}")
            except Exception as e:
                print(f"Error fetching category {category}: {e}")

            await asyncio.sleep(2)

    print(f"\nOfficial API ingestion complete! Processed {total_added} items.")


# ─── Scraper 2: Twikit Browser Scraper (Fallback) ───────────────────────────
async def run_twikit_scraper():
    if not load_twitter_session():
        return

    queries = {
        "jlr_reviews": (
            '("Range Rover" OR "Land Rover Defender" OR "Jaguar I-PACE" OR "Discovery Sport") '
            '("review" OR "owner" OR "reliability" OR "problem") lang:en -is:retweet',
            "jlr",
        ),
        "jlr_ev": (
            '("Jaguar EV" OR "I-PACE range" OR "JLR electric" OR "Range Rover PHEV") '
            "lang:en -is:retweet",
            "jlr",
        ),
        "tata_ev_reviews": (
            '("Nexon EV" OR "Punch EV" OR "Curvv EV" OR "Tata EV") '
            '("review" OR "range" OR "charging" OR "experience") lang:en -is:retweet',
            "tata",
        ),
        "tata_launch": (
            '("Harrier EV" OR "Sierra EV" OR "Tata Curvv" OR "Tata Safari") '
            '("launch" OR "booking" OR "price" OR "delivery") lang:en -is:retweet',
            "tata",
        ),
        "jlr_brand_mentions": (
            " OR ".join([f"@{acc}" for acc in JLR_ACCOUNTS]) + " lang:en -is:retweet",
            "jlr",
        ),
        "tata_brand_mentions": (
            " OR ".join([f"@{acc}" for acc in TATA_ACCOUNTS]) + " lang:en -is:retweet",
            "tata",
        ),
    }

    total_added = 0
    for category, (query_string, brand_hint) in queries.items():
        print(f"\n--- Fetching category: {category} (Twikit) ---")
        try:
            tweets = await client.search_tweet(query_string, product="Latest")
            for tweet in tweets:
                try:
                    tweet_id = f"twitter_{tweet.id}"
                    text_lower = tweet.text.lower()

                    if not is_automotive_relevant(tweet.text):
                        safe_name = tweet.user.screen_name.encode("ascii", "ignore").decode()
                        print(f"[SKIP] Non-automotive content from @{safe_name}")
                        continue

                    detected_brand = detect_brand(tweet.text) if brand_hint == "auto" else brand_hint
                    safe_name = tweet.user.name.encode("ascii", "ignore").decode()
                    safe_screen = tweet.user.screen_name.encode("ascii", "ignore").decode()
                    print(f"Found tweet by: {safe_name} (@{safe_screen})")

                    analysis = analyze_review_with_gemini(tweet.text, detected_brand)

                    try:
                        if isinstance(tweet.created_at, str):
                            dt = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
                            date_str = dt.strftime("%Y-%m-%d")
                        else:
                            date_str = tweet.created_at.strftime("%Y-%m-%d")
                    except Exception:
                        date_str = datetime.now().strftime("%Y-%m-%d")

                    # Find which brand account was tagged
                    tagged_account = None
                    for account in ALL_BRAND_ACCOUNTS:
                        if f"@{account.lower()}" in text_lower:
                            tagged_account = f"@{account}"
                            break

                    new_item = {
                        "id": tweet_id,
                        "platform": "Twitter",
                        "author": f"@{tweet.user.screen_name}",
                        "date": date_str,
                        "event": analysis.get("vehicle_model", "General"),
                        "text": tweet.text,
                        "sentiment": analysis.get("sentiment", "Neutral"),
                        "city": analysis.get("brand_group", "General"),
                        "isUpcoming": bool(analysis.get("isUpcoming")),
                        "parent_id": tagged_account,
                        "priority_score": int(analysis.get("priority_score", 1)),
                        "category_tag": analysis.get("category_tag", "General"),
                        "action_insight": analysis.get("action_insight", "No recommendation."),
                        "brand": analysis.get("brand", detected_brand),
                    }
                    upsert_feedback_local(new_item)
                    total_added += 1
                    print(f"[SUCCESS] Added tweet: {tweet.id}")

                except Exception as tweet_err:
                    print(f"[WARN] Skipping tweet: {str(tweet_err).encode('ascii', 'ignore').decode()}")
                    continue

        except Exception as e:
            print(f"Error searching category {category}: {str(e).encode('ascii', 'ignore').decode()}")

        await asyncio.sleep(5)

    print(f"\nTwikit ingestion complete! Processed {total_added} items.")


# ─── Scraper 3: Official brand account tweets ────────────────────────────────
async def run_account_scraper():
    """Fetch recent tweets from official JLR and Tata brand accounts."""
    if not load_twitter_session():
        return

    total_added = 0
    for account in ALL_BRAND_ACCOUNTS:
        brand_hint = "tata" if account in TATA_ACCOUNTS else "jlr"
        print(f"\n--- Fetching tweets from @{account} ---")
        try:
            user = await client.get_user_by_screen_name(account)
            if not user:
                print(f"[WARN] Could not find user @{account}")
                continue

            tweets = await client.get_user_tweets(user.id, tweet_type="Tweets")
            if not tweets:
                print(f"[INFO] No recent tweets found for @{account}")
                continue

            tweet_list = list(tweets) if tweets else []
            print(f"[INFO] Found {len(tweet_list)} tweets for @{account}")

            for tweet in tweet_list:
                try:
                    tweet_id = f"twitter_{tweet.id}"
                    analysis = analyze_review_with_gemini(tweet.text, brand_hint)

                    try:
                        if isinstance(tweet.created_at, str):
                            dt = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
                            date_str = dt.strftime("%Y-%m-%d")
                        else:
                            date_str = tweet.created_at.strftime("%Y-%m-%d")
                    except Exception:
                        date_str = datetime.now().strftime("%Y-%m-%d")

                    new_item = {
                        "id": tweet_id,
                        "platform": "Twitter",
                        "author": f"@{account}",
                        "date": date_str,
                        "event": analysis.get("vehicle_model", "General"),
                        "text": tweet.text,
                        "sentiment": analysis.get("sentiment", "Neutral"),
                        "city": analysis.get("brand_group", "General"),
                        "isUpcoming": bool(analysis.get("isUpcoming")),
                        "parent_id": None,
                        "priority_score": int(analysis.get("priority_score", 1)),
                        "category_tag": analysis.get("category_tag", "General"),
                        "action_insight": analysis.get("action_insight", "No recommendation."),
                        "brand": brand_hint,
                    }
                    upsert_feedback_local(new_item)
                    total_added += 1
                    print(f"[SUCCESS] Added tweet from @{account}: {tweet.id}")
                except Exception as tweet_err:
                    print(f"[WARN] Skipping tweet: {str(tweet_err).encode('ascii', 'ignore').decode()}")
                    continue
        except Exception as e:
            import traceback
            print(f"Error fetching @{account}: {str(e).encode('ascii', 'ignore').decode()}")
            traceback.print_exc()
        await asyncio.sleep(3)

    print(f"\nOfficial account ingestion complete! Processed {total_added} items.")


# ─── Scraper 4: Reddit public JSON ──────────────────────────────────────────
def run_reddit_scraper():
    """Scrape public Reddit subreddits for JLR and Tata reviews via public JSON API.
    No authentication required. Runs in-process (no asyncio conflicts)."""
    import subprocess
    reddit_script = os.path.join(os.path.dirname(__file__), "reddit_scraper.py")
    if not os.path.exists(reddit_script):
        print("[WARN] reddit_scraper.py not found. Skipping Reddit scraping.")
        return
    print("\n--- Starting Reddit scraper ---")
    result = subprocess.run([sys.executable, reddit_script], cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        print("[WARN] Reddit scraper exited with errors.")


# ─── Scraper 5: Automotive portal (AutoExpress/CarDekho via Playwright) ──────
def run_autoportal_scraper():
    """Scrape automotive review portals. Runs autoportal_scraper.py as subprocess."""
    import subprocess
    portal_script = os.path.join(os.path.dirname(__file__), "autoportal_scraper.py")
    if not os.path.exists(portal_script):
        print("[WARN] autoportal_scraper.py not found. Skipping portal scraping.")
        return
    print("\n--- Starting Automotive Portal scraper (Playwright) ---")
    result = subprocess.run([sys.executable, portal_script], cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        print("[WARN] Autoportal scraper exited with errors.")


# ─── DB deduplication ────────────────────────────────────────────────────────
def deduplicate_db():
    import re as _re
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, platform, author, date, event, text, sentiment, city, isUpcoming, parent_id FROM feedback_items"
    )
    rows = cursor.fetchall()

    def get_tokens(text):
        return set(_re.findall(r"[a-z0-9£]+", text.lower()))

    def is_near_dup(a, b):
        ta, tb = get_tokens(a), get_tokens(b)
        if not ta and not tb:
            return True
        shared = ta & tb
        union = ta | tb
        return len(union) > 0 and len(shared) / len(union) >= 0.85

    def score(item):
        return (
            (4 if item[8] else 0)
            + (2 if item[4] not in ("General", "General Review") else 0)
            + (1 if item[6] != "Neutral" else 0)
        )

    unique = []
    for row in rows:
        dup_idx = next(
            (
                i for i, existing in enumerate(unique)
                if existing[1].lower() == row[1].lower()
                and existing[2].lower() == row[2].lower()
                and existing[3] == row[3]
                and is_near_dup(existing[5], row[5])
            ),
            -1,
        )
        if dup_idx == -1:
            unique.append(row)
        elif score(row) > score(unique[dup_idx]):
            unique[dup_idx] = row

    before = len(rows)
    after = len(unique)

    if before != after:
        cursor.execute("DELETE FROM feedback_items")
        for row in unique:
            cursor.execute(
                "INSERT INTO feedback_items (id, platform, author, date, event, text, sentiment, city, isUpcoming, parent_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
        conn.commit()
        print(f"\nDeduplicated DB: {before} -> {after} items (removed {before - after} duplicates)")
    else:
        print(f"\nNo duplicates found in DB ({before} items).")

    conn.close()


# ─── Main orchestrator ───────────────────────────────────────────────────────
async def run_scraper():
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if bearer_token and bearer_token != "your_bearer_token":
        await run_official_api_scraper(bearer_token)
    else:
        await run_twikit_scraper()

    # Fetch from official brand accounts
    await run_account_scraper()

    # Reddit public scraping (no auth needed)
    import threading
    reddit_thread = threading.Thread(target=run_reddit_scraper)
    reddit_thread.start()
    reddit_thread.join()

    # Automotive portals (AutoExpress, CarDekho via Playwright)
    portal_thread = threading.Thread(target=run_autoportal_scraper)
    portal_thread.start()
    portal_thread.join()

    # Deduplicate DB
    deduplicate_db()

    # Auto-export to data.json
    print("\n--- Exporting to data.json ---")
    import subprocess
    export_script = os.path.join(os.path.dirname(__file__), "export_data.py")
    subprocess.run([sys.executable, export_script], cwd=os.path.dirname(__file__))


if __name__ == "__main__":
    asyncio.run(run_scraper())
