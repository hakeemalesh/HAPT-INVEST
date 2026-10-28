import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_heartbeat_alert(active_tickers_count, market_status="ACTIVE"):
    message = (
        f"<b>HAPT INVEST | SYSTEM HEARTBEAT</b>\n"
        f"Status: Engine Online & Listening\n"
        f"Active Market: {market_status}\n"
        f"Monitored Tickers: {active_tickers_count}\n"
        f"48H Secondary Trial Pipeline Operational"
    )
    dispatch_telegram(message)

def send_daytrade_alert(ticker, market, signal_type, price, stop_loss, tp1, time_frame="5m"):
    message = (
        f"<b>HAPT INVEST | DAY TRADE ALERT</b>\n"
        f"Ticker: {ticker} ({market})\n"
        f"Signal: {signal_type.upper()}\n"
        f"Timeframe: {time_frame} (Live Feed)\n"
        f"Entry Price: ${price:.2f}\n"
        f"Stop Loss: ${stop_loss:.2f}\n"
        f"Take Profit (TP1): ${tp1:.2f}\n"
        f"Execution Mode: Instant Intraday Sizing"
    )
    dispatch_telegram(message)

def dispatch_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            logging.info("Telegram notification dispatched successfully.")
        else:
            logging.warning(f"Telegram dispatch failed: {res.status_code} - {res.text}")
    except Exception as e:
        logging.error(f"Telegram Exception: {e}")
