import os

print("=" * 50)
print("?? SANITIZING BOM FROM ALL PYTHON FILES")
print("=" * 50)

for file in os.listdir('.'):
    if file.endswith('.py'):
        try:
            # Read with utf-8-sig (which automatically strips U+FEFF BOM)
            with open(file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            # Write back as clean UTF-8 without BOM
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"? Cleaned BOM from: {file}")
        except Exception as e:
            print(f"?? Note on {file}: {e}")

print("=" * 50)
