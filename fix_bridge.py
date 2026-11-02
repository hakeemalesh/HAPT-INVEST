with open('scanner_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

bridge_code = """

def run_phase2_pipeline(watchlist=None):
    \"\"\"
    Bridges main.py Module 1 call to HAPT INVEST core intraday scan engine.
    \"\"\"
    import hapt_invest_core
    print("[SCANNER ENGINE] Initializing Phase 2 Intraday Breakout Pipeline...")
    hapt_invest_core.run_intraday_scan_cycle()
"""

if "def run_phase2_pipeline" not in content:
    content += bridge_code
    with open('scanner_engine.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("? Successfully added run_phase2_pipeline bridge to scanner_engine.py")
else:
    print("?? run_phase2_pipeline already exists in scanner_engine.py")
