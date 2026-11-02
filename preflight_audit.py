import os
import sys
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo

print("=" * 50)
print("?? HAPT INVEST PRE-FLIGHT SYSTEM AUDIT")
print("=" * 50)

# 1. Check Time Gatekeeper for Today (Nov 2, 2026)
try:
    now_et = datetime.now(ZoneInfo("America/New_York"))
    print(f"? Current ET Time: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    is_weekday = now_et.weekday() < 5
    print(f"   - Is Weekday? {is_weekday} (Weekday index: {now_et.weekday()})")
    print(f"   - Active Scan Window (8:30 AM - 4:00 PM ET): {now_et.time() >= datetime.strptime('08:30', '%H:%M').time() and now_et.time() <= datetime.strptime('16:00', '%H:%M').time()}")
except Exception as e:
    print(f"?? Time Zone Check Warning: {e}")

# 2. Check Database Schema
db_path = 'hapt_invest.db'
if os.path.exists(db_path):
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(signals);")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    if 'signal_type' in columns:
        print("? Database Schema: 'signals' table has 'signal_type' column verified.")
    else:
        print("? Database Schema Error: 'signal_type' column missing from 'signals' table!")
else:
    print("?? hapt_invest.db not found yet (will be initialized on first run).")

# 3. Check Alpaca API Connection
try:
    import alpaca_trade_api as tradeapi
    from dotenv import load_dotenv
    load_dotenv()
    
    key_id = os.getenv('APO_API_KEY') or os.getenv('APCA_API_KEY_ID') or os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('APO_SECRET_KEY') or os.getenv('APCA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')
    
    if key_id and secret_key:
        api = tradeapi.REST(key_id, secret_key, base_url, api_version='v2')
        account = api.get_account()
        print(f"? Alpaca API Connected Successfully!")
        print(f"   - Account Status: {account.status}")
        print(f"   - Buying Power: ${float(account.buying_power):,.2f}")
    else:
        print("?? Alpaca API Keys not fully detected in environment variables. Check .env file.")
except Exception as e:
    print(f"?? Alpaca API Connection Note: {e}")

# 4. Check Telegram Notifier
try:
    from telegram_notifier import send_telegram_alert
    print("? Telegram Notifier module loaded successfully.")
except Exception as e:
    print(f"?? Telegram Notifier check note: {e}")

print("=" * 50)
print("?? PRE-FLIGHT AUDIT COMPLETE.")
print("=" * 50)
