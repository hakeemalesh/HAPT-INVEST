import os
import ast
import re

core_file = "hapt_invest_core.py"
with open(core_file, "r", encoding="utf-8") as f:
    content = f.read()

new_code = '''

def calculate_ai_confidence_score(rvol: float, atr_expansion: float) -> int:
    \"\"\"Calculates a dynamic AI confidence percentage (60% to 99%) based on momentum depth.\"\"\"
    raw_score = 50 + (rvol * 10) + (atr_expansion * 5)
    return min(99, max(60, int(raw_score)))

def send_interactive_telegram_alert(ticker: str, price: float, grade: str, signal_type: str, rvol: float, atr_expansion: float):
    import requests
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return False
        
    confidence_pct = calculate_ai_confidence_score(rvol, atr_expansion)
    
    message = (
        "?? <b>[HAPT INVEST] AI BREAKOUT REVIEW</b>\\n"
        "???????????????????\\n"
        f"Ticker: <b>{ticker}</b>\\n"
        f"Action: <b>{signal_type}</b>\\n"
        f"Momentum Grade: <b>{grade}</b>\\n"
        f"AI Confidence: <b>{confidence_pct}%</b>\\n"
        f"Trigger Price: <b>${price:.2f}</b>\\n"
        "???????????????????"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": f"? Accept & Execute ({confidence_pct}%)", "callback_data": f"exec_buy_{ticker}"},
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
'''

content = re.sub(r'def calculate_ai_confidence_score\([\s\S]*?(?=\ndef |\Z)', '', content)
content = re.sub(r'def send_interactive_telegram_alert\([\s\S]*?(?=\ndef |\Z)', '', content)
content += new_code

ast.parse(content)

with open(core_file, "w", encoding="utf-8") as f:
    f.write(content)

print("? Successfully patched hapt_invest_core.py with AI Confidence Review & Interactive Buttons!")
