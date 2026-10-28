# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

FALLBACK_SP500 = ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "LLY"]
FALLBACK_FTSE100 = ["SHEL.L", "AZN.L", "HSBA.L", "BP.L", "GSK.L", "RIO.L", "ULVR.L", "REL.L"]

def get_universe() -> list:
    return list(set(FALLBACK_SP500 + FALLBACK_FTSE100))

def analyze_long_term_asset(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if len(hist) < 200:
            return None
            
        info = stock.info
        current_price = float(hist['Close'].iloc[-1])
        
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        trend_aligned = current_price > sma_50 > sma_200
        
        obv = (np.sign(hist['Close'].diff()) * hist['Volume']).fillna(0).cumsum()
        obv_sma_20 = obv.rolling(window=20).mean().iloc[-1]
        accumulation_active = obv.iloc[-1] > obv_sma_20
        
        pe_ratio = info.get("forwardPE", info.get("trailingPE", 0))
        profit_margins = info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0
        debt_to_equity = info.get("debtToEquity", 0)
        
        score = 50
        if trend_aligned: score += 20
        if accumulation_active: score += 15
        if 0 < pe_ratio < 30: score += 10
        if profit_margins > 15: score += 5
        
        rating = "STRONG BUY (3-6M)" if score >= 80 else "ACCUMULATE" if score >= 65 else "WATCHLIST"
        
        return {
            "ticker": ticker,
            "price": current_price,
            "pe_ratio": pe_ratio,
            "profit_margins": profit_margins,
            "trend_aligned": trend_aligned,
            "accumulation": accumulation_active,
            "score": score,
            "rating": rating
        }
    except Exception:
        return None

def run_long_term_scan():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running Segment 2 Long-Term Macro Scan (3-6+ Month Horizon)...")
    universe = get_universe()
    candidates = []
    
    for ticker in universe:
        res = analyze_long_term_asset(ticker)
        if res and res['score'] >= 65:
            candidates.append(res)
            
    candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    print("\n==========================================================================")
    print("        HAPT INVEST | LONG-TERM PORTFOLIO RECOMMENDATIONS (3-6M)          ")
    print("==========================================================================")
    for c in candidates:
        p = f"$ {c['price']:.2f}"
        print(f"• {c['ticker']:<8} | Score: {c['score']}/100 | Rating: {c['rating']:<18} | Price: {p:<9} | P/E: {c['pe_ratio']:.1f}")
    print("==========================================================================\n")

if __name__ == "__main__":
    run_long_term_scan()


# --- TELEGRAM DISPATCH FOR LONG-TERM ENGINE ---
import requests
from dotenv import load_dotenv

def send_longterm_telegram_report(summary_text):
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
    
    if not token or not chat_id:
        print("[WARN] Telegram credentials missing for long-term dispatch.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message = f"??? *HAPT INVEST | LONG-TERM PORTFOLIO REPORT*

{summary_text}"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("[SUCCESS] Long-term portfolio recommendations dispatched to Telegram!")
        else:
            print(f"[WARN] Telegram dispatch failed: {res.text}")
    except Exception as e:
        print(f"[ERROR] Exception during long-term Telegram dispatch: {e}")
