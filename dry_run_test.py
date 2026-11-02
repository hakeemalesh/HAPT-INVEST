import sys
import os

print("=" * 50)
print("?? HAPT INVEST END-TO-END DRY-RUN TEST")
print("=" * 50)

try:
    import hapt_invest_core
    print("? Successfully imported hapt_invest_core.")
    
    # Run a single manual scan cycle (will test market hours check, data pull, and logic)
    print("?? Triggering manual scan cycle test...")
    hapt_invest_core.run_intraday_scan_cycle()
    print("? Dry-run scan cycle completed successfully without crashes!")
except Exception as e:
    print(f"? Dry-run test caught an exception: {e}")
    import traceback
    traceback.print_exc()

print("=" * 50)
