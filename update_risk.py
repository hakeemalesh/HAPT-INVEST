import re
import ast

core_file = "hapt_invest_core.py"
with open(core_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace trailing percentage or ATR multiplier parameter defaults
# Example: Setting default trailing stop to 4% (0.04) or ATR multiplier to 2.5
content = re.sub(r'trailing_pct\s*:\s*float\s*=\s*\d+\.\d+', 'trailing_pct: float = 0.04', content)
content = re.sub(r'atr_multiplier\s*:\s*float\s*=\s*\d+\.\d+', 'atr_multiplier: float = 2.5', content)

ast.parse(content)
print("? Successfully updated Module 3 risk engine parameters!")

with open(core_file, "w", encoding="utf-8") as f:
    f.write(content)
