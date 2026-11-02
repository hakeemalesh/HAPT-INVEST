import os

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Inspecting lines 110 to 130 of hapt_invest_core.py ---")
for idx in range(max(0, 110), min(len(lines), 130)):
    print(f"{idx+1}: {repr(lines[idx])}")
print("-" * 50)
