import csv
import os
from datetime import datetime

LOG_FILE = "trade_log.csv"

def init_logger():
    """Ensure the CSV log exists with proper headers."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Ticker", "Market", "Action", "Price", "Stop_Loss", "Take_Profit", "Status"])

def log_trade(ticker, market, action, price, sl, tp, status):
    """Append a trade event entry to the log file."""
    init_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, ticker, market, action, price, sl, tp, status])

if __name__ == "__main__":
    init_logger()
    print(f"✅ Trade Logger Initialized: {LOG_FILE}")
