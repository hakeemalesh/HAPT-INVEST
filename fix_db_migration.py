import os
import ast

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Improved init_db with dynamic column migration (ALTER TABLE if missing)
new_init_db = """    @staticmethod
    def init_db():
        conn = sqlite3.connect("hapt_invest.db")
        cursor = conn.cursor()
        
        # Create base table if not exists
        cursor.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ticker TEXT,
                market TEXT,
                signal_type TEXT,
                grade TEXT,
                confidence REAL,
                price REAL,
                status TEXT
            )
        \"\"\")
        
        # Ensure all modern telemetry columns exist (auto-migration)
        cursor.execute("PRAGMA table_info(signals)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        
        required_columns = {
            "stop_loss": "REAL",
            "tp1": "REAL",
            "tp2": "REAL",
            "rvol": "REAL",
            "atr_expansion": "REAL"
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}")
                    print(f"[DB MIGRATION] Added missing column '{col_name}' to signals table.")
                except Exception as e:
                    print(f"[DB MIGRATION] Notice on adding {col_name}: {e}")
                    
        conn.commit()
        conn.close()"""

import re
# Replace existing init_db definition
pattern = r'    @staticmethod\s+def init_db\(\):.*?(?=\n    def |\ndef |\Z)'

if re.search(pattern, content, flags=re.DOTALL):
    content = re.sub(pattern, new_init_db, content, flags=re.DOTALL)
    print("? Successfully updated DatabaseManager.init_db() with auto-migration.")
else:
    print("?? Pattern match failed for init_db.")

# Validate AST
ast.parse(content)
print("? AST Parse Successful: 0 syntax errors!")

with open(core_file, 'w', encoding='utf-8') as f:
    f.write(content)
