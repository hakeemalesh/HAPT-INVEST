import os
import shutil
import datetime

print("==================================================")
print("     HAPT INVEST | DATABASE BACKUP UTILITY        ")
print("==================================================")

db_path = "hapt_invest.db"
backup_dir = "backups"

if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"[INFO] Created backup directory: {backup_dir}/")

if os.path.exists(db_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = os.path.join(backup_dir, f"hapt_invest_backup_{timestamp}.db")
    
    # Copy database safely
    shutil.copy2(db_path, backup_filename)
    print(f"[SUCCESS] Database successfully backed up to: {backup_filename}")
    
    # Keep last 10 backups cleanly
    backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')]
    if len(backup_files) > 10:
        oldest_backup = min(backup_files, key=os.path.getctime)
        os.remove(oldest_backup)
        print(f"[INFO] Rotated oldest backup: {oldest_backup}")
else:
    print(f"[WARN] No active database found at {db_path} to back up.")

print("==================================================")
