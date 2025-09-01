#!/usr / bin / env python3
"""
Quick script to fix common linting issues automatically.
"""

import re
import os
import sys
import subprocess

def fix_arithmetic_operators(file_path):
    """Fix missing whitespace around arithmetic operators."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix arithmetic operators with missing spaces
    patterns = [
        (r'(\w)(\+)(\w)', r'\1 \2 \3'),  # word + word -> word + word
        (r'(\w)(\-)(\w)', r'\1 \2 \3'),  # word - word -> word - word  
        (r'(\w)(\*)(\w)', r'\1 \2 \3'),  # word * word -> word * word
        (r'(\w)(/)(\w)', r'\1 \2 \3'),   # word / word -> word / word
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed arithmetic operators in {file_path}")

def fix_f_strings(file_path):
    """Fix f - strings with missing placeholders."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    modified = False
    for i, line in enumerate(lines):
        # Find f - strings without placeholders
        if "'" in line or '"' in line:
            # Simple check - if f - string has no { } brackets, convert to regular string
            f_match = re.search(r'f(["\'])(.*?)\1', line)
            if f_match and '{' not in f_match.group(2):
                # Convert 'string' to 'string'
                new_line = line.replace("'", "'").replace('"', '"')
                if new_line != line:
                    lines[i] = new_line
                    modified = True
    
    if modified:
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print(f"Fixed f - strings in {file_path}")

def fix_specific_files():
    """Fix issues in specific files mentioned in flake8 output."""
    
    # Fix run_tests.py arithmetic operators
    run_tests_fixes = [
        ('run_tests.py', 26, 'passed + failed', 'passed + failed'),
        ('run_tests.py', 29, 'passed + failed', 'passed + failed'),
        ('run_tests.py', 129, 'passed + failed', 'passed + failed'),
        ('run_tests.py', 131, 'passed + failed', 'passed + failed'),
        ('run_tests.py', 136, 'passed + failed', 'passed + failed'),
        ('run_tests.py', 136, 'skipped + errors', 'skipped + errors'),
    ]
    
    for file_name, line_num, old, new in run_tests_fixes:
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                lines = f.readlines()
            
            if line_num <= len(lines):
                if old in lines[line_num - 1]:
                    lines[line_num - 1] = lines[line_num - 1].replace(old, new)
                    with open(file_name, 'w') as f:
                        f.writelines(lines)
                    print(f"Fixed arithmetic in {file_name} line {line_num}")

def main():
    """Main function to run fixes."""
    
    # Get Python files to process
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment and other directories
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', '.git', 'migrations']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Processing {len(python_files)} Python files...")
    
    # Apply fixes
    for file_path in python_files:
        try:
            fix_arithmetic_operators(file_path)
            fix_f_strings(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Apply specific fixes
    fix_specific_files()
    
    print("Linting fixes completed!")

if __name__ == '__main__':
    main()
