"""
export_data.py — Export diaspora.db to frontend/public/data.json

Reads all automotive reviews (JLR + Tata) from SQLite, deduplicates,
computes per-brand analytics, and writes the data.json consumed by the frontend.

Run after scraping:
    python export_data.py
"""
import os
import re
import json
import sqlite3
from collections import Counter
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "data.json")

# ─── Stop words (automotive-extended) ────────────────────────────────────────
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "this", "that", "these", "those",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "and",
    "or", "but", "so", "yet", "for", "nor", "to", "of", "in", "on",
    "at", "by", "with", "from", "about", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "not", "only", "own", "same", "than", "too", "very",
    "just", "now", "get", "got", "go", "going", "went", "come", "came",
    "one", "two", "three", "first", "last", "new", "old",
    "dont", "didnt", "wasnt", "werent", "isnt", "arent", "hasnt",
    "havent", "hadnt", "wouldnt", "couldnt", "shouldnt", "cant",
    "cannot", "wont", "im", "its", "thats", "weve", "theyve", "youre",
    "ive", "s", "t", "m", "re", "ve", "ll", "d", "2026", "2025", "2024",
    # automotive stop words
    "car", "vehicle", "model", "drive", "drove", "test", "review", "reviews",
    "overall", "really", "quite", "much", "also", "well", "like", "even",
    "year", "month", "day", "time", "use", "used", "using", "still",
    "however", "although", "though", "because", "since", "while",
    "great", "good", "bad", "best", "better", "worse", "worst",
    "nice", "love", "hate", "feel", "think", "say", "said", "see",
    "tata", "jaguar", "rover", "land", "defender", "range", "discovery",
}

# ─── Automotive Issue Keywords ────────────────────────────────────────────────
ISSUE_KEYWORDS = {
    # EV & Range
    "battery": "Battery & Range",
    "range": "Battery & Range",
    "charging": "Charging Infrastructure",
    "charger": "Charging Infrastructure",
    "charge": "Charging Infrastructure",
    # Quality & Reliability
    "reliability": "Reliability",
    "reliable": "Reliability",
    "breakdown": "Reliability",
    "fault": "Reliability",
    "defect": "Reliability",
    "recall": "Safety Recall",
    "safety": "Safety Recall",
    # Infotainment
    "infotainment": "Infotainment",
    "screen": "Infotainment",
    "touchscreen": "Infotainment",
    "software": "Infotainment",
    "update": "Infotainment",
    "glitch": "Infotainment",
    # After-Sales
    "service": "After-Sales Service",
    "dealer": "After-Sales Service",
    "dealership": "After-Sales Service",
    "warranty": "Warranty",
    "wait": "After-Sales Service",
    "parts": "After-Sales Service",
    # Ride & Handling
    "suspension": "Ride & Handling",
    "steering": "Ride & Handling",
    "vibration": "NVH Issues",
    "noise": "NVH Issues",
    "rattle": "NVH Issues",
    "nois": "NVH Issues",
    # Pricing
    "price": "Pricing",
    "expensive": "Pricing",
    "cost": "Pricing",
    "value": "Pricing",
    "overpriced": "Pricing",
    # Build
    "build": "Build Quality",
    "panel": "Build Quality",
    "interior": "Build Quality",
    "plastic": "Build Quality",
    # Comfort
    "comfort": "Comfort",
    "seat": "Comfort",
    "legroom": "Comfort",
    "space": "Comfort",
    "boot": "Comfort",
    # Off-road
    "off-road": "Off-road Capability",
    "offroad": "Off-road Capability",
    "terrain": "Off-road Capability",
    "mud": "Off-road Capability",
    "wading": "Off-road Capability",
}

# ─── Automotive Praise Keywords ───────────────────────────────────────────────
PRAISE_KEYWORDS = {
    # Performance
    "performance": "Performance",
    "powerful": "Performance",
    "torque": "Performance",
    "acceleration": "Performance",
    "fast": "Performance",
    "quick": "Performance",
    # EV
    "electric": "EV Experience",
    "ev": "EV Experience",
    "instant": "EV Experience",
    "zero emission": "EV Experience",
    "efficient": "EV Experience",
    # Comfort / luxury
    "comfortable": "Comfort & Luxury",
    "luxurious": "Comfort & Luxury",
    "premium": "Comfort & Luxury",
    "smooth": "Comfort & Luxury",
    "quiet": "Comfort & Luxury",
    # Design
    "design": "Design & Styling",
    "stunning": "Design & Styling",
    "beautiful": "Design & Styling",
    "gorgeous": "Design & Styling",
    "looks": "Design & Styling",
    "style": "Design & Styling",
    # Interior
    "interior": "Interior Quality",
    "finish": "Interior Quality",
    "material": "Interior Quality",
    "craftsmanship": "Interior Quality",
    # Off-road
    "capable": "Off-road Capability",
    "terrain": "Off-road Capability",
    "off-road": "Off-road Capability",
    "wade": "Off-road Capability",
    # Safety
    "safety": "Safety Features",
    "adas": "Safety Features",
    "assist": "Safety Features",
    "lane": "Safety Features",
    # Practicality
    "practical": "Practicality",
    "family": "Practicality",
    "spacious": "Practicality",
    "versatile": "Practicality",
    "cargo": "Practicality",
    # Value
    "value": "Value for Money",
    "affordable": "Value for Money",
    "worth": "Value for Money",
}

# ─── Model name aliases (normalization) ───────────────────────────────────────
MODEL_ALIASES = {
    "d110": "Defender 110",
    "d90": "Defender 90",
    "d130": "Defender 130",
    "rrs": "Range Rover Sport",
    "rrv": "Range Rover Velar",
    "rre": "Range Rover Evoque",
    "ipace": "I-PACE",
    "fpace": "F-PACE",
    "epace": "E-PACE",
    "nexonev": "Nexon EV",
    "punchev": "Punch EV",
    "tigorev": "Tigor EV",
    "tiagrev": "Tiago EV",
}


# ─── Deduplication helpers ────────────────────────────────────────────────────
def get_text_tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def has_near_duplicate_text(first: str, second: str) -> bool:
    a, b = get_text_tokens(first), get_text_tokens(second)
    if not a and not b:
        return True
    shared = a & b
    union = a | b
    return len(union) > 0 and len(shared) / len(union) >= 0.85


def is_more_complete(candidate: dict, existing: dict) -> bool:
    def score(item):
        return (
            (4 if item.get("isUpcoming") else 0)
            + (2 if item.get("event", "General") not in ("General", "General Review") else 0)
            + (1 if item.get("sentiment") != "Neutral" else 0)
        )
    return score(candidate) > score(existing)


def deduplicate(items: list) -> list:
    unique = []
    for item in items:
        dup_idx = next(
            (
                i for i, existing in enumerate(unique)
                if existing["platform"].lower() == item["platform"].lower()
                and existing["author"].lower() == item["author"].lower()
                and existing["date"] == item["date"]
                and has_near_duplicate_text(existing["text"], item["text"])
            ),
            -1,
        )
        if dup_idx == -1:
            unique.append(item)
        elif is_more_complete(item, unique[dup_idx]):
            unique[dup_idx] = item
    return unique


# ─── Analytics helpers ────────────────────────────────────────────────────────
def tokenize(text: str) -> list:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    cleaned = []
    for t in tokens:
        if t in MODEL_ALIASES:
            cleaned.append(MODEL_ALIASES[t])
            continue
        base = t.rstrip("s") if len(t) > 3 else t
        if base not in STOP_WORDS and len(base) > 2:
            cleaned.append(base)
    return cleaned


def get_trending_terms(items: list, top_n: int = 15) -> list:
    term_sentiments: dict = {}
    for item in items:
        for token in tokenize(item["text"]):
            if token not in term_sentiments:
                term_sentiments[token] = {"Positive": 0, "Neutral": 0, "Negative": 0}
            term_sentiments[token][item["sentiment"]] += 1

    counts = {term: sum(v.values()) for term, v in term_sentiments.items()}
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [
        {
            "term": term,
            "count": counts[term],
            "positive": term_sentiments[term]["Positive"],
            "neutral": term_sentiments[term]["Neutral"],
            "negative": term_sentiments[term]["Negative"],
        }
        for term, _ in top
    ]


def get_theme_mentions(items: list, keywords: dict, sentiments=None, top_n: int = 8) -> list:
    theme_counts: Counter = Counter()
    theme_examples: dict = {}
    for item in items:
        if sentiments and item["sentiment"] not in sentiments:
            continue
        text_lower = item["text"].lower()
        for kw, label in keywords.items():
            if kw in text_lower:
                theme_counts[label] += 1
                if label not in theme_examples:
                    theme_examples[label] = item["text"][:180]
    return [
        {"theme": theme, "count": count, "example": theme_examples.get(theme, "")}
        for theme, count in theme_counts.most_common(top_n)
    ]


def get_top_events(items: list, top_n: int = 8) -> list:
    """Most discussed vehicle models, with sentiment breakdown."""
    generic = {"General", "General Review"}
    event_counts: dict = {}
    event_sentiments: dict = {}
    for item in items:
        event = item["event"]
        if event in generic:
            continue
        if event not in event_counts:
            event_counts[event] = 0
            event_sentiments[event] = {"Positive": 0, "Neutral": 0, "Negative": 0}
        event_counts[event] += 1
        event_sentiments[event][item["sentiment"]] += 1

    top = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [
        {
            "event": event,
            "count": event_counts[event],
            "positive": event_sentiments[event]["Positive"],
            "neutral": event_sentiments[event]["Neutral"],
            "negative": event_sentiments[event]["Negative"],
        }
        for event, _ in top
    ]


def get_top_authors(items: list, top_n: int = 8) -> list:
    counts = Counter(i["author"] for i in items)
    return [{"author": a, "count": c} for a, c in counts.most_common(top_n)]


def get_sentiment_by_date(items: list) -> dict:
    dates: dict = {}
    for item in items:
        d = item["date"]
        if d not in dates:
            dates[d] = {"Positive": 0, "Neutral": 0, "Negative": 0}
        dates[d][item["sentiment"]] += 1
    return dict(sorted(dates.items(), key=lambda x: x[0], reverse=True)[:14])


def get_brand_group_sentiment(items: list) -> dict:
    """Sentiment breakdown by brand_group (stored in 'city' field)."""
    groups: dict = {}
    for item in items:
        g = item["city"]  # brand_group is stored in city field
        if g not in groups:
            groups[g] = {"Positive": 0, "Neutral": 0, "Negative": 0, "total": 0}
        groups[g][item["sentiment"]] += 1
        groups[g]["total"] += 1
    return groups


def get_top_posts(items: list, sentiment: str, top_n: int = 5) -> list:
    filtered = [i for i in items if i["sentiment"] == sentiment]
    filtered.sort(key=lambda x: len(x["text"]), reverse=True)
    return [
        {
            "id": i["id"],
            "author": i["author"],
            "event": i["event"],
            "city": i["city"],
            "text": i["text"][:250],
            "date": i["date"],
        }
        for i in filtered[:top_n]
    ]


def build_executive_summary(items: list, sentiment_pct: dict, issues: list, praises: list,
                             top_models: list, brand: str) -> str:
    total = len(items)
    brand_label = "JLR (Jaguar Land Rover)" if brand == "jlr" else "Tata Motors"
    top_issue_themes = [i["theme"] for i in issues[:3]]
    top_praise_themes = [p["theme"] for p in praises[:3]]

    summary = (
        f"Across {total} {brand_label} reviews, sentiment is "
        f"{sentiment_pct['Positive']:.0f}% positive, {sentiment_pct['Neutral']:.0f}% neutral, and "
        f"{sentiment_pct['Negative']:.0f}% negative. "
    )
    if top_issue_themes:
        summary += f"Key concerns: {', '.join(top_issue_themes)}. "
    if top_praise_themes:
        summary += f"Most praised aspects: {', '.join(top_praise_themes)}. "
    if top_models:
        summary += f"Most reviewed models: {', '.join(e['event'] for e in top_models[:3])}."
    return summary


def build_analytics(items: list, sentiment_pct: dict, brand: str) -> dict:
    issues = get_theme_mentions(items, ISSUE_KEYWORDS, sentiments=["Negative", "Neutral"], top_n=8)
    praises = get_theme_mentions(items, PRAISE_KEYWORDS, sentiments=["Positive", "Neutral"], top_n=8)
    top_models = get_top_events(items, top_n=8)

    return {
        "trendingTerms": get_trending_terms(items, top_n=15),
        "keyIssues": issues,
        "topPraises": praises,
        "topEvents": top_models,
        "topAuthors": get_top_authors(items, top_n=8),
        "sentimentByDate": get_sentiment_by_date(items),
        "citySentiment": get_brand_group_sentiment(items),
        "topNegativePosts": get_top_posts(items, "Negative", top_n=5),
        "topPositivePosts": get_top_posts(items, "Positive", top_n=5),
        "executiveSummary": build_executive_summary(items, sentiment_pct, issues, praises, top_models, brand),
    }


# ─── Main export function ─────────────────────────────────────────────────────
def export_to_json():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback_items ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()

    all_items = []
    for row in rows:
        item_dict = {
            "id": row["id"],
            "platform": row["platform"],
            "author": row["author"],
            "date": row["date"],
            "event": row["event"],
            "text": row["text"],
            "sentiment": row["sentiment"],
            "city": row["city"],
            "isUpcoming": bool(row["isUpcoming"]),
        }

        row_keys = row.keys()
        item_dict["parent_id"] = row["parent_id"] if "parent_id" in row_keys else None
        item_dict["priority_score"] = int(row["priority_score"]) if "priority_score" in row_keys and row["priority_score"] is not None else 1
        item_dict["category_tag"] = row["category_tag"] if "category_tag" in row_keys and row["category_tag"] else "General"
        item_dict["action_insight"] = row["action_insight"] if "action_insight" in row_keys and row["action_insight"] else "No recommendation."
        item_dict["brand"] = row["brand"] if "brand" in row_keys and row["brand"] else "jlr"

        all_items.append(item_dict)

    # Deduplicate
    before = len(all_items)
    all_items = deduplicate(all_items)
    after = len(all_items)
    if before != after:
        print(f"Deduplicated: {before} -> {after} items (removed {before - after} duplicates)")

    # Split by brand
    jlr_items = [i for i in all_items if i.get("brand") == "jlr"]
    tata_items = [i for i in all_items if i.get("brand") == "tata"]

    def compute_sentiment_pct(items):
        total = len(items)
        if total == 0:
            return {"Positive": 0, "Neutral": 0, "Negative": 0}
        pos = sum(1 for i in items if i["sentiment"] == "Positive")
        neu = sum(1 for i in items if i["sentiment"] == "Neutral")
        neg = sum(1 for i in items if i["sentiment"] == "Negative")
        return {
            "Positive": round((pos / total) * 100, 2),
            "Neutral": round((neu / total) * 100, 2),
            "Negative": round((neg / total) * 100, 2),
        }

    total = len(all_items)
    jlr_pct = compute_sentiment_pct(jlr_items)
    tata_pct = compute_sentiment_pct(tata_items)
    overall_pct = compute_sentiment_pct(all_items)

    # Platform and brand_group counts
    platform_counts: dict = {}
    brand_group_counts: dict = {}
    brand_counts = {"jlr": len(jlr_items), "tata": len(tata_items)}

    for i in all_items:
        platform_counts[i["platform"]] = platform_counts.get(i["platform"], 0) + 1
        brand_group_counts[i["city"]] = brand_group_counts.get(i["city"], 0) + 1

    output = {
        "exportedAt": datetime.utcnow().isoformat() + "Z",
        "totalFeedbackCount": total,
        "sentimentPercentages": overall_pct,
        "platformCounts": platform_counts,
        "cityCounts": brand_group_counts,        # brand_group stored here (city field)
        "brandCounts": brand_counts,
        "analytics": build_analytics(all_items, overall_pct, "all"),
        "jlrAnalytics": build_analytics(jlr_items, jlr_pct, "jlr") if jlr_items else None,
        "tataAnalytics": build_analytics(tata_items, tata_pct, "tata") if tata_items else None,
        "items": all_items,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nExported {total} items to {OUTPUT_PATH}")
    print(f"JLR: {len(jlr_items)} items | Tata: {len(tata_items)} items")
    print(f"Platforms: {platform_counts}")
    print(f"JLR Sentiment: {jlr_pct}")
    print(f"Tata Sentiment: {tata_pct}")


if __name__ == "__main__":
    export_to_json()
