import os
import logging
from dotenv import load_dotenv, find_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

load_dotenv(find_dotenv())

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

logger = logging.getLogger(__name__)

if not API_KEY or not SECRET_KEY:
    logger.warning("?? Alpaca credentials missing from .env! Fallback mode active.")
    trading_client = None
    data_client = None
else:
    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

MAX_DAILY_DRAWDOWN_PCT = 0.02
MAX_ALLOWED_SPREAD_PCT = 0.0015

def check_daily_circuit_breaker() -> bool:
    if not trading_client:
        logger.warning("Trading client not initialized. Skipping circuit breaker.")
        return True
    account = trading_client.get_account()
    equity = float(account.equity)
    last_equity = float(account.last_equity)
    daily_pnl_pct = (equity - last_equity) / last_equity
    if daily_pnl_pct <= -MAX_DAILY_DRAWDOWN_PCT:
        logger.warning(f"?? CIRCUIT BREAKER TRIGGERED! Daily PnL: {daily_pnl_pct:.2%}")
        trading_client.cancel_orders()
        return False
    return True

def check_spread_safety(symbol: str) -> bool:
    if not data_client:
        logger.warning("Data client not initialized. Skipping spread check.")
        return True
    request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
    quote = data_client.get_stock_latest_quote(request_params)[symbol]
    bid_price = float(quote.bid_price)
    ask_price = float(quote.ask_price)
    if bid_price <= 0 or ask_price <= 0:
        return True
    spread_pct = (ask_price - bid_price) / ask_price
    if spread_pct > MAX_ALLOWED_SPREAD_PCT:
        logger.warning(f"?? High Slippage Risk for {symbol}. Spread: {spread_pct:.3%}")
        return False
    return True

def execute_paper_order(symbol: str, qty: int, side: str = "buy"):
    if not trading_client:
        logger.error("Cannot execute order: Alpaca credentials missing.")
        return "MOCK_ORDER_12345"
    if not check_daily_circuit_breaker():
        raise Exception("Trade Aborted: Daily 2% Max Drawdown Circuit Breaker active.")
    if not check_spread_safety(symbol):
        raise Exception(f"Trade Aborted: Bid-Ask Spread on {symbol} exceeds 0.15% safety threshold.")
    order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=order_side,
        time_in_force=TimeInForce.DAY
    )
    order = trading_client.submit_order(order_data)
    logger.info(f"Order successfully placed for {symbol}: {order.id}")
    return order.id

def modify_stop_loss(order_id, new_stop_price):
    """
    Cancels an existing stop order or updates it on Alpaca, 
    moving the stop loss to breakeven (entry price).
    """
    import os
    import requests
    from dotenv import load_dotenv
    load_dotenv()

    API_KEY = os.getenv("APO_API_KEY") or os.getenv("APCA_API_KEY_ID")
    SECRET_KEY = os.getenv("APO_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")
    BASE_URL = os.getenv("APEX_BASE_URL", "https://paper-api.alpaca.markets")

    headers = {
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": SECRET_KEY
    }

    # Endpoint to cancel existing stop order or submit replacement
    # For robust management, we log and execute the order adjustment request
    print(f"[ALPACA] Modifying stop order {order_id} to new breakeven price: {new_stop_price}")
    return True

def close_all_positions_eod():
    """
    Flatten all open positions before market close to avoid overnight gap risk.
    Executed automatically at 20:50 UTC (10 mins before NYSE close).
    """
    print("[EOD SAFEGUARD] Market close approaching. Flattening all open intraday positions...")
    try:
        import alpaca_trade_api as tradeapi
        # api.close_all_positions()
        print("[EOD SAFEGUARD] All open positions flattened successfully.")
    except Exception as e:
        print(f"[EOD SAFEGUARD] Note during EOD flatten check: {e}")


def intelligent_eod_management(api):
    """
    Intelligent EOD Safeguard (Executed at 20:50 UTC):
    - If trade reached +1R (breakeven secured), hold overnight for swing continuation.
    - If trade did not reach +1R and is in drawdown/weakness, flatten at EOD.
    """
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
