import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")

class HaptOptimizedBacktester:
    def __init__(self):
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.db_path = "hapt_invest.db"

    def run_optimized_backtest(self, symbols=["SOFI", "F", "NIO", "PLTR"], days=90):
        print("=" * 65)
        print("🏛️ HAPT INVEST: OPTIMIZED QUANTITATIVE BACKTESTER (RVOL + 3x ATR)")
        print(f"📊 Analyzing {symbols} over the last {days} days (IEX Feed)...")
        print("=" * 65)

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days + 30) # Extra buffer for indicators

        all_trades = []

        for ticker in symbols:
            try:
                req = StockBarsRequest(
                    symbol_or_symbols=ticker,
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    end=end_date,
                    feed=DataFeed.IEX
                )
                bars = self.data_client.get_stock_bars(req)
                df = bars.df
                
                if df.empty or ticker not in df.index.get_level_values(0):
                    print(f"⚠️ Insufficient historical data for {ticker}")
                    continue

                data = df.loc[ticker].copy()
                
                # Indicators
                high_low = data['high'] - data['low']
                high_close = np.abs(data['high'] - data['close'].shift())
                low_close = np.abs(data['low'] - data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = np.max(ranges, axis=1)
                data['atr'] = true_range.rolling(14).mean()
                data['volume_sma'] = data['volume'].rolling(20).mean()
                data['rvol'] = data['volume'] / data['volume_sma']

                in_position = False
                entry_price = 0.0
                peak_price = 0.0
                stop_loss = 0.0
                target_price = 0.0

                for i in range(30, len(data)):
                    current_close = data['close'].iloc[i]
                    current_high = data['high'].iloc[i]
                    current_low = data['low'].iloc[i]
                    current_atr = data['atr'].iloc[i]
                    current_rvol = data['rvol'].iloc[i]

                    if pd.isna(current_atr) or pd.isna(current_rvol):
                        continue

                    if not in_position:
                        sma_20 = data['close'].iloc[i-20:i].mean()
                        # Enhanced Entry Rule: Price in $3-$40 sweet spot, RVOL > 1.3, Close > 20 SMA
                        if 3.0 <= current_close <= 40.0 and current_close > sma_20 and current_rvol >= 1.3:
                            in_position = True
                            entry_price = current_close
                            peak_price = current_close
                            stop_loss = entry_price - (3.0 * current_atr) # Wider 3.0x ATR buffer
                            target_price = entry_price + (2.5 * (3.0 * current_atr)) # 2.5 R/R target
                    else:
                        if current_high > peak_price:
                            peak_price = current_high
                            # Trailing stop ratchets up
                            new_stop = peak_price - (3.0 * current_atr)
                            if new_stop > stop_loss:
                                stop_loss = new_stop

                        # Exit check: Hit target, hit stop loss, or end of series
                        if current_high >= target_price:
                            exit_price = target_price
                            pnl = exit_price - entry_price
                            return_pct = (pnl / entry_price) * 100
                            all_trades.append({"ticker": ticker, "pnl": pnl, "return_pct": return_pct, "outcome": "WIN"})
                            in_position = False
                        elif current_low <= stop_loss or i == len(data) - 1:
                            exit_price = stop_loss if current_low <= stop_loss else current_close
                            pnl = exit_price - entry_price
                            return_pct = (pnl / entry_price) * 100
                            outcome = "WIN" if pnl > 0 else "LOSS"
                            all_trades.append({"ticker": ticker, "pnl": pnl, "return_pct": return_pct, "outcome": outcome})
                            in_position = False

                print(f"✅ Successfully backtested {ticker} with RVOL filter")

            except Exception as e:
                print(f"❌ Error backtesting {ticker}: {e}")

        if not all_trades:
            print("⚠️ No completed trades generated in optimized simulation.")
            return

        trades_df = pd.DataFrame(all_trades)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]

        win_rate = len(wins) / len(trades_df)
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 1
        profit_factor = (wins['pnl'].sum() / abs(losses['pnl'].sum())) if len(losses) > 0 and losses['pnl'].sum() != 0 else float('inf')
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        print("\n📈 OPTIMIZED QUANTITATIVE BACKTEST RESULTS:")
        print(f"   -> Total Simulated Trades: {len(trades_df)}")
        print(f"   -> Win Rate:               {win_rate * 100:.2f}%")
        print(f"   -> Average Win:            ${avg_win:.2f}")
        print(f"   -> Average Loss:           ${avg_loss:.2f}")
        print(f"   -> Profit Factor:          {profit_factor:.2f}")
        print(f"   -> Mathematical Expectancy: ${expectancy:.2f} per trade")
        print("=" * 65)

if __name__ == "__main__":
    tester = HaptOptimizedBacktester()
    tester.run_optimized_backtest()
