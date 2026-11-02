import sqlite3
import os

db_path = "hapt_invest.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table count and recent signals
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"?? Database Tables Found: {tables}")
    
    if "signals" in tables:
        cursor.execute("SELECT timestamp, ticker, signal_type, price, status FROM signals ORDER BY id DESC LIMIT 5;")
        rows = cursor.fetchall()
        print("\n?? Recent Logged Signals in hapt_invest.db:")
        print("-" * 65)
        for row in rows:
            print(f"Time: {row[0]} | Ticker: {row[1]} | Type: {row[2]} | Price: ${row[3]} | Status: {row[4]}")
        print("-" * 65)
    else:
        print("?? 'signals' table not found yet.")
    conn.close()
else:
    print("?? hapt_invest.db not found yet. Run main.py once to initialize it.")
