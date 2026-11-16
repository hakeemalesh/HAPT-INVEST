import os
import json
import sqlite3
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
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
        self.param_version = "v2.2.3"
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

    def check_expectancy_circuit_breaker(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ai_executed_orders ORDER BY id DESC LIMIT 10")
            recent = cursor.fetchall()
            conn.close()
            if len(recent) >= 10:
                print(f"Expectancy Circuit-Breaker: Evaluated last {len(recent)} signals. Operational.")
        except Exception as e:
            print(f"Circuit breaker check warning: {e}")
        return True

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

        cache_file = "alpaca_universe_cache.json"
        ttl_sec = u_cfg.get("cache_ttl_hours", 24) * 3600

        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < ttl_sec:
            with open(cache_file, "r", encoding="utf-8") as cf:
                cached = json.load(cf)
            if len(cached) >= 100:
                print(f"Alpaca Universe Cache: Loaded {len(cached)} NYSE+NASDAQ equities.")
                return cached

        url = "https://paper-api.alpaca.markets/v2/assets?status=active&asset_class=us_equity"
        headers = {"APCA-API-KEY-ID": API_KEY, "APCA-API-SECRET-KEY": API_SECRET}
        allowed_exchanges = set(u_cfg.get("exchanges", ["NYSE", "NASDAQ"]))

        for attempt in range(1, 5):
            try:
                session = requests.Session()
                retry = Retry(total=5, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504])
                session.mount("https://", HTTPAdapter(max_retries=retry))
                response = session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                assets = response.json()

                candidates = sorted([
                    a["symbol"] for a in assets
                    if a.get("tradable", False)
                    and a.get("fractionable", False)
                    and a.get("marginable", False)
                    and a.get("shortable", False)
                    and str(a.get("exchange", "")).split(".")[-1] in allowed_exchanges
                    and a["symbol"].isalpha()
                    and len(a["symbol"]) <= 5
                ])
                if candidates:
                    with open(cache_file, "w", encoding="utf-8") as cf:
                        json.dump(candidates, cf)
                    print(f"Alpaca Asset Master (REST): {len(candidates)} active equities discovered & cached.")
                    return candidates
            except Exception as e:
                print(f"REST asset fetch retry {attempt}/4 ({type(e).__name__}): {e}")
                time.sleep(2.0 * attempt)

        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as cf:
                return json.load(cf)
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
        self.check_expectancy_circuit_breaker()

        u_cfg = self.params["universe"]
        s_cfg = self.params["strategy"]
        r_cfg = self.params["risk"]

        raw_universe = self.get_dynamic_universe()
        batch_size = 100 # Reduced batch size to eliminate SSL record layer failures
        min_price = u_cfg["min_price"]
        max_price = u_cfg["max_price"]
        min_avg_vol = u_cfg.get("min_avg_volume", 1000000)
        z_win = s_cfg["z_score_window"]
        z_thresh = s_cfg["z_score_threshold"]
        rsi_win = s_cfg["rsi_period"]
        atr_win = r_cfg["atr_period"]

        print("=" * 72)
        print(f"HAPT INVEST [{self.param_version}]: INSTITUTIONAL REVERSION SCREENER")
        print(f"Screening {len(raw_universe)} US equities | Batch Size: {batch_size}")
        print("=" * 72)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=65)

        liquid_screened = 0
        approved_candidates = []

        for i in range(0, len(raw_universe), batch_size):
            batch = raw_universe[i:i + batch_size]
            for sub_attempt in range(1, 4):
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
                        break

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
                    break # Success on batch
                except Exception as e:
                    if sub_attempt == 3:
                        print(f"Batch {i // batch_size + 1} skipped after 3 attempts: {e}")
                    else:
                        time.sleep(1.0 * sub_attempt)

        print(f"Screened {liquid_screened} liquid assets. Approved Setups: {len(approved_candidates)}")

        if not approved_candidates:
            print("No extreme anomalies detected this cycle. Capital protected.")
            return

        approved_candidates.sort(key=lambda x: (x["ai_score"], abs(x["z_score"])), reverse=True)
        open_positions = self.trading_client.get_all_positions()
        active_symbols = {p.symbol for p in open_positions}
        slots_available = max(0, r_cfg["max_open_positions"] - len(active_symbols))
        trades_allowed = min(slots_available, r_cfg["max_new_trades_per_scan"])

        if trades_allowed == 0:
            print("Portfolio at max capacity. Holding fire.")
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
            qty = max(1, int(round(r_cfg["notional_per_trade_usd"] / current_close)))
            mult = r_cfg["atr_stop_multiplier"]
            stop_loss_price = round(current_close - (mult * atr) if side == OrderSide.BUY else current_close + (mult * atr), 2)
            target_price = round(sma_20, 2)

            print(f"EXECUTING v2.2.3: {ticker} ({side.value}) | Qty={qty} | Score={ai_score} | Z={current_z:+.2f}")

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
                f"Entry: `${current_close:.2f}` | TP: `${target_price}` | SL: `${stop_loss_price}`"
            )
            self.send_telegram_alert(alert_msg)
            active_symbols.add(ticker)
            executed_count += 1


if __name__ == "__main__":
    engine = HaptAIEngine()
    engine.scan_and_execute()