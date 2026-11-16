import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def load_parameters(path="parameters.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class HaptAutoExitMonitor:
    def __init__(self, param_path="parameters.json"):
        self.params = load_parameters(param_path)
        self.param_version = self.params.get("version", "v2.2.0")
        self.trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

    def send_telegram_alert(self, message):
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Telegram dispatch error: {e}")

    def compute_rsi(self, series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def monitor_and_execute_exits(self):
        s_cfg = self.params["strategy"]
        rsi_win = s_cfg.get("rsi_period", 14)
        rsi_target = s_cfg.get("rsi_exit_target", 50.0)

        print("=" * 72)
        print(f"HAPT INVEST [{self.param_version}]: AUTOMATED RSI {rsi_target:.0f} EXIT EXECUTOR")
        print("=" * 72)
        try:
            positions = self.trading_client.get_all_positions()
            if not positions:
                print("No active positions found in portfolio.")
                return

            end_date = datetime.now()
            start_date = end_date - timedelta(days=45)

            for pos in positions:
                ticker = pos.symbol
                current_price = float(pos.current_price)
                avg_entry = float(pos.avg_entry_price)
                qty = float(pos.qty)
                side = pos.side

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
                data["rsi"] = self.compute_rsi(data["close"], rsi_win)
                current_rsi = float(data["rsi"].iloc[-1])

                print(f"Holding {ticker} | Entry: ${avg_entry:.2f} | Current: ${current_price:.2f} | RSI: {current_rsi:.1f}")

                long_exit = (side == "long" and current_rsi >= rsi_target)
                short_exit = (side == "short" and current_rsi <= rsi_target)

                if long_exit or short_exit:
                    print(f"TARGET REACHED: Closing {ticker} ({side}) at RSI {current_rsi:.1f}...")
                    close_side = OrderSide.SELL if side == "long" else OrderSide.BUY

                    market_order_data = MarketOrderRequest(
                        symbol=ticker,
                        qty=abs(qty),
                        side=close_side,
                        time_in_force=TimeInForce.GTC
                    )
                    self.trading_client.submit_order(order_data=market_order_data)

                    alert_msg = (
                        f"*HAPT AUTO-EXIT EXECUTED [{self.param_version}]*\n"
                        f"Symbol: `{ticker}` ({side.upper()})\n"
                        f"Entry: `${avg_entry:.2f}` | Exit: `${current_price:.2f}`\n"
                        f"RSI Centerline: `{current_rsi:.1f}` (Target: `{rsi_target:.0f}`)"
                    )
                    self.send_telegram_alert(alert_msg)
                else:
                    print(f"   -> Holding steady. Awaiting RSI {rsi_target:.0f} centerline (Current: {current_rsi:.1f})")

        except Exception as e:
            print(f"Error in exit monitor: {e}")


if __name__ == "__main__":
    monitor = HaptAutoExitMonitor()
    monitor.monitor_and_execute_exits()
