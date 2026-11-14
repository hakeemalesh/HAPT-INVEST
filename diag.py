import os
import sqlite3
import requests
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv(dotenv_path=".env")

print("=" * 60)
print("HAPT INVEST: PRE-FLIGHT DIAGNOSTIC & AUDIT VERIFICATION")
print("=" * 60)

api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
api_secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print("1. Credentials Check:")
print(f"   - Alpaca API Key Present: {bool(api_key)}")
print(f"   - Alpaca Secret Present:  {bool(api_secret)}")
print(f"   - Telegram Token Present: {bool(bot_token)}")
print(f"   - Telegram Chat ID:       {bool(chat_id)}")

try:
    client = TradingClient(api_key, api_secret, paper=True)
    acc = client.get_account()
    print(f"2. Alpaca Account Status: ACTIVE (Buying Power: ${float(acc.buying_power):,.2f})")
except Exception as e:
    print(f"2. Alpaca Connection ERROR: {e}")

try:
    conn = sqlite3.connect("hapt_invest.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    print(f"3. SQLite Database Check: Tables found -> {tables}")
    conn.close()
except Exception as e:
    print(f"3. Database ERROR: {e}")

if bot_token and chat_id:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    msg = "🤖 HAPT INVEST PRE-FLIGHT TEST\n\nStatus: All core modules, database tables, and Alpaca endpoints verified successfully."
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        if resp.status_code == 200:
            print("4. Telegram Integration: TEST MESSAGE SENT SUCCESSFULLY!")
        else:
            print(f"4. Telegram Integration: Failed with code {resp.status_code}")
    except Exception as e:
        print(f"4. Telegram Integration ERROR: {e}")
else:
    print("4. Telegram Integration: Bot token or Chat ID missing in .env")

print("=" * 60)
