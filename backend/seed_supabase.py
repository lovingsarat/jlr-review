import asyncio
import json
from pathlib import Path

from backend.supabase_store import store


def seed() -> None:
    if not store.configured:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY before seeding.")
    data_path = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data.json"
    items = json.loads(data_path.read_text(encoding="utf-8"))["items"]
    for item in items:
        store.upsert_feedback(item)
    print(f"Seeded {len(items)} records.")


if __name__ == "__main__":
    seed()
