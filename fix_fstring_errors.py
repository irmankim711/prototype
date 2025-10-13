#!/usr/bin/env python3
"""
Fix f-string syntax errors in production_routes.py
This script replaces all instances of \") with ") in f-strings
"""

import re

def fix_fstring_errors(file_path):
    """Fix f-string syntax errors in the given file"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count original issues
        original_count = content.count('\\\")')
        
        # Fix the f-string syntax errors
        # Replace \") with ") 
        fixed_content = content.replace('\\\")', '\")')
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        # Count remaining issues
        remaining_count = fixed_content.count('\\\")')
        
        print(f"Fixed {original_count - remaining_count} f-string syntax errors")
        print(f"Remaining issues: {remaining_count}")
        
        return True
        
    except Exception as e:
        print(f"Error fixing file: {e}")
        return False

if __name__ == "__main__":
    file_path = "backend/app/routes/production_routes.py"
    success = fix_fstring_errors(file_path)
    
    if success:
        print("F-string syntax errors fixed successfully!")
    else:
        print("Failed to fix f-string syntax errors")
