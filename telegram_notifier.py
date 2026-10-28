import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_alert(message: str):
    """Sends a real-time trade signal alert directly to your Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ALERT WARNING] Telegram credentials not configured in .env. Skipping push notification.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"?? **HAPT INVEST LIVE SIGNAL** ??\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[INFO] Telegram alert successfully dispatched!")
            return True
        else:
            print(f"[ERROR] Failed to send Telegram alert: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception sending Telegram alert: {e}")
        return False
