import os
import sys
from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("?? TELEGRAM & EXECUTION SDK CHECK")
print("=" * 50)

# 1. Test Telegram
try:
    from telegram_notifier import send_telegram_alert
    success = send_telegram_alert("?? [HAPT INVEST] Pre-flight Telegram Ping: All systems armed for Monday launch!")
    if success:
        print("? Telegram Alert: Sent successfully! Check your phone/chat.")
    else:
        print("?? Telegram Alert: Function ran but returned False. Check bot token/chat ID.")
except Exception as e:
    print(f"? Telegram Alert Error: {e}")

# 2. Check Alpaca SDK (alpaca-py vs alpaca_trade_api)
try:
    import alpaca
    print("? Alpaca SDK ('alpaca' / alpaca-py) is installed and available.")
except ImportError:
    try:
        import alpaca_trade_api
        print("? Alpaca SDK ('alpaca_trade_api') is installed and available.")
    except ImportError:
        print("? Warning: Neither 'alpaca' nor 'alpaca_trade_api' found in python environment.")

print("=" * 50)
