import os
import requests
import yfinance as yf
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_test():
    """Tests the Telegram Bot Connection."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🤖 *HAPT - Invest System Check*\n\nPhase 1 environment online! Telegram alert pipeline verified.",
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200

def check_market_data(ticker="AAPL"):
    """Tests Live Stock Data Retrieval."""
    stock = yf.Ticker(ticker)
    price = stock.fast_info['lastPrice']
    return price

if __name__ == "__main__":
    print("Initializing HAPT - Invest Phase 1 Test...\n")
    
    # 1. Test Market Data Connection
    try:
        aapl_price = check_market_data("AAPL")
        print(f"✅ Market Data Connection Active! Current AAPL Price: ${aapl_price:.2f}")
    except Exception as e:
        print(f"❌ Market Data Failed: {e}")

    # 2. Test Telegram Connection
    try:
        if send_telegram_test():
            print("✅ Telegram Connection Active! Check your phone for the test message.\n")
        else:
            print("❌ Telegram Delivery Failed. Double-check your Token and Chat ID in the .env file.\n")
    except Exception as e:
        print(f"❌ Telegram Test Failed: {e}")