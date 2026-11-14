@echo off
cd /d "C:\Users\hakee\OneDrive\Desktop\HAPT INVEST"
echo [%DATE% %TIME%] 📊 HAPT INVEST: Generating Weekly Performance Report...
.\.venv\Scripts\python.exe hapt_report.py
echo [%DATE% %TIME%] ✅ Weekly Report Complete.
