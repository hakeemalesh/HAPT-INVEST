import os
import ast

core_file = 'hapt_invest_core.py'
with open(core_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'def is_us_open' in line:
        new_lines.append(line)
        i += 1
        # Process the body of is_us_open and indent by 8 spaces
        while i < len(lines):
            body_line = lines[i]
            stripped = body_line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            if stripped == "":
                new_lines.append("\n")
                i += 1
                continue
            # Apply correct 8-space indentation for class staticmethod body
            new_lines.append("        " + stripped + "\n")
            i += 1
    else:
        new_lines.append(line)
        i += 1

full_code = "".join(new_lines)

# Validate with AST
try:
    ast.parse(full_code)
    print("? AST Syntax Check Passed: 100% valid Python syntax!")
    with open(core_file, 'w', encoding='utf-8') as f:
        f.write(full_code)
    print("? Successfully wrote corrected code to hapt_invest_core.py.")
except SyntaxError as e:
    print(f"? Syntax Error: {e}")
    exit(1)
