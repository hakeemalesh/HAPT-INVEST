import yfinance as yf
import pandas as pd
import numpy as np

def run_segment1_analysis(ticker="NVDA"):
    print("=== HAPT INVEST: SEGMENT 1 (DAY TRADING) ENGINE TEST ===")
    print(f"Analyzing intraday 5-min structure for: {ticker}\n")
    
    # Download 5-day, 5-minute intraday data
    data = yf.download(tickers=ticker, period="5d", interval="5m", progress=False)
    
    if data.empty:
        print("Error: No market data fetched.")
        return

    # Extract 1D numpy arrays regardless of MultiIndex columns
    close_arr = np.array(data['Close']).flatten()
    high_arr = np.array(data['High']).flatten()
    low_arr = np.array(data['Low']).flatten()
    vol_arr = np.array(data['Volume']).flatten()

    # Clean scalar float
    last_close = float(close_arr[-1])

    # Calculate True Range & 14-period ATR
    high_low = high_arr - low_arr
    high_close = np.abs(high_arr[1:] - close_arr[:-1])
    low_close = np.abs(low_arr[1:] - close_arr[:-1])
    
    tr = np.maximum(high_low[1:], np.maximum(high_close, low_close))
    atr_series = pd.Series(tr).rolling(14).mean().values
    last_atr = float(atr_series[-1]) if len(atr_series) > 0 and not np.isnan(atr_series[-1]) else 1.50

    # Calculate Session VWAP
    dates = data.index.date
    latest_date = dates[-1]
    today_mask = (dates == latest_date)

    today_close = close_arr[today_mask]
    today_high = high_arr[today_mask]
    today_low = low_arr[today_mask]
    today_vol = vol_arr[today_mask]

    tp = (today_high + today_low + today_close) / 3.0
    cum_vol = np.cumsum(today_vol)
    cum_tp_vol = np.cumsum(tp * today_vol)
    
    vwap_arr = np.where(cum_vol > 0, cum_tp_vol / cum_vol, today_close)
    last_vwap = float(vwap_arr[-1])

    # Calculate RVOL (20-bar volume SMA)
    vol_sma20 = pd.Series(today_vol).rolling(20).mean().values
    rvol_arr = np.where(vol_sma20 > 0, today_vol / vol_sma20, 1.0)
    last_rvol = float(rvol_arr[-1]) if not np.isnan(rvol_arr[-1]) else 1.0

    stop_loss = last_close - (1.5 * last_atr)
    take_profit = last_close + (3.0 * last_atr)

    print(f"Latest Bar Time: {data.index[-1]}")
    print(f"Current Price:   ${last_close:.2f}")
    print(f"Session VWAP:    ${last_vwap:.2f}")
    print(f"5-Min ATR (14):  ${last_atr:.2f}")
    print(f"Intraday RVOL:   {last_rvol:.2f}x\n")

    print("--- SIGNAL EVALUATION ---")
    if last_close > last_vwap and last_rvol > 1.2:
        print("SIGNAL: [ BULLISH DAY TRADE ENTRY ]")
        print(f"Suggested Entry:                 ${last_close:.2f}")
        print(f"Dynamic Trailing Stop (-1.5 ATR): ${stop_loss:.2f}")
        print(f"Intraday Profit Target (+3.0 ATR): ${take_profit:.2f}")
    elif last_close < last_vwap:
        print("SIGNAL: [ BEARISH / NO TRADE ] - Price below Session VWAP.")
        print("Action: Stay in Cash or Exit Longs.")
    else:
        print("SIGNAL: [ NEUTRAL HOLD ] - Awaiting Volume Spike (RVOL > 1.2x).")

if __name__ == "__main__":
    run_segment1_analysis("NVDA")
