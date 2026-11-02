import os
import ast

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Ensure DatabaseManager.init_db() is called inside run_intraday_scan_cycle
target = "def run_intraday_scan_cycle():"
replacement = "def run_intraday_scan_cycle():\n    DatabaseManager.init_db()"

if target in content and "DatabaseManager.init_db()" not in content.split("def run_intraday_scan_cycle():")[1][:100]:
    content = content.replace(target, replacement, 1)
    print("? Added DatabaseManager.init_db() call to run_intraday_scan_cycle()")

ast.parse(content)
print("? AST Parse Successful!")

with open(core_file, 'w', encoding='utf-8') as f:
    f.write(content)
