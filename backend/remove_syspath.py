#!/usr/bin/env python3
"""
ABOUTME: Script to remove sys.path.insert() statements from all Python files.
ABOUTME: Part of Issue #8 - proper Python packaging implementation.
"""
import os
import re
from pathlib import Path

def remove_syspath_insert(file_path: Path) -> bool:
    """Remove sys.path.insert statements from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        i = 0
        modified = False
        
        while i < len(lines):
            line = lines[i]
            
            # Skip sys.path.insert lines
            if 'sys.path.insert' in line:
                modified = True
                i += 1
                continue
            
            # Skip 'import sys' if followed by sys.path.insert
            if 'import sys' in line and not 'import' in line.replace('import sys', ''):
                # Check if next non-empty line has sys.path.insert
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                
                if j < len(lines) and 'sys.path.insert' in lines[j]:
                    # Skip the import sys line, skip empty lines, will skip sys.path.insert on next iteration
                    modified = True
                    while i < j:
                        i += 1
                    continue
            
            # Skip 'import os' if only used for sys.path.insert
            if re.match(r'^\s*import os\s*$', line):
                # Check if os is used elsewhere in the file
                remaining = ''.join(lines[i+1:])
                if 'os.' not in remaining and 'import os' in line:
                    # Check if next lines are sys-related
                    j = i + 1
                    while j < len(lines) and (lines[j].strip() == '' or 'sys' in lines[j]):
                        j += 1
                    if j > i + 1:
                        # Likely only for path manipulation, skip it
                        i += 1
                        continue
            
            new_lines.append(line)
            i += 1
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all Python files in backend directory."""
    backend_dir = Path(__file__).parent
    
    count = 0
    modified = 0
    
    for py_file in backend_dir.rglob('*.py'):
        # Skip this script and virtual environments
        if 'venv' in str(py_file) or 'remove_syspath.py' in str(py_file):
            continue
        
        count += 1
        if remove_syspath_insert(py_file):
            modified += 1
            print(f"✓ Modified: {py_file.relative_to(backend_dir)}")
    
    print(f"\nProcessed {count} files, modified {modified} files")

if __name__ == '__main__':
    main()

