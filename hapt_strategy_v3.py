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
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")

class HaptInstitutionalUniverseBacktester:
    def __init__(self):
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.db_path = "hapt_invest.db"
        # Robust institutional universe of liquid equities in the $3-$40 sweet spot
        self.universe = [
            "SOFI", "PLTR", "F", "NIO", "AMD", "INTC", "BAC", "SNAP", "VALE", 
            "CCL", "PBR", "AAL", "LCID", "PLUG", "UBER", "LYFT", "RIVN", "NCLH",
            "KGC", "BTBT", "X", "CLF", "HAL", "MU", "SCHW", "PYPL", "HOOD", "DKNG"
        ]

    def run_backtest(self, days=180):
        print("=" * 65)
        print("🏛️ HAPT INVEST: INSTITUTIONAL MULTI-ASSET MEAN REVERSION BACKTEST")
        print(f"📊 Testing {len(self.universe)} equities over the last {days} days (IEX Feed)...")
        print("=" * 65)

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days + 40)

        all_trades = []

        for ticker in self.universe:
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
                    continue

                data = df.loc[ticker].copy()
                
                # Mathematical Indicators for Mean Reversion
                data['sma_20'] = data['close'].rolling(20).mean()
                data['std_20'] = data['close'].rolling(20).std()
                data['z_score'] = (data['close'] - data['sma_20']) / data['std_20']
                
                high_low = data['high'] - data['low']
                high_close = np.abs(data['high'] - data['close'].shift())
                low_close = np.abs(data['low'] - data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = np.max(ranges, axis=1)
                data['atr'] = true_range.rolling(14).mean()

                in_position = False
                entry_price = 0.0
                stop_loss = 0.0
                target_price = 0.0

                for i in range(30, len(data)):
                    current_close = data['close'].iloc[i]
                    current_low = data['low'].iloc[i]
                    current_high = data['high'].iloc[i]
                    current_z = data['z_score'].iloc[i]
                    current_sma = data['sma_20'].iloc[i]
                    current_atr = data['atr'].iloc[i]

                    if pd.isna(current_z) or pd.isna(current_atr):
                        continue

                    if not in_position:
                        # Stricter Z-Score Entry: <= -2.0 (95% statistical oversold extreme) in sweet spot
                        if 3.0 <= current_close <= 40.0 and current_z <= -2.0:
                            in_position = True
                            entry_price = current_close
                            stop_loss = entry_price - (2.5 * current_atr) 
                            target_price = current_sma 
                    else:
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

                print(f"✅ Successfully simulated mean reversion for {ticker}")

            except Exception as e:
                print(f"⚠️ Error processing {ticker}: {e}")

        if not all_trades:
            print("⚠️ No completed trades generated across universe.")
            return

        trades_df = pd.DataFrame(all_trades)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]

        win_rate = len(wins) / len(trades_df) if len(trades_df) > 0 else 0
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 1
        profit_factor = (wins['pnl'].sum() / abs(losses['pnl'].sum())) if len(losses) > 0 and losses['pnl'].sum() != 0 else float('inf')
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        print("\n📈 INSTITUTIONAL MULTI-ASSET BACKTEST RESULTS:")
        print(f"   -> Total Simulated Trades: {len(trades_df)}")
        print(f"   -> Win Rate:               {win_rate * 100:.2f}%")
        print(f"   -> Average Win:            ${avg_win:.2f}")
        print(f"   -> Average Loss:           ${avg_loss:.2f}")
        print(f"   -> Profit Factor:          {profit_factor:.2f}")
        print(f"   -> Mathematical Expectancy: ${expectancy:.2f} per trade")
        print("=" * 65)

if __name__ == "__main__":
    backtester = HaptInstitutionalUniverseBacktester()
    backtester.run_backtest()
