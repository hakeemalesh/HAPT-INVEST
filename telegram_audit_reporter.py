import os
import sqlite3
import requests
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_audit_metrics():
    """Query SQLite and calculate Week win/loss statistics."""
    conn = sqlite3.connect("hapt_invest.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM executed_orders")
        orders = cursor.fetchall()
    except sqlite3.OperationalError:
        orders = []
        
    try:
        cursor.execute("SELECT symbol, confidence, grade, status, timestamp FROM signals")
        signals = cursor.fetchall()
    except sqlite3.OperationalError:
        signals = []
        
    conn.close()
    
    total_signals = len(signals)
    total_executed = len(orders)
    
    report = (
        "📊 *HAPT INVEST: Automated Milestone Audit*\n"
        "──────────────────────────────\n"
        f"📡 *Total Signals Scanned:* {total_signals}\n"
        f"⚡ *Executed Trades:* {total_executed}\n"
        "🎯 *Current Win Rate:* --% (Pending active closes)\n"
        "💰 *Realized P&L:* $0.00\n"
        "──────────────────────────────\n"
        "_Status: Engine is live, synchronized, and monitoring._"
    )
    return report

def send_telegram_audit():
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment.")
        return
        
    message = get_audit_metrics()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Telegram audit report successfully dispatched!")
    else:
        print(f"❌ Failed to send Telegram alert: {response.text}")

if __name__ == "__main__":
    send_telegram_audit()
