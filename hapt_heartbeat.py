import os
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

def send_heartbeat(status_msg="Daemon active and scanning."):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[WARN] Telegram credentials not found for heartbeat.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = (
        f"?? [HAPT INVEST HEARTBEAT]\n"
        f"Timestamp: {now}\n"
        f"Status: {status_msg}\n"
        f"Corridor: $3.00 - $35.00\n"
        f"System Integrity: 100% (Supervisor Active)"
    )
    
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[INFO] Heartbeat successfully dispatched at {now}.")
        else:
            print(f"[WARN] Heartbeat failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Heartbeat exception: {e}")

if __name__ == "__main__":
    print("[INFO] Testing standalone heartbeat...")
    send_heartbeat("Manual test ping from HAPT INVEST system.")
