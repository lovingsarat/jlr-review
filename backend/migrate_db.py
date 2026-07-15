import sqlite3
import random

DB_PATH = "diaspora.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add columns if not exists
    for col, col_type in [("parent_id", "TEXT"), ("priority_score", "INTEGER"), ("category_tag", "TEXT"), ("action_insight", "TEXT")]:
        try:
            cursor.execute(f"ALTER TABLE feedback_items ADD COLUMN {col} {col_type}")
            print(f"Added column {col}")
        except sqlite3.OperationalError:
            pass # already exists
            
    # 2. Backfill existing data
    cursor.execute("SELECT id, text, sentiment, event FROM feedback_items")
    rows = cursor.fetchall()
    
    categories = ["Transport", "Facilities", "Pricing", "Stalls & Food", "Safety & Crowd", "Culture & Music", "Ticketing", "India Passport", "India Visa", "Visa Appointment", "OCI Card"]
    
    for row_id, text, sentiment, event in rows:
        # Determine category based on keywords
        text_l = text.lower()
        cat = "General"
        if any(w in text_l for w in ["passport"]):
            cat = "India Passport"
        elif any(w in text_l for w in ["oci"]):
            cat = "OCI Card"
        elif "visa" in text_l:
            if any(w in text_l for w in ["appointment", "slot", "booking", "schedule"]):
                cat = "Visa Appointment"
            else:
                cat = "India Visa"
        elif any(w in text_l for w in ["parking", "bus", "shuttle", "traffic", "road", "train"]):
            cat = "Transport"
        elif any(w in text_l for w in ["ticket", "price", "expensive", "cost", "resell", "scalp"]):
            cat = "Pricing" if "expensive" in text_l else "Ticketing"
        elif any(w in text_l for w in ["food", "chaat", "coffee", "cater", "langar", "eat", "stall"]):
            cat = "Stalls & Food"
        elif any(w in text_l for w in ["crowd", "litter", "safety", "trash", "bin", "washroom", "toilet"]):
            cat = "Safety & Crowd"
        elif any(w in text_l for w in ["music", "dhol", "dance", "bhangra", "garba", "classical"]):
            cat = "Culture & Music"
        else:
            cat = "General"
            
        # Determine priority score based on sentiment and keywords
        if sentiment == "Negative":
            p_score = random.choice([3, 4, 5])
            if any(w in text_l for w in ["safety", "rape", "murder", "stab", "terrorist", "litter"]):
                p_score = 5
            insight = f"Review safety measures and improve {cat.lower()} coordination."
        elif sentiment == "Positive":
            p_score = 1
            insight = f"Maintain high standards for {cat.lower()} experiences."
        else:
            p_score = random.choice([1, 2, 3])
            insight = f"Monitor feedback regarding {cat.lower()} details."
            
        cursor.execute("""
            UPDATE feedback_items
            SET priority_score = ?, category_tag = ?, action_insight = ?
            WHERE id = ?
        """, (p_score, cat, insight, row_id))
        
    conn.commit()
    conn.close()
    print("Database backfill successfully completed!")

if __name__ == "__main__":
    migrate()
