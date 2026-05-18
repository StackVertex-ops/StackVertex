#!/usr/bin/env python3
"""
Fix B904: Add 'from e' or 'from None' to all raise HTTPException in except blocks
"""
import re
import sys
from pathlib import Path

def fix_exception_handling(file_path):
    """Fix exception handling in a single file."""
    content = file_path.read_text()
    original = content

    # Pattern: raise HTTPException(...) am Ende eines except-Blocks (ohne 'from')
    # Suche nach: raise HTTPException... OHNE 'from e' oder 'from None' danach
    pattern = r'(raise HTTPException\([^)]+\))(\s*(?!from\s))'

    # Ersetze durch: raise HTTPException(...) from e
    # Aber nur wenn wir in einem except-Block mit 'as e' sind

    lines = content.split('\n')
    fixed_lines = []
    in_except_block = False
    except_var = None
    indent_level = 0

    for i, line in enumerate(lines):
        # Check if we're entering an except block
        except_match = re.search(r'except\s+\w+(?:\s+as\s+(\w+))?:', line)
        if except_match:
            in_except_block = True
            except_var = except_match.group(1)  # Variable name (e, err, error, etc.) or None
            indent_level = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue

        # Check if we're leaving the except block (dedent)
        if in_except_block and line.strip() and not line.startswith(' ' * (indent_level + 1)):
            in_except_block = False
            except_var = None

        # Fix raise HTTPException if in except block
        if in_except_block and 'raise HTTPException' in line and 'from' not in line:
            # Add 'from e' or 'from None' at the end
            if except_var:
                line = line.rstrip() + f' from {except_var}'
            else:
                line = line.rstrip() + ' from None'

        fixed_lines.append(line)

    fixed_content = '\n'.join(fixed_lines)

    if fixed_content != original:
        file_path.write_text(fixed_content)
        return True
    return False

def main():
    """Fix all Python files in app/api/"""
    api_dir = Path('app/api')
    if not api_dir.exists():
        print("Error: app/api/ directory not found")
        sys.exit(1)

    fixed_count = 0
    for py_file in api_dir.glob('*.py'):
        if py_file.name.startswith('_'):
            continue

        print(f"Processing {py_file}...")
        if fix_exception_handling(py_file):
            fixed_count += 1
            print(f"  ✅ Fixed {py_file}")
        else:
            print(f"  ⏭️  No changes needed")

    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
