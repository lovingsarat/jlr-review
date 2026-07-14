import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from database import get_db_connection, query_chroma_context

# Load environment
load_dotenv(dotenv_path="../.env")
load_dotenv()

app = FastAPI(title="Diaspora Hub API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Scraper State (in-memory) ---
scraper_state = {
    "is_running": False,
    "last_run": None,          # ISO timestamp of last successful run
    "last_added": 0,           # How many items were added in the last run
    "status_message": "Idle",
}

class ChatMessage(BaseModel):
    sender: str  # "USER" or "BOT"
    text: str
    timestamp: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]

# --- Background scraper task ---
async def run_scraper_background():
    scraper_state["is_running"] = True
    scraper_state["status_message"] = "Scraping X (Twitter) for new UK diaspora content..."
    try:
        from scraper import run_scraper
        # Count before
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM feedback_items")
        count_before = c.fetchone()[0]
        conn.close()

        await run_scraper()

        # Count after
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM feedback_items")
        count_after = c.fetchone()[0]
        conn.close()

        added = count_after - count_before
        scraper_state["last_added"] = added
        scraper_state["last_run"] = datetime.utcnow().isoformat() + "Z"
        scraper_state["status_message"] = f"Done. {added} new UK items added."
    except Exception as e:
        scraper_state["status_message"] = f"Error: {str(e)[:120]}"
    finally:
        scraper_state["is_running"] = False

@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger the Twitter/X scraper in the background. Tracks duplicate tweet IDs automatically."""
    if scraper_state["is_running"]:
        return {
            "status": "already_running",
            "message": "Scraper is already running. Check /api/scrape/status for progress."
        }
    background_tasks.add_task(run_scraper_background)
    return {
        "status": "started",
        "message": "UK diaspora scraper started. New tweets will be filtered for duplicates automatically."
    }

@app.get("/api/scrape/status")
def get_scrape_status():
    """Get the current status of the scraper and when it last ran."""
    return {
        "is_running": scraper_state["is_running"],
        "last_run": scraper_state["last_run"],
        "last_added": scraper_state["last_added"],
        "status_message": scraper_state["status_message"],
    }

@app.get("/api/feedback")
def get_feedback(
    query: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_str = "SELECT * FROM feedback_items WHERE 1=1"
    params = []
    
    if platform:
        query_str += " AND LOWER(platform) = LOWER(?)"
        params.append(platform)
    if sentiment:
        query_str += " AND LOWER(sentiment) = LOWER(?)"
        params.append(sentiment)
    if city:
        query_str += " AND LOWER(city) = LOWER(?)"
        params.append(city)
        
    cursor.execute(query_str, params)
    rows = cursor.fetchall()
    conn.close()
    
    items = [dict(row) for row in rows]
    
    # Map `isUpcoming` integer 0/1 back to boolean for React App consumption
    for item in items:
        item["isUpcoming"] = bool(item["isUpcoming"])
        
    # Python-side filtering for textual search queries
    if query:
        q = query.lower()
        items = [
            item for item in items
            if q in item["text"].lower()
            or q in item["event"].lower()
            or q in item["author"].lower()
        ]
        
    return items

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all items to compute stats dynamically
    cursor.execute("SELECT sentiment, platform, city FROM feedback_items")
    rows = cursor.fetchall()
    conn.close()
    
    total = len(rows)
    if total == 0:
        return {
            "totalFeedbackCount": 0,
            "sentimentPercentages": {"Positive": 0.0, "Neutral": 0.0, "Negative": 0.0},
            "platformCounts": {},
            "cityCounts": {}
        }
        
    positives = sum(1 for r in rows if r["sentiment"] == "Positive")
    neutrals = sum(1 for r in rows if r["sentiment"] == "Neutral")
    negatives = sum(1 for r in rows if r["sentiment"] == "Negative")
    
    sentiment_percentages = {
        "Positive": (positives / total) * 100.0,
        "Neutral": (neutrals / total) * 100.0,
        "Negative": (negatives / total) * 100.0
    }
    
    platform_counts = {}
    for r in rows:
        platform_counts[r["platform"]] = platform_counts.get(r["platform"], 0) + 1
        
    city_counts = {}
    for r in rows:
        city_counts[r["city"]] = city_counts.get(r["city"], 0) + 1
        
    return {
        "totalFeedbackCount": total,
        "sentimentPercentages": sentiment_percentages,
        "platformCounts": platform_counts,
        "cityCounts": city_counts
    }

@app.post("/api/chat")
async def chat_rag(request_body: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key in ["MY_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"]:
        return {
            "reply": "⚠️ **API Key Missing**: It looks like your `GEMINI_API_KEY` is not set on the server. Please define it in the `.env` file to perform live vector RAG analysis!"
        }

    # Query ChromaDB Vector database to extract the closest RAG context matches
    print(f"Retrieving vector search context for query: {request_body.message}...")
    rag_context = query_chroma_context(request_body.message, k=5)
    
    system_instruction_text = (
        "You are the \"Diaspora RAG Bot\", an expert sentiment analyzer and community reporter for the Indian Diaspora "
        "in the UK Midlands (including Birmingham, Leicester, Coventry, Wolverhampton, Nottingham, etc.).\n\n"
        "You have access to a dynamically updated vector database of social media posts and community comments.\n\n"
        "Here is the relevant subset of records retrieved from our vector database matching the user's current topic in Markdown format:\n"
        f"{rag_context}\n\n"
        "Instructions for your responses:\n"
        "1. Answer the user's questions based strictly on the provided context feedback records. Do not invent any posts, authors, or events that are not in the context dataset.\n"
        "2. If the user asks about sentiment, give an insightful analysis of Positive vs Neutral vs Negative feedback, highlighting specific complaints and achievements based on the retrieved items.\n"
        "3. Use bold text, bullet points, and clean headers. Speak with deep familiarity about Midlands UK geography.\n"
        "4. If a query is outside the scope of community events, state: \"I couldn't find specific social feedback on that in our consolidated database. However, based on our recorded trends...\" and summarize the nearest relevant trend."
    )

    api_contents = []
    
    for msg in request_body.history:
        role = "user" if msg.sender == "USER" else "model"
        api_contents.append({
            "role": role,
            "parts": [{"text": msg.text}]
        })
        
    api_contents.append({
        "role": "user",
        "parts": [{"text": request_body.message}]
    })

    payload = {
        "contents": api_contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction_text}]
        },
        "generationConfig": {
            "temperature": 0.3
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Gemini API returned error: {response.text}"
                )
                
            resp_data = response.json()
            
            try:
                bot_reply = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                bot_reply = "I received an empty response. Please try rephrasing your question."
                
            return {"reply": bot_reply}
            
    except Exception as e:
        return {
            "reply": f"❌ **Error**: Could not connect to Gemini API. {str(e)}\n\n*Note: Verify that the API key provided is valid.*"
        }
