import yfinance as yf

ticker = "NVDA"
print("--- SEGMENT 1: INTRADAY 5-MIN DATA TEST ---")
df_intraday = yf.download(tickers=ticker, period="1d", interval="5m")
print(f"Ticker: {ticker}")
print(f"Total 5-Min Bars Captured Today: {len(df_intraday)}")
print(df_intraday.tail(3))
