import os
import ast

print("=" * 50)
print("?? SEARCHING WORKSPACE FOR TechnicalEngine OR analyze_ticker")
print("=" * 50)

for file in os.listdir('.'):
    if file.endswith('.py') and file not in ['fix_bom.py', 'inspect_scanner.py', 'dry_run_test.py']:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'TechnicalEngine' in content or 'def analyze_ticker' in content or 'class Technical' in content:
                print(f"?? Found match in: {file}")
                tree = ast.parse(content)
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        print(f"   ??? Class: {node.name}")
                        for sub in node.body:
                            if isinstance(sub, ast.FunctionDef):
                                print(f"        ??? method: {sub.name}")
                    elif isinstance(node, ast.FunctionDef):
                        print(f"   ??? Function: {node.name}")
        except Exception as e:
            pass
print("=" * 50)
