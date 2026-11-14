import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

def run_holistic_audit():
    print("=" * 70)
    print("📊 HAPT INVEST: WEEK 1 HOLISTIC EXPECTANCY & PERFORMANCE AUDIT")
    print("=" * 70)
    
    db_path = "hapt_invest.db"
    if not os.path.exists(db_path):
        print("❌ Database hapt_invest.db not found!")
        return

    conn = sqlite3.connect(db_path)
    
    # 1. Inspect Executed Orders
    print("\n[1] EXECUTED ORDERS & PLACEMENTS:")
    try:
        orders_df = pd.read_sql_query("SELECT * FROM executed_orders", conn)
        if orders_df.empty:
            print("   ⚠️ No executed orders logged yet.")
        else:
            print(orders_df.to_string(index=False))
    except Exception as e:
        print(f"   Error reading executed_orders: {e}")

    # 2. Inspect Portfolio Audit / Stop Tracking
    print("\n[2] PORTFOLIO & DYNAMIC STOP AUDIT:")
    try:
        audit_df = pd.read_sql_query("SELECT * FROM portfolio_audit", conn)
        if audit_df.empty:
            print("   ⚠️ No portfolio audit records found.")
        else:
            print(audit_df.tail(10).to_string(index=False))
    except Exception as e:
        print(f"   Error reading portfolio_audit: {e}")

    # 3. Inspect Trade Telemetry & Expectancy
    print("\n[3] TRADE TELEMETRY & EXPECTANCY METRICS:")
    try:
        telemetry_df = pd.read_sql_query("SELECT * FROM trade_telemetry", conn)
        if telemetry_df.empty:
            print("   ⚠️ No closed trade telemetry logged yet (Forward test in progress).")
            print("   💡 Expectancy analysis will populate as live positions take profit or hit stops.")
        else:
            print(telemetry_df.to_string(index=False))
            
            # Compute basic metrics if data exists
            wins = telemetry_df[telemetry_df['pnl'] > 0]
            losses = telemetry_df[telemetry_df['pnl'] <= 0]
            win_rate = len(wins) / len(telemetry_df) if len(telemetry_df) > 0 else 0
            total_pnl = telemetry_df['pnl'].sum()
            print(f"\n   -> Total Trades: {len(telemetry_df)}")
            print(f"   -> Win Rate: {win_rate * 100:.1f}%")
            print(f"   -> Cumulative PnL: ${total_pnl:,.2f}")
    except Exception as e:
        print(f"   Error reading trade_telemetry: {e}")

    conn.close()
    print("=" * 70)
    print("✅ Audit extraction complete. Ready for holistic review session.")
    print("=" * 70)

if __name__ == "__main__":
    run_holistic_audit()
