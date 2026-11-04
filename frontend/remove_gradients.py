import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to match linear-gradient(...) and capture the first color
    # Examples:
    # linear-gradient(135deg, #0d9488, #0b7a71) -> #0d9488
    # linear-gradient(to bottom, #f0fdf4, #e6f7ee) -> #f0fdf4
    # linear-gradient(135deg, #667eea 0%, #764ba2 100%) -> #667eea
    
    # Pattern: match linear-gradient, optional angle/direction, then the first color (hex code), optionally followed by a percentage, then the rest.
    pattern = re.compile(r'linear-gradient\([^,]+,\s*(#[0-9a-fA-F]{3,6})(?:\s+\d+%?)?[^)]*\)')
    
    new_content = pattern.sub(r'\1', content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {filepath}")

def main():
    src_dir = r"E:\landlock-system\landlock\frontend\src"
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.svelte') or file.endswith('.css'):
                process_file(os.path.join(root, file))

if __name__ == '__main__':
    main()
