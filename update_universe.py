import os
import ast

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Target $3-$40 high-momentum intraday universe
new_us_tickers = 'DEFAULT_US_TICKERS = ["SOUN", "PLTR", "RIG", "MARA", "RIOT", "LCID", "RUN", "AFRM", "SNDL", "CLSK"]'
new_uk_tickers = 'DEFAULT_UK_TICKERS = ["ITV.L", "BOO.L", "ASC.L", "RR.L", "GENC.L", "ENOG.L"]'

import re
content = re.sub(r'DEFAULT_US_TICKERS\s*=\s*\[.*?\]', new_us_tickers, content, flags=re.DOTALL)
content = re.sub(r'DEFAULT_UK_TICKERS\s*=\s*\[.*?\]', new_uk_tickers, content, flags=re.DOTALL)

ast.parse(content)
print("? Successfully updated intraday universe to $3?$40 price band assets!")

with open(core_file, 'w', encoding='utf-8') as f:
    f.write(content)
