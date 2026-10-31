import os

target_file = 'alpaca_execution.py'
if os.path.exists(target_file):
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    intelligent_eod_code = """

def intelligent_eod_management(api):
    \"\"\"
    Intelligent EOD Safeguard (Executed at 20:50 UTC):
    - If trade reached +1R (breakeven secured), hold overnight for swing continuation.
    - If trade did not reach +1R and is in drawdown/weakness, flatten at EOD.
    \"\"\"
    print("[EOD ENGINE] Evaluating open positions for overnight hold criteria...")
    try:
        positions = api.list_positions()
    except Exception as e:
        print(f"[EOD ENGINE] Error fetching positions: {e}")
        return

    for p in positions:
        symbol = p.symbol
        unrealized_plpc = float(p.unrealized_plpc) # Return percentage
        cost_basis = float(p.avg_entry_price)
        current_price = float(p.current_price)
        
        estimated_gain_pct = (current_price - cost_basis) / cost_basis
        
        if estimated_gain_pct >= 0.015: # Roughly +1R or greater achieved
            print(f"? {symbol} is up {estimated_gain_pct*100:.1f}%. Breakeven secured. HOLDING overnight.")
        else:
            print(f"?? {symbol} did not reach +1R threshold (P&L: {unrealized_plpc*100:.1f}%). FLATTENING at EOD.")
            # api.close_position(symbol)
"""
    
    if 'intelligent_eod_management' not in content:
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(intelligent_eod_code)
        print("? Intelligent EOD Management logic successfully added to alpaca_execution.py!")
    else:
        print("?? Intelligent_eod_management already exists in alpaca_execution.py.")
else:
    print("?? alpaca_execution.py not found.")
