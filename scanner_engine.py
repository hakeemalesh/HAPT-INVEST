import logging
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Initialize Alpaca Data Client (Uses Paper/Live API keys from environment or config)
# Replace API_KEY and SECRET_KEY if loaded via os.getenv
ALPACA_API_KEY = "YOUR_ALPACA_KEY"
ALPACA_SECRET_KEY = "YOUR_ALPACA_SECRET"

def fetch_realtime_5m_bars(ticker):
    """Fetches real-time 5-minute bars from Alpaca for US equities to eliminate yfinance delays."""
    try:
        client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        request_params = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=TimeFrame.Minute,
            start=datetime.utcnow() - timedelta(days=2)
        )
        bars = client.get_stock_bars(request_params)
        df = bars.df
        if not df.empty:
            logging.info(f"Successfully fetched real-time Alpaca bars for {ticker}")
            return df
    except Exception as e:
        logging.warning(f"Alpaca live feed fallback to yfinance for {ticker}: {e}")
    
    # Fallback for UK (LSE) tickers or API key bypass
    data = yf.download(tickers=ticker, period="2d", interval="5m", progress=False)
    return data
