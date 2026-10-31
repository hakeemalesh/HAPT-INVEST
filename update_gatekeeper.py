import os

core_file = 'hapt_invest_core.py'
if os.path.exists(core_file):
    with open(core_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # Define the new robust ET-aware market gatekeeper snippet
    et_gatekeeper_snippet = """
def is_us_open() -> bool:
    \"\"\"
    Dynamically checks if US market is in its active window (8:30 AM to 4:00 PM Eastern Time),
    accounting automatically for US/UK clock changes.
    \"\"\"
    try:
        from zoneinfo import ZoneInfo # Python 3.9+ standard library
    except ImportError:
        from pytz import timezone as ZoneInfo
        
    try:
        now_et = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        # Fallback if timezone database is missing
        now_et = datetime.now()

    if now_et.weekday() >= 5: # Weekend check
        return False
        
    current_time = now_et.time()
    # 8:30 AM ET (1 hour pre-market scan start) to 4:00 PM ET (EOD close)
    return dtime(8, 30) <= current_time <= dtime(16, 0)
"""

    # If is_us_open exists, let's replace it with the robust dynamic version
    if 'def is_us_open' in code:
        # Find and replace the old is_us_open function block
        import re
        code = re.sub(r'def is_us_open\(\).*?(?=\ndef |\Z)', et_gatekeeper_snippet.strip() + '\n\n', code, flags=re.DOTALL)
        with open(core_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print("? Successfully upgraded is_us_open() to a dynamic Eastern Time-aware gatekeeper!")
    else:
        print("?? Could not locate def is_us_open in hapt_invest_core.py.")
else:
    print("?? hapt_invest_core.py not found.")
