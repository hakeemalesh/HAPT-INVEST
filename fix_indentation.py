import os
import re

core_file = 'hapt_invest_core.py'
if os.path.exists(core_file):
    with open(core_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Clean, perfectly indented is_us_open function
    clean_function = """def is_us_open() -> bool:
    \"\"\"
    Dynamically checks if US market is in its active window (8:30 AM to 4:00 PM Eastern Time),
    accounting automatically for US/UK clock changes.
    \"\"\"
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from pytz import timezone as ZoneInfo
        
    try:
        now_et = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now_et = datetime.now()

    if now_et.weekday() >= 5: # Weekend check
        return False
        
    current_time = now_et.time()
    return dtime(8, 30) <= current_time <= dtime(16, 0)"""

    # Replace existing is_us_open definition entirely
    if 'def is_us_open' in content:
        content = re.sub(r'def is_us_open\(\).*?(?=\ndef |\Z)', clean_function + '\n\n', content, flags=re.DOTALL)
    else:
        content += "\n\n" + clean_function

    with open(core_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("? Successfully repaired and indented is_us_open() in hapt_invest_core.py!")
else:
    print("? hapt_invest_core.py not found.")
