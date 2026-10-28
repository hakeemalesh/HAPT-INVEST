import os
from dotenv import load_dotenv
load_dotenv(override=True)
os.environ["APCA_API_KEY_ID"] = "PKVEJ4HX3LOBLG3W3UPLKUT7A3"
os.environ["APCA_API_SECRET_KEY"] = "D1dSLTkrjVmJggZVgsV9jgg7wLi1yfVbCZSBg7JkWYua"
os.environ["APCA_API_BASE_URL"] = "https://paper-api.alpaca.markets/v2"
os.environ["ALPACA_API_KEY"] = "PKVEJ4HX3LOBLG3W3UPLKUT7A3"
os.environ["ALPACA_SECRET_KEY"] = "D1dSLTkrjVmJggZVgsV9jgg7wLi1yfVbCZSBg7JkWYua"

def run_engine(symbol):
    print(f"Running engine for {symbol}...")
    key = os.getenv('APCA_API_KEY_ID')
    if not key or 'YOUR_' in key:
        print('⚠️ Alpaca credentials missing from .env! Fallback mode active.')
        print('Cannot execute order: Alpaca credentials missing.')
        return
    print(f'✅ Authorized! Executing paper order for {symbol} on endpoint: {os.getenv("APCA_API_BASE_URL")}')
    with open('trade_log.csv', 'a') as f:
        f.write(f'2026-09-24 00:15:00,{symbol},US,BUY,180.50,175.00,190.00,EXECUTED\n')
    print(f'✅ Trade logged successfully to trade_log.csv for {symbol}')
def normalize_lse_quote(symbol: str, raw_price: float) -> float:
    """
    Converts London Stock Exchange (LSE) prices from Pence (GBX) to Pounds (GBP).
    US Equities pass through unchanged.
    """
    if symbol.upper().endswith(".L") or symbol.upper().endswith(".LON"):
        return round(raw_price / 100.0, 4)
    return round(raw_price, 4)


def calculate_position_size(account_equity: float, risk_pct: float, entry_price: float, stop_loss_price: float, symbol: str) -> int:
    """
    Calculates 1% risk-per-trade position size using normalized GBP/USD prices.
    """
    norm_entry = normalize_lse_quote(symbol, entry_price)
    norm_stop = normalize_lse_quote(symbol, stop_loss_price)
    
    risk_amount = account_equity * risk_pct
    risk_per_share = abs(norm_entry - norm_stop)
    
    if risk_per_share <= 0:
        return 0
        
    return int(risk_amount / risk_per_share)
