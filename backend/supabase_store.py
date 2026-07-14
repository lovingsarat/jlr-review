import hashlib
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
load_dotenv()


class SupabaseStore:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    @property
    def configured(self) -> bool:
        return bool(self.url and self.service_key)

    @property
    def headers(self) -> Dict[str, str]:
        if not self.configured:
            raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
        return {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = httpx.request(method, f"{self.url}{path}", headers=self.headers, timeout=30.0, **kwargs)
        response.raise_for_status()
        return response

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(item["id"]),
            "platform": item["platform"],
            "author": item["author"],
            "date": str(item["date"]),
            "event": item["event"],
            "text": item["text"],
            "sentiment": item["sentiment"],
            "city": item["city"],
            "isUpcoming": bool(item.get("is_upcoming", item.get("isUpcoming", False))),
        }

    def _source_hash(self, item: Dict[str, Any]) -> str:
        normalized_text = re.sub(r"\s+", " ", item["text"].strip().lower())
        value = "|".join((item["platform"].strip().lower(), item["author"].strip().lower(), str(item["date"]), normalized_text))
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def list_feedback(self, query: Optional[str] = None, platform: Optional[str] = None, sentiment: Optional[str] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
        response = self._request(
            "GET",
            "/rest/v1/feedback_items",
            params={"select": "id,platform,author,date,event,text,sentiment,city,is_upcoming", "order": "date.desc", "limit": "1000"},
        )
        items = [self._normalize_item(item) for item in response.json()]
        if platform:
            items = [item for item in items if item["platform"].lower() == platform.lower()]
        if sentiment:
            items = [item for item in items if item["sentiment"].lower() == sentiment.lower()]
        if city:
            items = [item for item in items if item["city"].lower() == city.lower()]
        if query:
            text = query.lower()
            items = [item for item in items if text in item["text"].lower() or text in item["event"].lower() or text in item["author"].lower()]
        return items

    def get_stats(self) -> Dict[str, Any]:
        items = self.list_feedback()
        total = len(items)
        sentiment_counts = Counter(item["sentiment"] for item in items)
        return {
            "totalFeedbackCount": total,
            "sentimentPercentages": {
                "Positive": (sentiment_counts["Positive"] / total * 100) if total else 0,
                "Neutral": (sentiment_counts["Neutral"] / total * 100) if total else 0,
                "Negative": (sentiment_counts["Negative"] / total * 100) if total else 0,
            },
            "platformCounts": dict(Counter(item["platform"] for item in items)),
            "cityCounts": dict(Counter(item["city"] for item in items)),
        }

    def get_gemini_embedding(self, text: str) -> List[float]:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key in {"MY_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"}:
            return []
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}",
            json={"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["embedding"]["values"]

    def upsert_feedback(self, item: Dict[str, Any]) -> bool:
        embedding = self.get_gemini_embedding(item["text"])
        payload = {
            "id": str(item["id"]),
            "source_hash": self._source_hash(item),
            "platform": item["platform"],
            "author": item["author"],
            "date": str(item["date"]),
            "event": item["event"],
            "text": item["text"],
            "sentiment": item["sentiment"],
            "city": item["city"],
            "is_upcoming": bool(item.get("isUpcoming", item.get("is_upcoming", False))),
            "embedding": embedding if embedding else None,
        }
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=representation"}
        response = httpx.post(
            f"{self.url}/rest/v1/feedback_items?on_conflict=source_hash",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return bool(response.json())

    def query_context(self, query: str, limit: int = 8) -> str:
        embedding = self.get_gemini_embedding(query)
        items: List[Dict[str, Any]] = []
        if embedding:
            try:
                response = self._request("POST", "/rest/v1/rpc/match_feedback", json={"query_embedding": embedding, "match_count": limit})
                items = [self._normalize_item(item) for item in response.json()]
            except httpx.HTTPError:
                items = []
        if not items:
            query_words = {word.lower() for word in re.findall(r"[a-zA-Z]{3,}", query)}
            ranked = []
            for item in self.list_feedback():
                haystack = f"{item['event']} {item['text']}".lower()
                score = sum(word in haystack for word in query_words)
                ranked.append((score, item))
            items = [item for _, item in sorted(ranked, key=lambda entry: entry[0], reverse=True)[:limit]]
        if not items:
            return "No matching feedback records found."
        lines = ["| Platform | Author | Date | Event | Sentiment | City | Feedback text |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for item in items:
            upcoming = " (Upcoming Planned Activity)" if item["isUpcoming"] else ""
            text = item["text"].replace("|", "\\|")
            lines.append(f"| {item['platform']} | {item['author']} | {item['date']} | {item['event']}{upcoming} | {item['sentiment']} | {item['city']} | {text} |")
        return "\n".join(lines)


store = SupabaseStore()
