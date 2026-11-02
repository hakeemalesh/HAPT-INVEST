import os
import re
import ast

core_file = "hapt_invest_core.py"
if not os.path.exists(core_file):
    print(f"? Error: {core_file} not found in current directory.")
else:
    with open(core_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Inject or update the confidence grading function
    confidence_code = """
def calculate_breakout_confidence(rvol: float, atr_expansion: float) -> str:
    \"\"\"
    Filters out noise by grading intraday momentum strength.
    - A+: Exceptional volume surge & explosive ATR expansion
    - A: Strong institutional momentum
    - B: Marginal breakout (watch closely)
    \"\"\"
    if rvol >= 3.5 and atr_expansion >= 2.0:
        return "A+ (Elite Momentum)"
    elif rvol >= 2.0 and atr_expansion >= 1.5:
        return "A (High Conviction)"
    else:
        return "B (Speculative / Noise)"
"""
    if "def calculate_breakout_confidence" not in content:
        content += "\n\n" + confidence_code
    
    # 2. Inject or update the interactive Telegram alert function with buttons
    telegram_code = """
def send_interactive_telegram_alert(ticker: str, price: float, grade: str, signal_type: str):
    import requests
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return False
        
    message = (
        f"?? <b>[HAPT INVEST] BREAKOUT ALERT</b>\\n"
        f"???????????????????\\n"
        f"Ticker: <b>{ticker}</b>\\n"
        f"Action: <b>{signal_type}</b> | Grade: <b>{grade}</b>\\n"
        f"Trigger Price: <b>${price:.2f}</b>\\n"
        f"???????????????????"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": f"? Accept & Execute {ticker}", "callback_data": f"exec_buy_{ticker}"},
                    {"text": "? Reject", "callback_data": f"reject_{ticker}"}
                ]
            ]
        }
    }
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram dispatch error: {e}")
        return False
"""
    if "def send_interactive_telegram_alert" not in content:
        content += "\n\n" + telegram_code

    ast.parse(content)
    with open(core_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("? Successfully patched hapt_invest_core.py with Confidence Grading & Interactive Telegram Buttons!")
