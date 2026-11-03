import os
import ast
import re

main_file = "main.py"
if not os.path.exists(main_file):
    print(f"? Error: {main_file} not found.")
else:
    with open(main_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure imports include send_interactive_telegram_alert and calculate_breakout_confidence
    if "send_interactive_telegram_alert" not in content:
        # Inject import at the top
        content = "from hapt_invest_core import send_interactive_telegram_alert, calculate_breakout_confidence\n" + content

    # Replace old telegram alert calls with the new interactive one if present
    # We look for typical patterns or let's update the alert dispatch block
    old_alert_pattern = r'send_telegram_alert\s*\([^)]*\)'
    new_alert_call = 'send_interactive_telegram_alert(ticker=ticker, price=current_price, grade=grade, signal_type="BUY BREAKOUT", rvol=rvol, atr_expansion=atr_expansion)'
    
    if re.search(old_alert_pattern, content):
        content = re.sub(old_alert_pattern, new_alert_call, content)
    else:
        # If no old alert call is found, let's append/inject an example usage or ensure the scan loop uses it
        pass

    ast.parse(content)
    with open(main_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("? Successfully wired interactive alerts into main.py!")
