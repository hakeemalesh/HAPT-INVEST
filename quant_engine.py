import numpy as np
import pandas as pd
import sqlite3

class QuantRiskEngine:
    def __init__(self, db_path='hapt_invest.db'):
        self.db_path = db_path

    def calculate_atr(self, high, low, close, window=14):
        """Calculates Average True Range for dynamic volatility stops."""
        tr1 = high - low
        tr2 = np.abs(high - close.shift(1))
        tr3 = np.abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=window).mean()

    def dynamic_chandelier_stop(self, peak_price, atr_value, multiplier=2.5):
        """Computes volatility-adjusted trailing stop to prevent noise whipsaws."""
        return peak_price - (multiplier * atr_value)

    def kelly_position_size(self, capital, win_rate, win_loss_ratio, max_risk_pct=0.02):
        """
        Computes optimal capital allocation using a constrained Kelly Criterion.
        """
        if win_loss_ratio <= 0:
            return capital * max_risk_pct
        
        kelly_f = (win_rate * (win_loss_ratio + 1) - 1) / win_loss_ratio
        # Apply fractional Kelly (half-Kelly) for institutional safety against drawdowns
        optimal_f = max(0.0, min(kelly_f * 0.5, max_risk_pct))
        return capital * optimal_f

    def log_trade_telemetry(self, ticker, entry, exit_val, pnl, strategy='breakout'):
        """Logs execution metrics to SQLite for automated expectancy audit."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl REAL,
                strategy TEXT
            )
        ''')
        cursor.execute('INSERT INTO trade_telemetry (ticker, entry_price, exit_price, pnl, strategy) VALUES (?, ?, ?, ?, ?)',
                       (ticker, entry, exit_val, pnl, strategy))
        conn.commit()
        conn.close()

print('✅ Quantitative Risk Engine compiled successfully.')
