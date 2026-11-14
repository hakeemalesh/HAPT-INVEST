import os
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Telegram dispatch error: {e}")

if __name__ == "__main__":
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram(f"🚀 *HAPT PIPELINE STARTED*\nTimestamp: `{start_time}`")
    
    print("=" * 65)
    print(f"🏛️ HAPT INVEST: Hourly Pipeline Initiated at {start_time}")
    print("=" * 65)
    
    # 1. Run AI Reversion Scanner & Execution Engine
    print("\n[1/2] Executing hapt_engine_v4.py...")
    subprocess.run([".\\.venv\\Scripts\\python.exe", "hapt_engine_v4.py"], check=False)
    
    # 2. Run Position Profit Exit Monitor
    print("\n[2/2] Executing hapt_monitor.py...")
    subprocess.run([".\\.venv\\Scripts\\python.exe", "hapt_monitor.py"], check=False)
    
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 65)
    print(f"✅ HAPT Pipeline execution complete at {end_time}.")
    print("=" * 65)
    
    send_telegram(f"✅ *HAPT PIPELINE FINISHED*\nTimestamp: `{end_time}`")
