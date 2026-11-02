import os
import ast

core_file = 'hapt_invest_core.py'
backup_file = 'hapt_invest_core_backup.py'

with open(core_file, 'r', encoding='utf-8') as f:
    core_content = f.read()

# 1. Remove the invalid import line if present
lines = [l for l in core_content.splitlines() if "from scanner_engine import TechnicalEngine" not in l]
core_content = "\n".join(lines)

# 2. Extract TechnicalEngine class code from backup file
with open(backup_file, 'r', encoding='utf-8') as f:
    backup_content = f.read()

import re
match = re.search(r'(class TechnicalEngine:.*?\n)(?=\nclass |\ndef |\Z)', backup_content, flags=re.DOTALL)

if match:
    tech_engine_code = match.group(1)
    print("? Extracted TechnicalEngine class from backup file.")
    
    # Place TechnicalEngine right before run_intraday_scan_cycle or at end of classes
    if "def run_intraday_scan_cycle" in core_content:
        core_content = core_content.replace("def run_intraday_scan_cycle", tech_engine_code + "\n\ndef run_intraday_scan_cycle")
    else:
        core_content += "\n\n" + tech_engine_code
else:
    print("?? Could not locate TechnicalEngine class in backup file via regex.")

# 3. Verify AST
try:
    ast.parse(core_content)
    print("? AST Parse Successful: 0 syntax errors!")
    with open(core_file, 'w', encoding='utf-8') as f:
        f.write(core_content)
    print("? Successfully restored TechnicalEngine into hapt_invest_core.py.")
except SyntaxError as e:
    print(f"? Syntax Error during restoration: {e}")
    exit(1)
