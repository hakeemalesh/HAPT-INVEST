import os
import json
import sqlite3
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest, GetAssetsRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, AssetClass, AssetStatus
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
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


class HaptAIEngine:
    def __init__(self, param_path="parameters.json"):
        self.params = load_parameters(param_path)
        self.param_version = self.params.get("version", "v2.2.0")
        self.trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        self.db_path = "hapt_invest.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_executed_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT,
                side TEXT,
                signal_type TEXT,
                qty REAL,
                price REAL,
                ai_score REAL,
                status TEXT,
                param_version TEXT,
                z_score REAL,
                rsi REAL
            )
        """)
        existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(ai_executed_orders)").fetchall()}
        for col, col_type in [("param_version", "TEXT"), ("z_score", "REAL"), ("rsi", "REAL")]:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE ai_executed_orders ADD COLUMN {col} {col_type}")
        conn.commit()
        conn.close()

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

    def get_dynamic_universe(self):
        u_cfg = self.params["universe"]
        if u_cfg.get("mode") != "dynamic_alpaca_screener":
            return u_cfg.get("fallback_tickers", [])

        try:
            req = GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY)
            assets = self.trading_client.get_all_assets(req)
            allowed_exchanges = set(u_cfg.get("exchanges", ["NYSE", "NASDAQ"]))

            candidates = [
                a.symbol for a in assets
                if getattr(a, "tradable", False)
                and getattr(a, "fractionable", False)
                and getattr(a, "marginable", False)
                and getattr(a, "shortable", False)
                and str(getattr(a, "exchange", "")).split(".")[-1] in allowed_exchanges
                and a.symbol.isalpha()
                and len(a.symbol) <= 5
            ]
            candidates = sorted(candidates)
            print(f"Alpaca Asset Master: {len(candidates)} active fractionable/shortable NYSE+NASDAQ equities discovered.")
            return candidates
        except Exception as e:
            print(f"Dynamic asset fetch fallback ({e}). Using fallback list.")
            return u_cfg.get("fallback_tickers", [])

    def ai_decision_analysis(self, z_score, rsi, volume_surge):
        s_cfg = self.params["strategy"]
        z_thresh = s_cfg["z_score_threshold"]
        score = 0.0
        reasons = []

        if z_score <= -z_thresh:
            score += 0.5
            reasons.append(f"Strong Oversold Z-Score ({z_score:.2f})")
        elif z_score >= z_thresh:
            score += 0.5
            reasons.append(f"Strong Overbought Z-Score ({z_score:.2f})")

        if rsi <= s_cfg["rsi_oversold"]:
            score += 0.3
            reasons.append(f"Oversold RSI Confirmation ({rsi:.1f})")
        elif rsi >= s_cfg["rsi_overbought"]:
            score += 0.3
            reasons.append(f"Overbought RSI Confirmation ({rsi:.1f})")

        if volume_surge >= s_cfg["min_volume_surge"]:
            score += 0.2
            reasons.append(f"Healthy Volume Support ({volume_surge:.1f}x ADV)")

        return round(score, 2), reasons

    def scan_and_execute(self):
        u_cfg = self.params["universe"]
        s_cfg = self.params["strategy"]
        r_cfg = self.params["risk"]

        raw_universe = self.get_dynamic_universe()
        batch_size = u_cfg.get("batch_size", 200)
        min_price = u_cfg["min_price"]
        max_price = u_cfg["max_price"]
        min_avg_vol = u_cfg.get("min_avg_volume", 1000000)
        z_win = s_cfg["z_score_window"]
        z_thresh = s_cfg["z_score_threshold"]
        rsi_win = s_cfg["rsi_period"]
        atr_win = r_cfg["atr_period"]

        print("=" * 72)
        print(f"HAPT INVEST [{self.param_version}]: MARKET-WIDE DYNAMIC REVERSION SCREENER")
        print(f"Screening {len(raw_universe)} US equities | Filter: ${min_price:.2f}-${max_price:.2f}, ADV >= {min_avg_vol:,}")
        print("=" * 72)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=65)

        liquid_screened = 0
        near_misses = []
        approved_candidates = []

        for i in range(0, len(raw_universe), batch_size):
            batch = raw_universe[i:i + batch_size]
            try:
                req = StockBarsRequest(
                    symbol_or_symbols=batch,
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    end=end_date,
                    feed=DataFeed.IEX
                )
                bars = self.data_client.get_stock_bars(req)
                df = bars.df
                if df.empty:
                    continue

                available_symbols = df.index.get_level_values(0).unique()
                for ticker in available_symbols:
                    data = df.loc[ticker]
                    if len(data) < max(z_win, rsi_win, atr_win) + 2:
                        continue

                    current_close = float(data["close"].iloc[-1])
                    if not (min_price <= current_close <= max_price):
                        continue

                    vol_sma = float(data["volume"].rolling(z_win).mean().iloc[-1])
                    if pd.isna(vol_sma) or vol_sma < min_avg_vol:
                        continue

                    liquid_screened += 1

                    sma_20 = float(data["close"].rolling(z_win).mean().iloc[-1])
                    std_20 = float(data["close"].rolling(z_win).std().iloc[-1])
                    if pd.isna(std_20) or std_20 == 0:
                        continue

                    current_z = (current_close - sma_20) / std_20
                    current_rsi = float(self.compute_rsi(data["close"], rsi_win).iloc[-1])
                    current_vol_surge = float(data["volume"].iloc[-1]) / vol_sma

                    if pd.isna(current_rsi) or pd.isna(current_vol_surge):
                        continue

                    if abs(current_z) >= (z_thresh * 0.80):
                        near_misses.append((abs(current_z), ticker, current_close, current_z, current_rsi, current_vol_surge))

                    if not (current_z <= -z_thresh or current_z >= z_thresh):
                        continue

                    ai_score, reasons = self.ai_decision_analysis(current_z, current_rsi, current_vol_surge)
                    if ai_score < s_cfg["min_ai_score"]:
                        continue

                    high_low = data["high"] - data["low"]
                    high_close = np.abs(data["high"] - data["close"].shift())
                    low_close = np.abs(data["low"] - data["close"].shift())
                    atr = float(pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(atr_win).mean().iloc[-1])
                    if pd.isna(atr) or atr <= 0:
                        continue

                    approved_candidates.append({
                        "ticker": ticker,
                        "close": current_close,
                        "z_score": current_z,
                        "rsi": current_rsi,
                        "vol_surge": current_vol_surge,
                        "atr": atr,
                        "sma_20": sma_20,
                        "ai_score": ai_score,
                        "reasons": reasons
                    })

            except Exception as e:
                print(f"Batch {i // batch_size + 1} warning: {e}")

        print(f"Passed Price (${min_price}-${max_price}) & Liquidity (>= {min_avg_vol:,} ADV) Filter: {liquid_screened} liquid stocks")

        if near_misses:
            near_misses.sort(reverse=True)
            top_watch = ", ".join([f"{t} (${p:.2f} | Z={z:+.2f} | RSI={r:.1f})" for _, t, p, z, r, _ in near_misses[:5]])
            print(f"Top Radar Watchlist (|Z| >= {z_thresh * 0.80:.2f}): {top_watch}")

        if not approved_candidates:
            print("Zero assets crossed extreme Z-Score +/-2.0 threshold this cycle. Capital preserved.")
            return

        approved_candidates.sort(key=lambda x: (x["ai_score"], abs(x["z_score"])), reverse=True)
        print(f"{len(approved_candidates)} Qualified Institutional Setups Detected Across US Market!")

        open_positions = self.trading_client.get_all_positions()
        active_symbols = {p.symbol for p in open_positions}
        slots_available = max(0, r_cfg["max_open_positions"] - len(active_symbols))
        trades_allowed = min(slots_available, r_cfg["max_new_trades_per_scan"])

        if trades_allowed == 0:
            print(f"Portfolio at max capacity ({len(active_symbols)}/{r_cfg['max_open_positions']} open positions). Holding fire.")
            return

        executed_count = 0
        for cand in approved_candidates:
            if executed_count >= trades_allowed:
                break

            ticker = cand["ticker"]
            if ticker in active_symbols:
                continue

            current_close = cand["close"]
            current_z = cand["z_score"]
            current_rsi = cand["rsi"]
            atr = cand["atr"]
            sma_20 = cand["sma_20"]
            ai_score = cand["ai_score"]
            reasons = cand["reasons"]

            side = OrderSide.BUY if current_z <= -z_thresh else OrderSide.SELL
            qty = round(r_cfg["notional_per_trade_usd"] / current_close, 2)
            mult = r_cfg["atr_stop_multiplier"]
            stop_loss_price = round(current_close - (mult * atr) if side == OrderSide.BUY else current_close + (mult * atr), 2)
            target_price = round(sma_20, 2)

            print(f"EXECUTING TOP-RANKED SIGNAL [{self.param_version}]: {ticker} ({side.value}) | Score={ai_score} | Z={current_z:+.2f}")

            bracket_data = MarketOrderRequest(
                symbol=ticker,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.GTC,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=target_price),
                stop_loss=StopLossRequest(stop_price=stop_loss_price)
            )
            self.trading_client.submit_order(order_data=bracket_data)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO ai_executed_orders
                   (ticker, side, signal_type, qty, price, ai_score, status, param_version, z_score, rsi)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ticker, side.value, "AI_DYNAMIC_REVERSION", qty, current_close, ai_score, "SUBMITTED", self.param_version, round(current_z, 4), round(current_rsi, 2))
            )
            conn.commit()
            conn.close()

            alert_msg = (
                f"*HAPT AI TRADING DESK [{self.param_version}]*\n"
                f"Symbol: `{ticker}`\n"
                f"Signal: `{side.value} (AI Score: {ai_score})`\n"
                f"Z-Score: `{current_z:+.2f}` | RSI: `{current_rsi:.1f}`\n"
                f"Entry: `${current_close:.2f}` | TP: `${target_price}` | SL: `${stop_loss_price}`\n"
                f"Reasons: `{' | '.join(reasons)}`"
            )
            self.send_telegram_alert(alert_msg)
            active_symbols.add(ticker)
            executed_count += 1


if __name__ == "__main__":
    engine = HaptAIEngine()
    engine.scan_and_execute()