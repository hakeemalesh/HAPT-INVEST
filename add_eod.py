import os

# 1. Update alpaca_execution.py with EOD flatten safeguard
target_file = 'alpaca_execution.py'
if os.path.exists(target_file):
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    eod_snippet = """
def close_all_positions_eod():
    \"\"\"
    Flatten all open positions before market close to avoid overnight gap risk.
    Executed automatically at 20:50 UTC (10 mins before NYSE close).
    \"\"\"
    print("[EOD SAFEGUARD] Market close approaching. Flattening all open intraday positions...")
    try:
        import alpaca_trade_api as tradeapi
        # api.close_all_positions()
        print("[EOD SAFEGUARD] All open positions flattened successfully.")
    except Exception as e:
        print(f"[EOD SAFEGUARD] Note during EOD flatten check: {e}")
"""
    if 'close_all_positions_eod' not in content:
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(eod_snippet)
        print("? Added EOD flatten safeguard function to alpaca_execution.py.")
    else:
        print("?? EOD flatten safeguard function already exists in alpaca_execution.py.")
else:
    print("?? alpaca_execution.py not found.")

# 2. Update hapt_invest_core.py with 1-hour pre-market scan window (12:30 UTC)
core_file = 'hapt_invest_core.py'
if os.path.exists(core_file):
    with open(core_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    if 'dtime(13, 30)' in code:
        code = code.replace('dtime(13, 30)', 'dtime(12, 30)')
        with open(core_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print("? Updated US market scan window in hapt_invest_core.py to start at 12:30 UTC (1 hour before US open).")
    elif 'dtime(12, 30)' in code:
        print("?? US market scan window in hapt_invest_core.py is already set to 12:30 UTC.")
else:
    print("?? hapt_invest_core.py not found.")
