import os
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.supabase_store import store

app = FastAPI(title="Midlands Sentiment API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatMessage(BaseModel):
    sender: str
    text: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]


def require_store() -> None:
    if not store.configured:
        raise HTTPException(status_code=503, detail="Data service is not configured.")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "dataStoreConfigured": store.configured}


@app.get("/api/feedback")
def get_feedback(
    query: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
) -> list:
    require_store()
    return store.list_feedback(query=query, platform=platform, sentiment=sentiment, city=city)


@app.get("/api/stats")
def get_stats() -> dict:
    require_store()
    return store.get_stats()


@app.get("/api/scrape/status")
def get_scrape_status() -> dict:
    return {
        "is_running": False,
        "last_run": None,
        "last_added": 0,
        "status_message": "Scheduled scraper service manages live updates.",
    }


@app.post("/api/scrape")
def trigger_scrape() -> dict:
    return {
        "status": "scheduled_service",
        "message": "The deployed scraper runs on its configured schedule.",
    }


@app.post("/api/chat")
async def chat_rag(request_body: ChatRequest) -> dict:
    require_store()
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key in {"MY_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"}:
        raise HTTPException(status_code=503, detail="Gemini is not configured.")

    context = store.query_context(request_body.message)
    system_instruction = (
        "You are the Midlands Sentiment RAG assistant for Indian diaspora community events in the UK Midlands. "
        "Answer strictly from the retrieved feedback records. Do not invent posts, authors, or events. "
        "Use concise markdown with headings and bullets when useful. If the records do not answer the question, say so clearly.\n\n"
        "Retrieved feedback records:\n"
        f"{context}"
    )
    contents = [
        {
            "role": "user" if message.sender == "USER" else "model",
            "parts": [{"text": message.text}],
        }
        for message in request_body.history
    ]
    contents.append({"role": "user", "parts": [{"text": request_body.message}]})
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            json={
                "contents": contents,
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "generationConfig": {"temperature": 0.3},
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Gemini request failed.")
    data = response.json()
    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
    if not reply:
        raise HTTPException(status_code=502, detail="Gemini returned no response.")
    return {"reply": reply}
