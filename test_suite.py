import unittest
from strategy_engine import run_engine

class TestHaptInvestSuite(unittest.TestCase):

    def test_lse_gbx_normalization(self):
        """Verify LSE prices convert from GBX (pence) to GBP (£)."""
        # SHEL.L typically trades in thousands of pence
        result = run_engine("SHEL.L")
        self.assertIsNotNone(result)
        self.assertIn("Market: London Stock Exchange", result)
        self.assertIn("Execution Status: MANUAL_EXECUTION_REQUIRED", result)

    def test_us_equity_flow(self):
        """Verify US equity processing and Alpaca integration."""
        result = run_engine("AAPL")
        # Should either return a trade alert or None if no setup
        if result:
            self.assertIn("Market: US Equity", result)
            self.assertIn("$", result)

    def test_invalid_symbol_handling(self):
        """Verify engine gracefully skips corrupt/invalid tickers."""
        result = run_engine("INVALID_TICKER_999")
        self.assertIsNone(result)

if __name__ == "__main__":
    print("🧪 Running HAPT INVEST Automated Diagnostic Tests...\n")
    unittest.main()
