import scanner_engine
import valuation_engine
import escalator_engine

# High-Priority Core Focus Assets (for DCF Valuation & Trailing Risk Engine)
CORE_VALUATION_WATCHLIST = [
    "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA",
    "SHEL.L", "AZN.L", "HSBA.L", "BP.L", "GSK.L", "RIO.L"
]

PORTFOLIO = [
    {"ticker": "NVDA", "entry_price": 180.00, "peak_price": 235.00},
    {"ticker": "SHEL.L", "entry_price": 2400.00, "peak_price": 2650.00},
    {"ticker": "AAPL", "entry_price": 175.00, "peak_price": 220.00}
]

def main():
    print("=" * 50)
    print("🚀 LAUNCHING MULTI-EXCHANGE HAPT - INVEST PLATFORM")
    print("=" * 50 + "\n")

    print("--- [MODULE 1/3]: FULL MARKET DYNAMIC SCANNERS ---")
    # Fetch live S&P 500 + FTSE 100 universe automatically (Pass None to trigger dynamic fetch)
    scanner_engine.run_phase2_pipeline(watchlist=None)
    print("\n")

    print("--- [MODULE 2/3]: INTRINSIC VALUATION MODELS ---")
    valuation_engine.run_valuation_pipeline(CORE_VALUATION_WATCHLIST)
    print("\n")

    print("--- [MODULE 3/3]: TRAILING ESCALATOR RISK ENGINE ---")
    escalator_engine.run_escalator_pipeline(PORTFOLIO)
    print("\n")

    print("=" * 50)
    print("✅ MULTI-EXCHANGE PIPELINE EXECUTION COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()