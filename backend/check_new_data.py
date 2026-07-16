import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "diaspora.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get platform distribution
cursor.execute("SELECT platform, COUNT(*) FROM feedback_items GROUP BY platform")
platforms = cursor.fetchall()

print("=== Current Database Ingestion Stats ===")
print("Reviews Count by Platform:")
for p, count in platforms:
    print(f"  - {p:15s} : {count} reviews")

# Show sample of newly ingested portal data
print("\n=== Sample of Newly Ingested Data ===")
cursor.execute("""
    SELECT platform, author, event, sentiment, text 
    FROM feedback_items 
    WHERE platform IN ('Trustpilot', 'Team-BHP', 'Zigwheels', 'YouTube') 
    LIMIT 6
""")
for row in cursor.fetchall():
    print(f"\n[{row[0].upper()}] by {row[1]} for {row[2]} ({row[3]})")
    print(f"  Text: \"{row[4][:120]}...\"")

conn.close()
