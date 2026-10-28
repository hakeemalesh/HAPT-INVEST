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

def calculate_dcf_valuation(ticker: str, g_rate: float = 0.08, discount_rate: float = 0.10, terminal_g: float = 0.025) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        cashflow = stock.cashflow
        
        raw_price = stock.fast_info["lastPrice"]
        shares_outstanding = info.get("sharesOutstanding", None)
        
        if "Free Cash Flow" in cashflow.index:
            fcf = cashflow.loc["Free Cash Flow"].iloc[0]
        else:
            fcf = cashflow.loc["Operating Cash Flow"].iloc[0] + cashflow.loc["Capital Expenditure"].iloc[0]

        if not fcf or not shares_outstanding:
            return None

        projected_fcf = []
        for i in range(1, 6):
            fcf_i = fcf * ((1 + g_rate) ** i)
            pv_fcf = fcf_i / ((1 + discount_rate) ** i)
            projected_fcf.append(pv_fcf)

        terminal_value = (fcf * ((1 + g_rate) ** 5) * (1 + terminal_g)) / (discount_rate - terminal_g)
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** 5)

        total_pv = sum(projected_fcf) + pv_terminal_value
        fair_value_per_share = total_pv / shares_outstanding
        
        eval_price = raw_price / 100 if ticker.endswith(".L") else raw_price
        margin_of_safety = ((fair_value_per_share - eval_price) / fair_value_per_share) * 100

        return {
            "ticker": ticker,
            "fmt_price": format_currency(ticker, raw_price),
            "fmt_fair_value": format_currency(ticker, fair_value_per_share * 100 if ticker.endswith(".L") else fair_value_per_share),
            "margin_of_safety": margin_of_safety,
            "pe_ratio": info.get("trailingPE", 0.0),
            "peg_ratio": info.get("pegRatio", 0.0)
        }
    except Exception as e:
        print(f"⚠️ Could not compute DCF for {ticker}: {e}")
        return None

def run_valuation_pipeline(tickers: list):
    print("🧮 Running Multi-Exchange Intrinsic Valuation Models...\n")
    
    for ticker in tickers:
        dcf = calculate_dcf_valuation(ticker)
        if dcf:
            status = "🟢 UNDERVALUED" if dcf["margin_of_safety"] > 0 else "🔴 OVERVALUED"
            print(f"[{ticker}] Fair Value: {dcf['fmt_fair_value']} | Current: {dcf['fmt_price']} | Margin of Safety: {dcf['margin_of_safety']:+.2f}%")
            
            alert_msg = (
                f"📊 *HAPT - INVEST | Valuation Report*\n\n"
                f"• *Ticker:* `{dcf['ticker']}`\n"
                f"• *Current Price:* `{dcf['fmt_price']}`\n"
                f"• *DCF Intrinsic Value:* `{dcf['fmt_fair_value']}`\n"
                f"• *Margin of Safety:* `{dcf['margin_of_safety']:+.2f}%`\n"
                f"• *Trailing P/E:* `{dcf['pe_ratio']:.2f}` | *PEG:* `{dcf['peg_ratio']:.2f}`\n\n"
                f"🎯 *Valuation Status:* `{status}`"
            )
            send_telegram_alert(alert_msg)

if __name__ == "__main__":
    run_valuation_pipeline(["AAPL", "NVDA", "SHEL.L", "AZN.L"])