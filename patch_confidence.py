import os
import ast

core_file = "hapt_invest_core.py"
with open(core_file, "r", encoding="utf-8") as f:
    content = f.read()

# Add AI Confidence Score calculator if missing
confidence_func = """
def calculate_ai_confidence_score(rvol: float, atr_expansion: float) -> int:
    \"\"\"Calculates a dynamic AI confidence percentage (60% to 99%) based on momentum depth.\"\"\"
    raw_score = 50 + (rvol * 10) + (atr_expansion * 5)
    return min(99, max(60, int(raw_score)))
"""

if "def calculate_ai_confidence_score" not in content:
    content += "\n\n" + confidence_func

# Update send_interactive_telegram_alert to include AI Confidence Review
updated_telegram_func = """
def send_interactive_telegram_alert(ticker: str, price: float, grade: str, signal_type: str, rvol: float, atr_expansion: float):
    import requests
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return False
        
    confidence_pct = calculate_ai_confidence_score(rvol, atr_expansion)
    
    message = (
        f"?? <b>[HAPT INVEST] AI BREAKOUT REVIEW</b>\\n"
        f"???????????????????\\n"
        f"Ticker: <b>{ticker}</b>\\n"
        f"Action: <b>{signal_type}</b>\\n"
        f"Momentum Grade: <b>{grade}</b>\\n"
        f"AI Confidence: <b>{confidence_pct}%</b>\\n"
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
"""

# Replace old telegram function or append if not present
if "def send_interactive_telegram_alert" in content:
    # Remove old definition up to the next def or end of file
    import re
    content = re.sub(r'def send_interactive_telegram_alert\([\s\S]*?(?=\ndef |\Z)', updated_telegram_func.strip(), content)
else:
    content += "\n\n" + updated_telegram_func

ast.parse(content)
with open(core_file, "w", encoding="utf-8") as f:
    f.write(content)

print("? Successfully updated hapt_invest_core.py with AI Confidence Review percentages!")
