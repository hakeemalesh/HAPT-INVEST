import yfinance as yf
import pandas as pd
import numpy as np

def run_hapt_master_analysis(ticker="NVDA"):
    print("==================================================================")
    print(f"            HAPT INVEST UNIFIED PLATFORM ENGINE                  ")
    print("==================================================================")
    print(f"Target Asset: {ticker} | Running Dual-Segment Analysis...\n")

    # --------------------------------------------------------------------
    # SEGMENT 1: INTRADAY DAY TRADING ANALYSIS (5-Min Bars)
    # --------------------------------------------------------------------
    df_5m = yf.download(tickers=ticker, period="5d", interval="5m", progress=False)
    
    if not df_5m.empty:
        close_5m = np.array(df_5m['Close']).flatten()
        high_5m = np.array(df_5m['High']).flatten()
        low_5m = np.array(df_5m['Low']).flatten()
        vol_5m = np.array(df_5m['Volume']).flatten()

        last_close = float(close_5m[-1])

        # 14-period ATR
        high_low = high_5m - low_5m
        high_close = np.abs(high_5m[1:] - close_5m[:-1])
        low_close = np.abs(low_5m[1:] - close_5m[:-1])
        tr_5m = np.maximum(high_low[1:], np.maximum(high_close, low_close))
        atr_5m = pd.Series(tr_5m).rolling(14).mean().values
        last_atr_5m = float(atr_5m[-1]) if len(atr_5m) > 0 and not np.isnan(atr_5m[-1]) else 1.50

        # Session VWAP
        dates_5m = df_5m.index.date
        latest_date = dates_5m[-1]
        today_mask = (dates_5m == latest_date)

        today_close = close_5m[today_mask]
        today_high = high_5m[today_mask]
        today_low = low_5m[today_mask]
        today_vol = vol_5m[today_mask]

        tp = (today_high + today_low + today_close) / 3.0
        cum_vol = np.cumsum(today_vol)
        cum_tp_vol = np.cumsum(tp * today_vol)
        vwap_arr = np.where(cum_vol > 0, cum_tp_vol / cum_vol, today_close)
        last_vwap = float(vwap_arr[-1])

        # RVOL
        vol_sma20 = pd.Series(today_vol).rolling(20).mean().values
        rvol_arr = np.where(vol_sma20 > 0, today_vol / vol_sma20, 1.0)
        last_rvol = float(rvol_arr[-1]) if not np.isnan(rvol_arr[-1]) else 1.0

        stop_loss_s1 = last_close - (1.5 * last_atr_5m)
        target_s1 = last_close + (3.0 * last_atr_5m)

        print("--- [ SEGMENT 1: INTRADAY DAY TRADING ] ---")
        print(f"Current Price:           ${last_close:.2f}")
        print(f"Session VWAP:            ${last_vwap:.2f}")
        print(f"5-Min ATR (14):          ${last_atr_5m:.2f}")
        print(f"Intraday RVOL:           {last_rvol:.2f}x")
        
        if last_close > last_vwap and last_rvol > 1.2:
            print("SEGMENT 1 SIGNAL:        [ BULLISH DAY TRADE ] ?")
            print(f"  +- Suggested Entry:     ${last_close:.2f}")
            print(f"  +- Dynamic Stop (-1.5x): ${stop_loss_s1:.2f}")
            print(f"  +- Profit Target (+3x):  ${target_s1:.2f}\n")
        elif last_close < last_vwap:
            print("SEGMENT 1 SIGNAL:        [ BEARISH / CASH ] - Price Below VWAP\n")
        else:
            print("SEGMENT 1 SIGNAL:        [ NEUTRAL ] - Waiting for RVOL > 1.2x\n")

    # --------------------------------------------------------------------
    # SEGMENT 2: MULTI-MONTH INVESTMENT ANALYSIS (Daily Bars)
    # --------------------------------------------------------------------
    df_daily = yf.download(tickers=ticker, period="1y", interval="1d", progress=False)

    if not df_daily.empty:
        close_d = np.array(df_daily['Close']).flatten()
        last_daily_close = float(close_d[-1])

        sma_50 = float(pd.Series(close_d).rolling(50).mean().values[-1])
        sma_200 = float(pd.Series(close_d).rolling(200).mean().values[-1])
        
        high_52w = float(np.max(close_d))
        low_52w = float(np.min(close_d))

        target_30 = last_daily_close * 1.30
        target_50 = last_daily_close * 1.50
        stop_loss_s2 = last_daily_close * 0.92  # 8% Macro Hard Gate

        print("--- [ SEGMENT 2: MULTI-MONTH INVESTMENT (3-6M+) ] ---")
        print(f"Daily Close Price:       ${last_daily_close:.2f}")
        print(f"50-Day SMA:              ${sma_50:.2f}")
        print(f"200-Day SMA:             ${sma_200:.2f}")
        print(f"52-Week Range:           ${low_52w:.2f} - ${high_52w:.2f}")

        if last_daily_close > sma_50 and sma_50 > sma_200:
            print("SEGMENT 2 SIGNAL:        [ STRUCTURAL BULLISH ACCUMULATION ] ??")
            print(f"  +- Position Entry:      ${last_daily_close:.2f}")
            print(f"  +- Target 1 (30% Gain):  ${target_30:.2f}")
            print(f"  +- Target 2 (50% Gain):  ${target_50:.2f}")
            print(f"  +- Hard Macro Stop (-8%): ${stop_loss_s2:.2f}\n")
        else:
            print("SEGMENT 2 SIGNAL:        [ NEUTRAL / CONSOLIDATION ]\n")

    print("==================================================================")
    print("                 HAPT INVEST EXECUTION READY                      ")
    print("==================================================================")

if __name__ == "__main__":
    run_hapt_master_analysis("NVDA")
