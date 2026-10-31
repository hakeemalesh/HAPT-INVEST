import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("       HAPT INVEST FULL SYSTEM AUDIT REPORT       ")
print("==================================================")

tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
tg_chat = os.getenv("TELEGRAM_CHAT_ID")
apca_key = os.getenv("APCA_API_KEY_ID")

print(f"[1] Telegram Token Configured: {bool(tg_token)} (Length: {len(tg_token) if tg_token else 0})")
print(f"[2] Telegram Chat ID Configured: {bool(tg_chat)}")
print(f"[3] Alpaca API Key Configured: {bool(apca_key)}")

db_files = [f for f in os.listdir(".") if f.endswith(".db")]
print(f"[4] SQLite Databases Found: {db_files}")

for db in db_files:
    print(f"\nChecking schema for {db}...")
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"    - Tables: {tables}")
    
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"      * Table '{t}' columns: {columns}")
        
        # Check if signals table lacks signal_type and fix it
        if t == "signals" and "signal_type" not in columns:
            print("        [FIXING] Adding missing 'signal_type' column to signals table...")
            cursor.execute("ALTER TABLE signals ADD COLUMN signal_type TEXT;")
            conn.commit()
            print("        [FIXED] Column added successfully!")
            
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        count = cursor.fetchone()[0]
        print(f"      * Row count: {count}")
    conn.close()

if os.path.exists("trade_log.csv"):
    df = pd.read_csv("trade_log.csv")
    print(f"\n[5] trade_log.csv found with {len(df)} rows.")
else:
    print("\n[5] trade_log.csv is currently clean/missing.")

print("==================================================")
print("        DIAGNOSTIC VERIFICATION COMPLETE          ")
print("==================================================")
