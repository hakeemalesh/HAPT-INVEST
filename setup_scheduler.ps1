$action = New-ScheduledTaskAction -Execute "C:\Users\hakee\OneDrive\Desktop\HAPT INVEST\.venv\Scripts\python.exe" -Argument "C:\Users\hakee\OneDrive\Desktop\HAPT INVEST\main.py" -WorkingDirectory "C:\Users\hakee\OneDrive\Desktop\HAPT INVEST"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "08:15AM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "HAPT_Invest_Daily_Breakout" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "? Successfully registered HAPT_Invest_Daily_Breakout task to run every weekday at 8:15 AM!" -ForegroundColor Green
