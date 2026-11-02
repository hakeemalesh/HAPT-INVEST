import ast

print("=" * 50)
print("?? INSPECTING scanner_engine.py")
print("=" * 50)
with open('scanner_engine.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        print(f"?? Function: {node.name}")
    elif isinstance(node, ast.ClassDef):
        print(f"?? Class: {node.name}")
        for sub in node.body:
            if isinstance(sub, ast.FunctionDef):
                print(f"   ??? Method: {sub.name}")

print("=" * 50)
print("?? INSPECTING main.py")
print("=" * 50)
with open('main.py', 'r', encoding='utf-8') as f:
    print(f.read())
print("=" * 50)
