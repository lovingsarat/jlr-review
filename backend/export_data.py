"""
Export the current diaspora.db SQLite database to frontend/public/data.json
so that the GitHub Pages static deployment always shows the latest scraped data.

Run this after scraping new tweets:
    python export_data.py
"""
import os
import json
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "diaspora.db")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "data.json")

def export_to_json():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM feedback_items ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            "id": row["id"],
            "platform": row["platform"],
            "author": row["author"],
            "date": row["date"],
            "event": row["event"],
            "text": row["text"],
            "sentiment": row["sentiment"],
            "city": row["city"],
            "isUpcoming": bool(row["isUpcoming"])
        })

    # Compute stats
    total = len(items)
    positives = sum(1 for i in items if i["sentiment"] == "Positive")
    neutrals  = sum(1 for i in items if i["sentiment"] == "Neutral")
    negatives = sum(1 for i in items if i["sentiment"] == "Negative")

    platform_counts = {}
    city_counts = {}
    for i in items:
        platform_counts[i["platform"]] = platform_counts.get(i["platform"], 0) + 1
        city_counts[i["city"]] = city_counts.get(i["city"], 0) + 1

    output = {
        "exportedAt": datetime.utcnow().isoformat() + "Z",
        "totalFeedbackCount": total,
        "sentimentPercentages": {
            "Positive": round((positives / total) * 100, 2) if total else 0,
            "Neutral":  round((neutrals  / total) * 100, 2) if total else 0,
            "Negative": round((negatives / total) * 100, 2) if total else 0,
        },
        "platformCounts": platform_counts,
        "cityCounts": city_counts,
        "items": items
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Exported {total} items to {OUTPUT_PATH}")
    print(f"Sentiment: {positives} positive, {neutrals} neutral, {negatives} negative")
    print(f"Platforms: {platform_counts}")

if __name__ == "__main__":
    export_to_json()
