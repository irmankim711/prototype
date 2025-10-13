#!/usr/bin/env python3
"""
Quick fix for escaped quotes in production_routes.py
"""

import re

def fix_escaped_quotes(file_path):
    """Fix escaped quotes in f-strings"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace f\" with f"
    fixed_content = re.sub(r'f\\"([^"]*)"', r'f"\1"', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed escaped quotes in {file_path}")

if __name__ == "__main__":
    fix_escaped_quotes("backend/app/routes/production_routes.py")
