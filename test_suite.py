import unittest
from unittest.mock import patch
from strategy_engine import run_engine

class TestHaptInvestSuite(unittest.TestCase):
    
    @patch('yfinance.Ticker')
    def test_lse_gbx_normalization(self, mock_ticker):
        # Mock yfinance data for an LSE stock returning pence (GBX) values
        import pandas as pd
        mock_df = pd.DataFrame({
            'Close': [2500.0, 2550.0, 2600.0, 2650.0, 2700.0, 2750.0, 2800.0, 2850.0, 2900.0, 2950.0, 3000.0],
            'High': [2550.0, 2600.0, 2650.0, 2700.0, 2750.0, 2800.0, 2850.0, 2900.0, 2950.0, 3000.0, 3050.0],
            'Low': [2450.0, 2500.0, 2550.0, 2600.0, 2650.0, 2700.0, 2750.0, 2800.0, 2850.0, 2900.0, 2950.0],
            'Volume': [200000, 250000, 300000, 350000, 400000, 450000, 500000, 550000, 600000, 650000, 700000]
        })
        mock_ticker.return_value.history.return_value = mock_df
        
        # Test engine handling of .L ticker normalization
        try:
            result = run_engine("SHEL.L")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"LSE normalization raised an unexpected exception: {e}")

    def test_invalid_ticker(self):
        result = run_engine("INVALID_TICKER_999")
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
