#!/usr/bin/env python3
"""
Quick fix script to replace get_jwt_identity() with get_current_user_id()
"""

import os
import re

def fix_jwt_identity_calls():
    backend_path = r"C:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\routes"
    
    for filename in os.listdir(backend_path):
        if filename.endswith('.py'):
            filepath = os.path.join(backend_path, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace get_jwt_identity() with get_current_user_id()
            original_content = content
            content = re.sub(r'user_id = get_jwt_identity\(\)', 'user_id = get_current_user_id()', content)
            
            # Add import if needed and not already present
            if 'get_current_user_id' in content and 'from ..decorators import' in content:
                # Update existing import
                content = re.sub(
                    r'from \.\.decorators import ([^,\n]+)',
                    r'from ..decorators import \1, get_current_user_id',
                    content
                )
            elif 'get_current_user_id' in content and 'from ..decorators import' not in content:
                # Add new import
                import_line = 'from ..decorators import get_current_user_id\n'
                # Find a good place to insert the import
                if 'from flask_jwt_extended import' in content:
                    content = content.replace(
                        'from flask_jwt_extended import jwt_required, get_jwt_identity',
                        'from flask_jwt_extended import jwt_required\n' + import_line.strip()
                    )
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated {filename}")
            else:
                print(f"⚪ No changes needed in {filename}")

if __name__ == "__main__":
    print("🔧 Fixing JWT identity calls...")
    fix_jwt_identity_calls()
    print("🎉 Done!")
