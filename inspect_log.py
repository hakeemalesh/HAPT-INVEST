with open('hapt_invest_core.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Inspecting log_signal in hapt_invest_core.py ---")
for idx, line in enumerate(lines):
    if 'def log_signal' in line:
        for i in range(idx, idx + 25):
            if i < len(lines):
                print(f"{i+1}: {repr(lines[i])}")
        break
print("-" * 50)
