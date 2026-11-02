import os

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

import_statement = "from scanner_engine import TechnicalEngine\n"

if "from scanner_engine import TechnicalEngine" not in content and "import TechnicalEngine" not in content:
    # Insert import near the top of the file after existing imports
    content = import_statement + content
    print("? Added TechnicalEngine import to hapt_invest_core.py")

with open(core_file, 'w', encoding='utf-8') as f:
    f.write(content)
