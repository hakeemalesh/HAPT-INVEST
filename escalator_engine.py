# -*- coding: utf-8 -*-
import os
import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")
        return False

def format_currency(ticker: str, price: float) -> str:
    if ticker.endswith(".L"):
        return f"£{price / 100:.2f}"
    else:
        return f"${price:.2f}"

def calculate_escalator_levels(entry_price: float, peak_price: float, trail_pct: float = 0.03) -> dict:
    gain_pct = ((peak_price - entry_price) / entry_price) * 100
    trailing_stop = peak_price * (1 - trail_pct)
    
    if gain_pct >= 15.0:
        tier = "Tier 3 (Lock +12% Minimum Gain)"
        guaranteed_floor = entry_price * 1.12
    elif gain_pct >= 10.0:
        tier = "Tier 2 (Lock +7% Minimum Gain)"
        guaranteed_floor = entry_price * 1.07
    elif gain_pct >= 5.0:
        tier = "Tier 1 (Break-Even + 2% Buffer)"
        guaranteed_floor = entry_price * 1.02
    else:
        tier = "Base Entry (Standard Initial Stop)"
        guaranteed_floor = entry_price * (1 - trail_pct)

    active_stop = max(trailing_stop, guaranteed_floor)

    return {
        "entry_price": entry_price,
        "peak_price": peak_price,
        "gain_pct": gain_pct,
        "tier": tier,
        "active_stop": active_stop
    }

def run_escalator_pipeline(portfolio: list):
    print("🪜 Running Multi-Exchange Trailing Escalator Risk Engine...\n")
    
    for pos in portfolio:
        ticker = pos['ticker']
        entry_price = pos['entry_price']
        
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.fast_info['lastPrice']
            peak_price = max(pos.get('peak_price', entry_price), current_price)
            
            esc = calculate_escalator_levels(entry_price, peak_price)
            triggered = current_price <= esc['active_stop']
            status_symbol = "⚠️ EXIT SIGNAL" if triggered else "🟢 ACTIVE HOLD"
            
            fmt_curr = format_currency(ticker, current_price)
            fmt_entry = format_currency(ticker, entry_price)
            fmt_peak = format_currency(ticker, peak_price)
            fmt_stop = format_currency(ticker, esc['active_stop'])
            
            print(f"[{ticker}] Current: {fmt_curr} | Entry: {fmt_entry} | Peak: {fmt_peak} | Active Stop: {fmt_stop} | {status_symbol}")
            
            alert_msg = (
                f"🪜 *HAPT - INVEST | Escalator Strategy Signal*\n\n"
                f"• *Ticker:* `{ticker}`\n"
                f"• *Entry Price:* `{fmt_entry}`\n"
                f"• *Current Price:* `{fmt_curr}` ({esc['gain_pct']:+.2f}%)\n"
                f"• *Peak High:* `{fmt_peak}`\n"
                f"• *Active Exit Stop:* `{fmt_stop}`\n"
                f"• *Escalator Tier:* `{esc['tier']}`\n\n"
                f"🎯 *Strategy Action:* `{status_symbol}`"
            )
            send_telegram_alert(alert_msg)
        except Exception as e:
            print(f"⚠️ Escalator error for {ticker}: {e}")

if __name__ == "__main__":
    mock_portfolio = [
        {"ticker": "NVDA", "entry_price": 180.00, "peak_price": 235.00},
        {"ticker": "SHEL.L", "entry_price": 2400.00, "peak_price": 2650.00}
    ]
    run_escalator_pipeline(mock_portfolio)