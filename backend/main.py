import os
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from database import FEEDBACK_ITEMS, get_markdown_summary

# Load environment variables from .env
# Search in root directory and backend directory
load_dotenv(dotenv_path="../.env")
load_dotenv()

app = FastAPI(title="Diaspora Hub API")

# Configure CORS so the React frontend (running on port 5173 or others) can access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    sender: str  # "USER" or "BOT"
    text: str
    timestamp: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]

@app.get("/api/feedback")
def get_feedback(
    query: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):
    filtered = FEEDBACK_ITEMS
    
    if platform:
        filtered = [item for item in filtered if item["platform"].lower() == platform.lower()]
    if sentiment:
        filtered = [item for item in filtered if item["sentiment"].lower() == sentiment.lower()]
    if city:
        filtered = [item for item in filtered if item["city"].lower() == city.lower()]
        
    if query:
        q = query.lower()
        filtered = [
            item for item in filtered
            if q in item["text"].lower()
            or q in item["event"].lower()
            or q in item["author"].lower()
        ]
        
    return filtered

@app.get("/api/stats")
def get_stats():
    total = len(FEEDBACK_ITEMS)
    if total == 0:
        return {
            "totalFeedbackCount": 0,
            "sentimentPercentages": {"Positive": 0.0, "Neutral": 0.0, "Negative": 0.0},
            "platformCounts": {},
            "cityCounts": {}
        }
        
    positives = sum(1 for item in FEEDBACK_ITEMS if item["sentiment"] == "Positive")
    neutrals = sum(1 for item in FEEDBACK_ITEMS if item["sentiment"] == "Neutral")
    negatives = sum(1 for item in FEEDBACK_ITEMS if item["sentiment"] == "Negative")
    
    sentiment_percentages = {
        "Positive": (positives / total) * 100.0,
        "Neutral": (neutrals / total) * 100.0,
        "Negative": (negatives / total) * 100.0
    }
    
    # Platform counts
    platform_counts = {}
    for item in FEEDBACK_ITEMS:
        platform = item["platform"]
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
    # City counts
    city_counts = {}
    for item in FEEDBACK_ITEMS:
        city = item["city"]
        city_counts[city] = city_counts.get(city, 0) + 1
        
    return {
        "totalFeedbackCount": total,
        "sentimentPercentages": sentiment_percentages,
        "platformCounts": platform_counts,
        "cityCounts": city_counts
    }

@app.post("/api/chat")
async def chat_rag(request_body: ChatRequest):
    # Retrieve API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "MY_GEMINI_API_KEY" or api_key == "YOUR_GEMINI_API_KEY":
        return {
            "reply": "⚠️ **API Key Missing**: It looks like your `GEMINI_API_KEY` is not set on the server. Please define it in the `.env` file to perform live RAG analysis!\n\n*(Meanwhile, here is a quick overview: Holi tickets are seen as too expensive, Diwali drone plans are exciting but park-and-ride is requested, and Coventry Garba has ticket scalping issues.)*"
        }

    # Prepare RAG context
    system_instruction_text = (
        "You are the \"Diaspora RAG Bot\", an expert sentiment analyzer and community reporter for the Indian Diaspora "
        "in the UK Midlands (including Birmingham, Leicester, Coventry, Wolverhampton, Nottingham, etc.).\n\n"
        "You have access to a consolidated database of social media feedback from Twitter (X), Facebook, and Quora "
        "regarding community event engagement in 2026, and upcoming planned events.\n\n"
        "Here is the entire consolidated dataset in Markdown format:\n"
        f"{get_markdown_summary()}\n\n"
        "Instructions for your responses:\n"
        "1. Answer the user's questions based strictly on the provided feedback dataset. Do not invent any posts, authors, or events that are not in the dataset.\n"
        "2. If the user asks about sentiment, give an insightful analysis of Positive vs Neutral vs Negative feedback, highlighting specific complaints (e.g. Holi/Garba pricing, Vaisakhi crowd management, Sports Day rain delay) and achievements (e.g. Vaisakhi Langar quality, Sports Day youth engagement).\n"
        "3. If asked about upcoming activities or planned events, detail the entries for Leicester Diwali Lights Switch-On 2026 (drone show, park and ride concerns) and Coventry Navratri Garba 2026 (scalping issues, new venue).\n"
        "4. Keep your answers well-structured using markdown formatting (bullet points, bold text, headers) and highly professional. Speak with deep familiarity about Midlands UK geography.\n"
        "5. If a query is outside the scope of community events, state: \"I couldn't find specific social feedback on that in our consolidated 2026 Midlands database. However, based on our recorded trends...\" and summarize the nearest relevant trend."
    )

    # Format the history and current message for the Gemini API
    api_contents = []
    
    # Iterate through history
    for msg in request_body.history:
        role = "user" if msg.sender == "USER" else "model"
        api_contents.append({
            "role": role,
            "parts": [{"text": msg.text}]
        })
        
    # Append the new message
    api_contents.append({
        "role": "user",
        "parts": [{"text": request_body.message}]
    })

    # Prepare call payload
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
            "reply": f"❌ **Error**: Could not connect to Gemini API. {str(e)}\n\n*Note: If the error persists, verify that the API key provided in the .env file is valid.*"
        }
