import yfinance as yf
import pandas as pd
import numpy as np

tickers = ["SOFI", "F", "AAL", "CLSK", "KGC", "NCLH", "RBLX", "PLTR", "LCID", "MARA", "BAC"]

print("==================================================")
print("   HAPT INVEST | PERMANENT BACKTEST AUDIT TOOL    ")
print("==================================================")

total_checked = 0
winning_trades = 0
losing_trades = 0
total_pnl_pct = 0.0

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="60d", interval="1h").dropna()
        if df.empty or len(df) < 50:
            continue
            
        close, high, low, vol = df['Close'], df['High'], df['Low'], df['Volume']
        avg_vol = vol.rolling(20).mean()
        tr = np.maximum(high - low, np.abs(low - close.shift(1)))
        atr = tr.rolling(14).mean()
        avg_atr = tr.mean()
        vwap = (vol * (high + low + close) / 3).cumsum() / vol.cumsum()
        
        for i in range(30, len(df) - 10):
            total_checked += 1
            p = float(close.iloc[i])
            prev_p = float(close.iloc[i-1])
            if not (3.0 <= p <= 35.0) or ((p - prev_p) / prev_p) * 100 <= 0.3 or p < float(vwap.iloc[i]):
                continue
            if (vol.iloc[i] / (avg_vol.iloc[i] if avg_vol.iloc[i] > 0 else 1.0)) < 1.4:
                continue
            if (atr.iloc[i] / (float(avg_atr) if avg_atr > 0 else 1.0)) < 1.2:
                continue
                
            sl = p - (1.5 * float(atr.iloc[i]))
            tp = p + (2.0 * float(atr.iloc[i]))
            
            for j in range(i + 1, min(i + 10, len(df))):
                if float(low.iloc[j]) <= sl:
                    total_pnl_pct += ((sl - p) / p) * 100
                    losing_trades += 1
                    break
                elif float(high.iloc[j]) >= tp:
                    total_pnl_pct += ((tp - p) / p) * 100
                    winning_trades += 1
                    break
    except:
        continue

closed = winning_trades + losing_trades
print(f"Total Bars Scanned: {total_checked}")
print(f"Total Completed Signals: {closed}")
if closed > 0:
    print(f"Win Rate: {(winning_trades/closed)*100:.2f}% ({winning_trades}W / {losing_trades}L)")
    print(f"Average Return: {total_pnl_pct/closed:.2f}%")
