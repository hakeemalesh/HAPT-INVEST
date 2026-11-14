
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")

class HaptMasterCommandCenter:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.db_path = "hapt_invest.db"
        self._init_audit_table()

    def _init_audit_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT,
                current_price REAL,
                suggested_stop REAL,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()

    def run_audit(self):
        print("="*65)
        print("🏛️ HAPT INVEST: INSTITUTIONAL PORTFOLIO COMMAND CENTER")
        print("="*65)
        
        account = self.trading_client.get_account()
        print(f"💰 Portfolio Cash: ${float(account.cash):,.2f}")
        print(f"📈 Portfolio Equity: ${float(account.equity):,.2f}")
        print(f"⚡ Buying Power: ${float(account.buying_power):,.2f}")
        print("-" * 65)

        holdings = ["SOFI", "F", "NIO"]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for ticker in holdings:
            try:
                req = StockLatestTradeRequest(symbol_or_symbols=ticker)
                resp = self.data_client.get_stock_latest_trade(req)
                if ticker in resp:
                    price = resp[ticker].price
                    stop_price = price * 0.975
                    print(f"🟢 [MONITORED] Ticker: {ticker:<6} | Price: ${price:<8.2f} | Dynamic Stop: ${stop_price:<8.2f}")
                    
                    cursor.execute(
                        "INSERT INTO portfolio_audit (ticker, current_price, suggested_stop, status) VALUES (?, ?, ?, ?)",
                        (ticker, price, stop_price, "ACTIVE_MONITORING")
                    )
            except Exception as e:
                print(f"⚠️ Error auditing {ticker}: {e}")

        conn.commit()
        conn.close()
        print("="*65)
        print("✅ Portfolio telemetry successfully logged to hapt_invest.db!")
        print("="*65)

if __name__ == "__main__":
    center = HaptMasterCommandCenter()
    center.run_audit()

