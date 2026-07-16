"""
verify_slack.py — Simple script to test the Slack Webhook integration.
Loads SLACK_WEBHOOK_URL from .env and sends a test Priority 5 alert.
"""
import os
import httpx
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv()

def test_slack():
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    print(f"Webhook URL loaded: {bool(webhook_url)}")
    
    if not webhook_url or webhook_url == "your_slack_webhook_url":
        print("❌ ERROR: SLACK_WEBHOOK_URL is missing or not configured in your .env file!")
        return

    print("Sending test critical alert to Slack...")
    
    test_item = {
        "brand": "tata",
        "priority_score": 5,
        "event": "Nexon EV Max",
        "platform": "Twitter",
        "author": "@NexonOwnerIndia",
        "category_tag": "After-Sales",
        "action_insight": "Establish a 24-hour SLA hot-swap policy for battery packs at top-tier metro service centers.",
        "text": "My Nexon EV Max (2024 model) has been sitting at the service center for 18 days due to a battery charging management fault. No ETA on replacement parts, and customer service has given me zero updates. Incredibly frustrating after-sales experience!"
    }

    brand_name = "JLR (Jaguar Land Rover)" if test_item.get("brand") == "jlr" else "Tata Motors"
    
    payload = {
        "text": f"🚨 *CRITICAL FEEDBACK DETECTED — {brand_name.upper()}* (TEST ALERT)",
        "attachments": [
            {
                "color": "#ef4444",
                "fields": [
                    {"title": "Vehicle Model", "value": test_item.get("event"), "short": True},
                    {"title": "Platform", "value": test_item.get("platform"), "short": True},
                    {"title": "Author", "value": test_item.get("author"), "short": True},
                    {"title": "Theme", "value": test_item.get("category_tag"), "short": True},
                    {"title": "Priority Score", "value": "★" * test_item.get("priority_score"), "short": True},
                    {"title": "Actionable Insight", "value": test_item.get("action_insight"), "short": False}
                ],
                "text": f"*{test_item.get('author')}:* {test_item.get('text')}"
            }
        ]
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=8.0)
        if resp.status_code == 200:
            print("SUCCESS: Test alert sent successfully! Check your Slack channel.")
        else:
            print(f"FAILED: Slack returned status code {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"ERROR: Failed to make the request: {e}")

if __name__ == "__main__":
    test_slack()
