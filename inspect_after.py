with open('hapt_invest_core.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Current state of lines 110 to 145 ---")
for idx in range(109, min(len(lines), 145)):
    print(f"{idx+1}: {repr(lines[idx])}")
print("-" * 50)
