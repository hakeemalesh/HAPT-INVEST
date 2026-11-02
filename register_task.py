import subprocess
import os

python_path = os.path.abspath(r".\.venv\Scripts\python.exe")
script_path = os.path.abspath("main.py")
work_dir = os.path.abspath(".")

# Windows schtasks command to run every weekday (Mon-Fri) at 8:15 AM
cmd = [
    "schtasks", "/Create", "/TN", "HAPT_Invest_Daily_Breakout",
    "/TR", f'"{python_path} {script_path}"',
    "/SC", "WEEKLY", "/D", "MON,TUE,WED,THU,FRI", "/ST", "08:15",
    "/F"
]

print("?? Registering Windows Task Scheduler job...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("? Successfully registered HAPT_Invest_Daily_Breakout task!")
    print("?? Schedule: Every Monday through Friday at 8:15 AM.")
else:
    print(f"? Task registration failed: {result.stderr}")
