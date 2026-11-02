import ast

with open('scanner_engine.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

print("=" * 50)
print("?? INSPECTING scanner_engine.py DEFINITIONS")
print("=" * 50)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print(f"?? Class: {node.name}")
        for subnode in node.body:
            if isinstance(subnode, ast.FunctionDef):
                print(f"   ??? Method: {subnode.name}")
    elif isinstance(node, ast.FunctionDef):
        print(f"?? Function: {node.name}")
print("=" * 50)
