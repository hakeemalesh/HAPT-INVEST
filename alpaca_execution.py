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
