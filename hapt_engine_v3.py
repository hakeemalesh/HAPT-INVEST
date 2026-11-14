import os
import sqlite3
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class HaptHybridExecutionEngine:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.db_path = "hapt_invest.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executed_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT,
                side TEXT,
                qty REAL,
                price REAL,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()

    def send_telegram_alert(self, message):
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"❌ Telegram dispatch error: {e}")

    def compute_rsi(self, series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def get_clean_universe(self):
        return [
            "SOFI", "PLTR", "F", "NIO", "AMD", "INTC", "BAC", "SNAP", "VALE", 
            "CCL", "PBR", "AAL", "LCID", "PLUG", "UBER", "LYFT", "RIVN", "NCLH",
            "KGC", "BTBT", "X", "CLF", "HAL", "MU", "SCHW", "PYPL", "HOOD", "DKNG",
            "ON", "WBD", "C", "T", "VZ", "PTON", "COIN", "MARA", "RIOT"
        ]

    def scan_and_execute(self):
        universe = self.get_clean_universe()
        print(f"=" * 65)
        print(f"🏛️ HAPT INVEST: HYBRID Z-SCORE + RSI REVERSION SCANNER")
        print(f"📊 Scanning {len(universe)} institutional assets at {datetime.now()}...")
        print(f"=" * 65)

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=60)

        for ticker in universe:
            try:
                req = StockBarsRequest(
                    symbol_or_symbols=ticker,
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    end=end_date,
                    feed=DataFeed.IEX
                )
                bars = self.data_client.get_stock_bars(req)
                df = bars.df
                
                if df.empty or ticker not in df.index.get_level_values(0):
                    continue

                data = df.loc[ticker].copy()
                data['sma_20'] = data['close'].rolling(20).mean()
                data['std_20'] = data['close'].rolling(20).std()
                data['z_score'] = (data['close'] - data['sma_20']) / data['std_20']
                data['rsi'] = self.compute_rsi(data['close'], 14)
                
                high_low = data['high'] - data['low']
                high_close = np.abs(data['high'] - data['close'].shift())
                low_close = np.abs(data['low'] - data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                data['atr'] = np.max(ranges, axis=1).rolling(14).mean()

                current_close = data['close'].iloc[-1]
                current_z = data['z_score'].iloc[-1]
                current_rsi = data['rsi'].iloc[-1]
                current_atr = data['atr'].iloc[-1]
                current_sma = data['sma_20'].iloc[-1]

                if pd.isna(current_z) or pd.isna(current_rsi) or pd.isna(current_atr):
                    continue

                print(f"📊 Evaluated {ticker}: Price=${current_close:.2f} | Z-Score={current_z:.2f} | RSI={current_rsi:.1f}")

                # Hybrid Entry Filter: Sweet Spot ($3-$40) AND Z-Score <= -2.0 AND RSI <= 30
                if 3.0 <= current_close <= 40.0 and current_z <= -2.0 and current_rsi <= 30.0:
                    positions = self.trading_client.get_all_positions()
                    if any(p.symbol == ticker for p in positions):
                        print(f"📌 Position already active for {ticker}. Skipping execution.")
                        continue

                    qty = round(500.0 / current_close, 2)
                    stop_loss_price = round(current_close - (2.5 * current_atr), 2)
                    target_price = round(current_sma, 2)

                    print(f"🚀 Hybrid Oversold Setup on {ticker}! Submitting Bracket Order...")

                    bracket_data = MarketOrderRequest(
                        symbol=ticker,
                        qty=qty,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.GTC,
                        order_class=OrderClass.BRACKET,
                        take_profit=TakeProfitRequest(limit_price=target_price),
                        stop_loss=StopLossRequest(stop_price=stop_loss_price)
                    )
                    self.trading_client.submit_order(order_data=bracket_data)

                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO executed_orders (ticker, side, qty, price, status) VALUES (?, ?, ?, ?, ?)",
                                   (ticker, "BUY (HYBRID BRACKET)", qty, current_close, "SUBMITTED"))
                    conn.commit()
                    conn.close()

                    alert_msg = f"""🚨 *HAPT HYBRID SETUP* 🚨
Symbol: `{ticker}`
Strategy: `Z-Score <= -2.0 + RSI <= 30`
Entry: `${current_close:.2f}`
Take Profit (SMA Mean): `${target_price}`
Stop Loss (2.5x ATR): `${stop_loss_price}`
Size: `{qty} shares`

BROKER EXECUTION: *BRACKET SECURED* ✅"""

                    self.send_telegram_alert(alert_msg)
                    break

            except Exception as e:
                print(f"⚠️ Error scanning {ticker}: {e}")

if __name__ == "__main__":
    engine = HaptHybridExecutionEngine()
    engine.scan_and_execute()
