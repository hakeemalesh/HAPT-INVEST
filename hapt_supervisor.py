
# --- HAPT HEARTBEAT INTEGRATION ---
try:
    import hapt_heartbeat
    hapt_heartbeat.send_heartbeat("Supervisor started. Core engine online.")
except Exception as e:
    print(f"[WARN] Heartbeat startup ping failed: {e}")
# ----------------------------------

import subprocess
import time
import sys
import datetime
import os

print("==================================================")
print("     HAPT INVEST | CRASH-PROOF SUPERVISOR ACTIVE  ")
print("==================================================")

python_executable = r".\.venv\Scripts\python.exe"
target_script = "hapt_invest_core.py"

crash_count = 0
MAX_CRASHES_BEFORE_LOCKOUT = 5

while True:
    start_time = datetime.datetime.now()
    print(f"\n[INFO] [{start_time}] Starting autonomous core engine...")
    
    # Run the core trading daemon as a subprocess
    process = subprocess.Popen([python_executable, target_script])
    
    # Wait for process to complete (if it crashes, Popen returns exit code != 0)
    process.wait()
    
    runtime = (datetime.datetime.now() - start_time).total_seconds()
    
    if process.returncode != 0:
        crash_count += 1
        print(f"[CRITICAL] Core engine crashed with exit code {process.returncode} after {runtime:.1f} seconds.")
        print(f"[WARNING] Crash recovery counter: {crash_count}/{MAX_CRASHES_BEFORE_LOCKOUT}")
        
        # Prevent infinite crash-loops if something is fundamentally broken
        if crash_count >= MAX_CRASHES_BEFORE_LOCKOUT:
            print("[FATAL] Maximum crash limit reached. Halting supervisor to protect capital.")
            break
            
        print("[INFO] Restarting engine in 10 seconds...")
        time.sleep(10)
    else:
        print("[INFO] Core engine shut down normally.")
        break
