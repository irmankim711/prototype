#!/usr/bin/env python3
"""
Script to fix authentication issues in forms.py
This script will add proper null checks for user authentication
"""

import re

def fix_forms_auth():
    file_path = r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\routes\forms.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find function definitions that use get_current_user()
    # but don't check for None
    functions_to_fix = [
        'update_form',
        'delete_form', 
        'submit_form',
        'get_form_submissions',
        'update_form_qr_code',
        'create_form_duplicate'
    ]
    
    for func_name in functions_to_fix:
        # Pattern to find the function and add null check after get_current_user()
        pattern = f"(def {func_name}.*?\\n.*?try:\\n.*?user = get_current_user\\(\\))"
        replacement = f"\\1\\n        if not user:\\n            return jsonify({{'error': 'User not found'}}), 401"
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Authentication fixes applied to forms.py")

if __name__ == "__main__":
    fix_forms_auth()
