import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")

def liquidate_legacy_positions():
    trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
    
    # Target legacy symbols to close out
    symbols_to_close = ["F", "NIO", "SOFI"]
    
    print("=" * 50)
    print("🧹 HAPT INVEST: LIQUIDATING LEGACY PAPER POSITIONS")
    print("=" * 50)
    
    for symbol in symbols_to_close:
        try:
            # Closes the entire open position for the symbol via market order
            response = trading_client.close_position(symbol_or_asset_id=symbol)
            print(f"✅ Successfully liquidated position for {symbol}")
        except Exception as e:
            print(f"⚠️ Could not liquidate {symbol} (Position may not exist): {e}")
            
    print("=" * 50)
    print("🎯 Liquidation sequence complete. Portfolio is reset!")
    print("=" * 50)

if __name__ == "__main__":
    liquidate_legacy_positions()
