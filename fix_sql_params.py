import os
import ast

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Correct SQL insert with standard parameter placeholders (?)
old_sql_block = """        cursor.execute(\"\"\"
            INSERT INTO signals (timestamp, ticker, market, signal_type, grade, confidence, price, stop_loss, tp1, tp2, rvol, atr_expansion, status)
            VALUES ([SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS], [SUCCESS])
        \"\"\" """

new_sql_block = """        cursor.execute(\"\"\"
            INSERT INTO signals (timestamp, ticker, market, signal_type, grade, confidence, price, stop_loss, tp1, tp2, rvol, atr_expansion, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \"\"\" """

if "VALUES ([SUCCESS]" in content:
    content = content.replace(old_sql_block.strip(), new_sql_block.strip())
    print("? Successfully replaced placeholder values with parameterized ? bindings.")
else:
    print("?? Exact match for old_sql_block not found, performing regex replacement...")
    import re
    content = re.sub(r'VALUES\s*\(.*?\)', 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', content, flags=re.DOTALL)

# Validate AST
ast.parse(content)
print("? AST Parse Successful: 0 syntax errors!")

with open(core_file, 'w', encoding='utf-8') as f:
    f.write(content)
