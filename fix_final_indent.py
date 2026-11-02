import os
import ast

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

# The perfectly formatted staticmethod with 8-space body indentation
correct_method = """    @staticmethod
    def is_us_open() -> bool:
        \"\"\"
        Dynamically checks if US market is in its active window (8:30 AM to 4:00 PM Eastern Time),
        accounting automatically for US/UK clock changes.
        \"\"\"
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            from pytz import timezone as ZoneInfo
            
        try:
            now_et = datetime.now(ZoneInfo("America/New_York"))
        except Exception:
            now_et = datetime.now()

        if now_et.weekday() >= 5: # Weekend check
            return False
            
        current_time = now_et.time()
        return dtime(8, 30) <= current_time <= dtime(16, 0)"""

# Find and replace the block from @staticmethod down to the next function definition
import re
pattern = r'    @staticmethod\s+def is_us_open\(\) -> bool:.*?(?=\n    def |\ndef |\Z)'

if re.search(pattern, content, flags=re.DOTALL):
    content = re.sub(pattern, correct_method, content, flags=re.DOTALL)
    print("? Successfully replaced is_us_open() with correct 8-space indentation.")
else:
    print("?? Pattern match failed. Appending correct method.")
    content += "\n\n" + correct_method

# Validate via AST
ast.parse(content)
print("? AST Parse Successful: 0 syntax or indentation errors!")

with open(core_file, 'w', encoding='utf-8') as f:
    f.write(content)
