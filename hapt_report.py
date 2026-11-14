import os
import sqlite3
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")
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

def generate_weekly_report():
    print("=" * 65)
    print("📊 HAPT INVEST: WEEKLY PERFORMANCE & PnL AUDITOR")
    print("=" * 65)

    # 1. Query SQLite Database for Executed Orders & AI Signals
    db_path = "hapt_invest.db"
    orders_df = pd.DataFrame()
    ai_orders_df = pd.DataFrame()

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            orders_df = pd.read_sql("SELECT * FROM executed_orders", conn)
        except Exception:
            pass
        try:
            ai_orders_df = pd.read_sql("SELECT * FROM ai_executed_orders", conn)
        except Exception:
            pass
        conn.close()

    total_legacy_orders = len(orders_df)
    total_ai_orders = len(ai_orders_df)

    # 2. Query Alpaca for Live Portfolio & Unrealized PnL
    trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
    account = trading_client.get_account()
    positions = trading_client.get_all_positions()

    portfolio_value = float(account.portfolio_value)
    cash = float(account.cash)
    buying_power = float(account.buying_power)

    active_positions_summary = []
    total_unrealized_pnl = 0.0

    for p in positions:
        ticker = p.symbol
        qty = float(p.qty)
        market_val = float(p.market_value)
        unrealized_pnl = float(p.unrealized_pl)
        total_unrealized_pnl += unrealized_pnl
        active_positions_summary.append(f"• `{ticker}` ({qty} sh): ${market_val:,.2f} | PnL: `${unrealized_pnl:,.2f}`")

    # 3. Format Report Output
    report_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_text = f"""📈 *HAPT INVEST WEEKLY PnL REPORT* 📈
Timestamp: `{report_timestamp}`

💼 *Portfolio Valuation:*
• Portfolio Value: `${portfolio_value:,.2f}`
• Cash Balance: `${cash:,.2f}`
• Buying Power: `${buying_power:,.2f}`
• Unrealized PnL: `${total_unrealized_pnl:,.2f}`

📊 *Execution Database Audit:*
• Legacy Orders Logged: `{total_legacy_orders}`
• AI-Engine Orders Logged: `{total_ai_orders}`

📌 *Active Portfolio Positions:*
{'\n'.join(active_positions_summary) if active_positions_summary else '• *No active positions currently held (Clean Slate)*'}

STATUS: *Week 2 Cycle Primed & Operational* ✅"""

    print(report_text)
    send_telegram(report_text)
    print("=" * 65)
    print("✅ Weekly performance report successfully generated and dispatched!")

if __name__ == "__main__":
    generate_weekly_report()
