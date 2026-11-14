@echo off
cd /d "C:\Users\hakee\OneDrive\Desktop\HAPT INVEST"
echo [%DATE% %TIME%] 🏛️ HAPT INVEST: Starting Hourly Automated Pipeline...

echo Running AI Reversion Engine...
.\.venv\Scripts\python.exe hapt_engine_v4.py

echo Running Position Exit Monitor...
.\.venv\Scripts\python.exe hapt_monitor.py

echo [%DATE% %TIME%] ✅ HAPT Pipeline execution complete.
