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

class HaptAIEngine:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.db_path = "hapt_invest.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_executed_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT,
                side TEXT,
                signal_type TEXT,
                qty REAL,
                price REAL,
                ai_score REAL,
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

    def get_broad_universe(self):
        return [
            "SOFI", "PLTR", "F", "NIO", "AMD", "INTC", "BAC", "SNAP", "VALE", 
            "CCL", "PBR", "AAL", "LCID", "PLUG", "UBER", "LYFT", "RIVN", "NCLH",
            "KGC", "BTBT", "X", "CLF", "HAL", "MU", "SCHW", "PYPL", "HOOD", "DKNG",
            "ON", "WBD", "C", "T", "VZ", "PTON", "COIN", "MARA", "RIOT",
            "ET", "AIG", "KEY", "ZIM", "NOK", "PFE", "ABEV", "TAL"
        ]

    def ai_decision_analysis(self, ticker, z_score, rsi, volume_surge):
        """Calibrated AI Multi-Factor Scoring Model."""
        score = 0.0
        reasons = []

        # Z-Score Weight (Primary Statistical Driver)
        if z_score <= -2.0:
            score += 0.5
            reasons.append(f"Strong Oversold Z-Score ({z_score:.2f})")
        elif z_score >= 2.0:
            score += 0.5
            reasons.append(f"Strong Overbought Z-Score ({z_score:.2f})")

        # RSI Weight (Momentum Confirmation)
        if rsi <= 30.0:
            score += 0.3
            reasons.append(f"Oversold RSI Confirmation ({rsi:.1f})")
        elif rsi >= 70.0:
            score += 0.3
            reasons.append(f"Overbought RSI Confirmation ({rsi:.1f})")

        # Volume Surge Weight (Activity Filter - relaxed to >= 1.0x baseline)
        if volume_surge >= 1.0:
            score += 0.2
            reasons.append(f"Healthy Volume Support ({volume_surge:.1f}x ADV)")

        return score, reasons

    def scan_and_execute(self):
        universe = self.get_broad_universe()
        print(f"=" * 65)
        print(f"🏛️ HAPT INVEST: CALIBRATED AI REVERSION SCANNER")
        print(f"📊 Scanning {len(universe)} broad-market assets at {datetime.now()}...")
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
                data['volume_sma'] = data['volume'].rolling(20).mean()
                data['volume_surge'] = data['volume'] / data['volume_sma']
                
                high_low = data['high'] - data['low']
                high_close = np.abs(data['high'] - data['close'].shift())
                low_close = np.abs(data['low'] - data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                data['atr'] = np.max(ranges, axis=1).rolling(14).mean()

                current_close = data['close'].iloc[-1]
                current_z = data['z_score'].iloc[-1]
                current_rsi = data['rsi'].iloc[-1]
                current_vol_surge = data['volume_surge'].iloc[-1]
                current_atr = data['atr'].iloc[-1]
                current_sma = data['sma_20'].iloc[-1]

                if pd.isna(current_z) or pd.isna(current_rsi) or pd.isna(current_vol_surge):
                    continue

                print(f"🔍 {ticker}: Price=${current_close:.2f} | Z={current_z:.2f} | RSI={current_rsi:.1f} | Vol Surge={current_vol_surge:.1f}x")

                # Sweet Spot Filter ($3-$40) & Z-Score Trigger
                if not (3.0 <= current_close <= 40.0 and (current_z <= -2.0 or current_z >= 2.0)):
                    continue

                ai_score, reasons = self.ai_decision_analysis(ticker, current_z, current_rsi, current_vol_surge)
                
                # Optimized AI Confidence Threshold (0.5 required)
                if ai_score >= 0.5:
                    positions = self.trading_client.get_all_positions()
                    if any(p.symbol == ticker for p in positions):
                        print(f"📌 Position already active for {ticker}. Skipping.")
                        continue

                    side = OrderSide.BUY if current_z <= -2.0 else OrderSide.SELL
                    qty = round(500.0 / current_close, 2)
                    stop_loss_price = round(current_close - (2.5 * current_atr) if side == OrderSide.BUY else current_close + (2.5 * current_atr), 2)
                    target_price = round(current_sma, 2)

                    print(f"🤖 AI TRADE SIGNAL APPROVED on {ticker} ({side.value})! Score: {ai_score}")
                    for r in reasons:
                        print(f"   - {r}")

                    bracket_data = MarketOrderRequest(
                        symbol=ticker,
                        qty=qty,
                        side=side,
                        time_in_force=TimeInForce.GTC,
                        order_class=OrderClass.BRACKET,
                        take_profit=TakeProfitRequest(limit_price=target_price),
                        stop_loss=StopLossRequest(stop_price=stop_loss_price)
                    )
                    self.trading_client.submit_order(order_data=bracket_data)

                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO ai_executed_orders (ticker, side, signal_type, qty, price, ai_score, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (ticker, side.value, "AI_BIDIRECTIONAL_REVERSION", qty, current_close, ai_score, "SUBMITTED"))
                    conn.commit()
                    conn.close()

                    alert_msg = f"""🤖 *HAPT AI TRADING DESK* 🤖
Symbol: `{ticker}`
Signal: `{side.value} (AI Score: {ai_score})`
Entry: `${current_close:.2f}`
Take Profit: `${target_price}`
Stop Loss: `${stop_loss_price}`
Reasons: `{' | '.join(reasons)}`

BROKER EXECUTION: *BRACKET SECURED* ✅"""

                    self.send_telegram_alert(alert_msg)
                    break

            except Exception as e:
                print(f"⚠️ Error scanning {ticker}: {e}")

if __name__ == "__main__":
    engine = HaptAIEngine()
    engine.scan_and_execute()
