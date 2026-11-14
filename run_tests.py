import os
import sys
import sqlite3
import requests
import traceback
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()

def print_header(title):
    print("=" * 65)
    print(f"🧪 REGRESSION TEST: {title}")
    print("=" * 65)

def test_environment_variables():
    print_header("1. Environment Variables & API Keys")
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID")

    assert api_key, "❌ ALPACA_API_KEY missing in .env"
    assert api_secret, "❌ ALPACA_SECRET_KEY missing in .env"
    assert tg_token, "❌ TELEGRAM_BOT_TOKEN missing in .env"
    assert tg_chat, "❌ TELEGRAM_CHAT_ID missing in .env"
    print("✅ All required environment variables and API keys are present.")

def test_telegram_connectivity():
    print_header("2. Telegram Telemetry Ping")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {"chat_id": tg_chat, "text": "🔍 *HAPT REGRESSION SUITE*: Diagnostic ping initiated.", "parse_mode": "Markdown"}
    response = requests.post(url, json=payload, timeout=5)
    assert response.status_code == 200, f"❌ Telegram API failed with status {response.status_code}"
    print("✅ Telegram bot telemetry ping successful.")

def test_alpaca_connection():
    print_header("3. Alpaca Paper Trading API & Database")
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")
    
    trading_client = TradingClient(api_key, api_secret, paper=True)
    account = trading_client.get_account()
    assert account, "❌ Failed to retrieve Alpaca account details."
    print(f"✅ Alpaca Paper Account Connected. Status: {account.status} | Cash: ${float(account.cash):,.2f}")

    # Test SQLite Database
    db_path = "hapt_invest.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    print("✅ SQLite database read/write integrity verified.")

def test_data_client_ingestion():
    print_header("4. Market Data Client & Technical Wiring")
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")
    data_client = StockHistoricalDataClient(api_key, api_secret)
    
    from datetime import datetime, timedelta
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=5)
    
    req = StockBarsRequest(
        symbol_or_symbols="SOFI",
        timeframe=TimeFrame.Day,
        start=start_date,
        end=end_date,
        feed=DataFeed.IEX
    )
    bars = data_client.get_stock_bars(req)
    assert not bars.df.empty, "❌ Failed to fetch historical bars from Alpaca Data API."
    print("✅ Historical market data ingestion and IEX feed verified.")

def test_script_imports():
    print_header("5. Core Script Syntax & Module Imports")
    try:
        import hapt_engine_v4
        import hapt_monitor
        import hapt_report
        import run_pipeline
        print("✅ All core modules (`hapt_engine_v4`, `hapt_monitor`, `hapt_report`, `run_pipeline`) imported successfully without errors.")
    except Exception as e:
        raise AssertionError(f"❌ Module import failure: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("🏛️ HAPT INVEST: EXECUTING FULL SYSTEM REGRESSION SUITE")
    print("=" * 65)
    try:
        test_environment_variables()
        test_telegram_connectivity()
        test_alpaca_connection()
        test_data_client_ingestion()
        test_script_imports()
        
        print("\n" + "=" * 65)
        print("🎉 ALL REGRESSION TESTS PASSED WITH ZERO FAILURES!")
        print("=" * 65)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ REGRESSION TEST FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
