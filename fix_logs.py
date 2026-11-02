import os

core_file = 'hapt_invest_core.py'
if os.path.exists(core_file):
    with open(core_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Replace common log emojis with clean text tags
    replacements = {
        '??': '[LOCKED]',
        '??': '[ACTIVE]',
        '??': '[READY]',
        '??': '[WARNING]',
        '?': '[ERROR]',
        '?': '[SUCCESS]',
        '??': '[INFO]'
    }
    
    for emoji, tag in replacements.items():
        code = code.replace(emoji, tag)
        
    with open(core_file, 'w', encoding='utf-8') as f:
        f.write(code)
    print("? Successfully sanitized all log emojis in hapt_invest_core.py for Windows terminal compatibility!")
else:
    print("?? hapt_invest_core.py not found.")
