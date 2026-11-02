import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print("--- TELEGRAM INTEGRATION TEST ---")
if not bot_token or not chat_id:
    print("?? Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env file!")
else:
    message = "?? [HAPT INVEST] Forward Test Alert Verification:\nTelegram dispatch pipeline is 100% operational!"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("? Telegram test message dispatched successfully! Check your phone.")
        else:
            print(f"? Telegram dispatch failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"? Connection error: {e}")
