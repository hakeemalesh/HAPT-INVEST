from audit_telemetry import send_heartbeat_alert
# -*- coding: utf-8 -*-
"""
HAPT INVEST - Unified Production Engine
- Market Hours Gatekeeper (LSE 08:00-16:30 BST / US 14:30-21:00 BST)
- Intraday RVOL/ATR Momentum Scanner with Strict VWAP & Positive Return Filters
- Risk Engine: Dynamic ATR Stop Loss, Take Profit 1 & 2, Position Sizing
- Interactive Security Gate Verification Circuit for Telegram
- Telemetry DB Logger & Segment 2 Macro Portfolio Scanner (/longterm)
"""

import os
import sys
import time
import sqlite3
import logging
from datetime import datetime, time as dtime
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from dotenv import load_dotenv
from trade_logger import log_trade
from alpaca_execution import execute_paper_order

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("hapt_invest.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

DB_PATH = "hapt_invest.db"
TELEGRAM_BOT_TOKEN = os.getenv("8740075368:AAFQ29GbkZvVhO01SePMnzYyDh-s-NZcM0Q", "")
TELEGRAM_CHAT_ID = os.getenv("8184495825", "")

MARKET_HW_LSE = (8, 0, 16, 30)
MARKET_HW_US = (14, 30, 21, 0)

MARKET_SCAN_USER = "HAPT INVEST OFFICIAL"

US_TICKERS = ["SOFI", "F", "AAL", "CLSK", "KGC", "NCLH", "RBLX", "PLTR", "LCID", "MARA", "BAC", "PBR", "RIG", "VALE", "ITUB"]
LSE_TICKERS = ["SHEL.L", "AZN.L", "HSBA.L", "BP.L", "GSK.L", "RIO.L", "ULVR.L", "REL.L"]

class DatabaseManager:
    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ticker TEXT,
                market TEXT,
                signal_type TEXT,
                grade TEXT,
                confidence INTEGER,
                price REAL,
                stop_loss REAL,
                tp1 REAL,
                tp2 REAL,
                rvol REAL,
                atr_expansion REAL,
                status TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executed_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER,
                timestamp TEXT,
                ticker TEXT,
                entry_price REAL,
                execution_price REAL,
                slippage_pct REAL,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def log_signal(sig: dict) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signals (timestamp, ticker, market, signal_type, grade, confidence, price, stop_loss, tp1, tp2, rvol, atr_expansion, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            sig['ticker'], sig['market'], sig['signal_type'], sig['grade'],
            sig['confidence'], sig['price'], sig['stop_loss'], sig['tp1'], sig['tp2'],
            sig['rvol'], sig['atr_expansion'], 'DISPATCHED'
        ))
        sig_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return sig_id

class MarketGatekeeper:
    @staticmethod
    def is_lse_open() -> bool:
        now_utc = datetime.utcnow()
        if now_utc.weekday() >= 5:
            return False
        current_time = now_utc.time()
        # LSE: 08:00 to 16:30 UTC
        return dtime(8, 0) <= current_time <= dtime(16, 30)

    @staticmethod
    def is_us_open() -> bool:
        now_utc = datetime.utcnow()
        if now_utc.weekday() >= 5:
            return False
        current_time = now_utc.time()
        # US (NYSE/NASDAQ): 13:30 to 21:00 UTC
        return dtime(13, 30) <= current_time <= dtime(21, 0)

class TechnicalEngine:
    @staticmethod
    def analyze_ticker(ticker: str, is_uk: bool = False) -> dict:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="10d", interval="5m")
            if hist.empty or len(hist) < 50:
                return None

            close_prices = hist['Close']
            volume = hist['Volume']
            high_prices = hist['High']
            low_prices = hist['Low']

            current_price = float(close_prices.iloc[-1])
            prev_close = float(close_prices.iloc[-2])
            pct_change = ((current_price - prev_close) / prev_close) * 100

            if pct_change <= 0.3:
                return None

            vwap = (hist['Volume'] * (hist['High'] + hist['Low'] + hist['Close']) / 3).sum() / hist['Volume'].sum()
            if current_price < vwap:
                return None

            avg_vol = volume.iloc[-20:].mean()
            current_vol = volume.iloc[-1]
            rvol = (current_vol / avg_vol) if avg_vol > 0 else 0.0

            if rvol < 1.4:
                return None

            tr = np.maximum(high_prices - low_prices, np.abs(low_prices - close_prices.shift(1)))
            atr = float(tr.rolling(14).mean().iloc[-1])
            avg_atr = float(tr.mean())
            atr_expansion = (atr / avg_atr) if avg_atr > 0 else 1.0

            if atr_expansion < 1.2:
                return None

            grade = "GRADE A+" if rvol >= 1.8 and atr_expansion >= 1.3 else ("GRADE A" if rvol >= 1.4 else "GRADE B"); # "GRADE A"
            confidence = 90 if grade == "GRADE A+" else 80

            stop_loss = round(current_price - (1.5 * atr), 2)
            tp1 = round(current_price + (2.0 * atr), 2)
            tp2 = round(current_price + (3.5 * atr), 2)

            return {
                "ticker": ticker,
                "market": "LSE" if is_uk else ("NASDAQ" if "AAPL" in ticker or "NVDA" in ticker else "NYSE"),
                "signal_type": "BUY",
                "grade": grade,
                "confidence": confidence,
                "price": round(current_price, 2),
                "pct_change": round(pct_change, 2),
                "stop_loss": stop_loss,
                "tp1": tp1,
                "tp2": tp2,
                "rvol": round(rvol, 2),
                "atr_expansion": round(atr_expansion, 2)
            }
        except Exception as e:
            logging.error(f"Error analyzing {ticker}: {e}")
            return None

def dispatch_telegram_alert(sig: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.info(f"[ALERT PREVIEW] {sig['ticker']} ({sig['market']}) | {sig['grade']} | Price: ${sig['price']:.2f} | SL: ${sig['stop_loss']:.2f} | TP1: ${sig['tp1']:.2f}")

    is_uk = sig['ticker'].endswith(".L")
    p_unit = "p" if is_uk else "$"
    price_val = sig['price'] / 100 if is_uk else sig['price']
    sl_val = sig['stop_loss'] / 100 if is_uk else sig['stop_loss']
    tp1_val = sig['tp1'] / 100 if is_uk else sig['tp1']
    tp2_val = sig['tp2'] / 100 if is_uk else sig['tp2']

    text = f"""🚨 *HAPT INVEST | Institutional Signal Alert* 🚨

*Symbol:* `{sig['ticker']}`
*Market:* {sig['market']}
*Signal:* *{sig['signal_type']} (LONG)*
*Grade:* `{sig['grade']}`
*Confidence:* `{sig['confidence']}%`

*Current Price:* `{p_unit}{price_val:.2f}` (+{sig['pct_change']:.2f}%)
*Stop Loss:* `{p_unit}{sl_val:.2f}`
*Take Profit 1:* `{p_unit}{tp1_val:.2f}`
*Take Profit 2:* `{p_unit}{tp2_val:.2f}`

*Volume Confluence (RVOL):* `{sig['rvol']}x` vs 20D Avg
*Range Expansion (ATR):* `{sig['atr_expansion']}x`
*Status:* Security Circuit Verification Ready
"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Failed to dispatch Telegram message: {e}")

def run_intraday_scan_cycle():
    logging.info("Initiating Intraday Market Scan Cycle...")
    lse_active = MarketGatekeeper.is_lse_open()
    us_active = MarketGatekeeper.is_us_open()

    tz = pytz.timezone("Europe/London")
    now = datetime.now(tz)
    if now.weekday() >= 5:
        logging.info("🔒 All Target Exchanges (LSE / US) currently closed. Gatekeeper standing by.")
        return

    active_tickers = []
    if lse_active:
        logging.info("[ALERT] LSE Market Open. Adding UK Tickers...")
        active_tickers.extend([(t, True) for t in LSE_TICKERS])
    if us_active:
        logging.info("[ALERT] US Market Open. Adding US Tickers...")
        active_tickers.extend([(t, False) for t in US_TICKERS])

    if not active_tickers:
        logging.info("🔒 Target market hours inactive. Gatekeeper standing by.")
        return

    for ticker, is_uk in active_tickers:
        sig = TechnicalEngine.analyze_ticker(ticker, is_uk)
        if sig:
            # 1. Store in SQLite state DB
            sig_id = DatabaseManager.log_signal(sig)
                
            # 2. Fire Telegram push notification
            dispatch_telegram_alert(sig)
                
            # 3. Mirror signal to trade_log.csv
            log_trade(
                ticker=sig['ticker'],
                market=sig['market'],
                action=sig['signal_type'],
                price=sig['price'],
                sl=sig['stop_loss'],
                tp=sig['tp1'],
                status="DISPATCHED"
            )
                
            # 4. Trigger Alpaca paper execution for US tickers
            if not is_uk:
                try:
                    order_id = execute_paper_order(symbol=sig['ticker'], qty=10, side="buy")
                    logging.info(f"Alpaca Order Dispatched | Order ID: {order_id}")
                except Exception as e:
                    logging.error(f"Alpaca Execution Guard Intercepted: {e}")

if __name__ == '__main__':
    import time
    DatabaseManager.init_db()
    logging.info("--------------------------------------------------")
    logging.info("     HAPT INVEST | UNIFIED PRODUCTION ENGINE     ")
    logging.info("--------------------------------------------------")
    logging.info("[START] Starting HAPT INVEST Autonomous Daemon Loop...")
    
    while True:
        try:
            run_intraday_scan_cycle()
        except Exception as e:
            logging.error(f"Scan Loop Exception: {e}")
        
        time.sleep(300)
