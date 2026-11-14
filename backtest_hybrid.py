import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")

class HaptHybridBacktester:
    def __init__(self):
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.universe = [
            "SOFI", "PLTR", "F", "NIO", "AMD", "INTC", "BAC", "SNAP", "VALE", 
            "CCL", "PBR", "AAL", "LCID", "PLUG", "UBER", "LYFT", "RIVN", "NCLH",
            "KGC", "BTBT", "X", "CLF", "HAL", "MU", "SCHW", "PYPL", "HOOD", "DKNG",
            "ON", "WBD", "C", "T", "VZ", "PTON", "COIN", "MARA", "RIOT"
        ]

    def compute_rsi(self, series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def run_backtest(self):
        print("=" * 65)
        print("🏛️ HAPT INVEST: 180-DAY HYBRID BACKTEST (Z-SCORE + RSI)")
        print("=" * 65)

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=180)

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
                
                # Calculate Indicators
                data['sma_20'] = data['close'].rolling(20).mean()
                data['std_20'] = data['close'].rolling(20).std()
                data['z_score'] = (data['close'] - data['sma_20']) / data['std_20']
                data['rsi'] = self.compute_rsi(data['close'], 14)
                
                high_low = data['high'] - data['low']
                high_close = np.abs(data['high'] - data['close'].shift())
                low_close = np.abs(data['low'] - data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                data['atr'] = np.max(ranges, axis=1).rolling(14).mean()

                data = data.dropna()

                in_position = False
                entry_price = 0.0
                stop_loss = 0.0
                shares = 0.0

                for i in range(len(data)):
                    current_close = data['close'].iloc[i]
                    current_z = data['z_score'].iloc[i]
                    current_rsi = data['rsi'].iloc[i]
                    current_atr = data['atr'].iloc[i]
                    date_idx = data.index[i]

                    if not in_position:
                        # Hybrid Entry: Z-Score <= -2.0 AND RSI <= 30 AND Sweet Spot $3-$40
                        if 3.0 <= current_close <= 40.0 and current_z <= -2.0 and current_rsi <= 30.0:
                            in_position = True
                            entry_price = current_close
                            stop_loss = entry_price - (2.5 * current_atr)
                            shares = 500.0 / entry_price
                    else:
                        # Exit Logic: Hit Stop Loss OR RSI >= 50 (Profit Target Centerline)
                        if current_close <= stop_loss:
                            pnl = (stop_loss - entry_price) * shares
                            all_trades.append({"ticker": ticker, "type": "STOP_LOSS", "pnl": pnl, "return_pct": (stop_loss/entry_price - 1)*100})
                            in_position = False
                        elif current_rsi >= 50.0:
                            pnl = (current_close - entry_price) * shares
                            all_trades.append({"ticker": ticker, "type": "RSI_50_TARGET", "pnl": pnl, "return_pct": (current_close/entry_price - 1)*100})
                            in_position = False

            except Exception as e:
                print(f"⚠️ Error backtesting {ticker}: {e}")

        # Performance Summary Calculations
        if not all_trades:
            print("❌ No trades triggered across the 180-day window with these tight parameters.")
            return

        trades_df = pd.DataFrame(all_trades)
        total_trades = len(trades_df)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        win_rate = (len(wins) / total_trades) * 100
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 0
        expectancy = (len(wins)/total_trades * avg_win) - (len(losses)/total_trades * avg_loss)
        total_pnl = trades_df['pnl'].sum()

        print("\n" + "=" * 65)
        print("📊 180-DAY HYBRID BACKTEST PERFORMANCE RESULTS")
        print("=" * 65)
        print(f"Total Trades Executed : {total_trades}")
        print(f"Winning Trades        : {len(wins)} ({win_rate:.2f}%)")
        print(f"Losing Trades         : {len(losses)} ({100 - win_rate:.2f}%)")
        print(f"Average Win           : ${avg_win:.2f}")
        print(f"Average Loss          : ${avg_loss:.2f}")
        print(f"Mathematical Expectancy: ${expectancy:.2f} per trade")
        print(f"Cumulative Strategy PnL: ${total_pnl:,.2f}")
        print("=" * 65)

if __name__ == "__main__":
    tester = HaptHybridBacktester()
    tester.run_backtest()
