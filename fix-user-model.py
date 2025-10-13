#!/usr/bin/env python3
"""
Fix User model to work without firebase_uid column
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def fix_user_model():
    # Read the current user model
    user_model_path = 'backend/app/models/production/user_models.py'
    
    with open(user_model_path, 'r') as f:
        content = f.read()
    
    # Comment out the firebase_uid column temporarily
    content = content.replace(
        'firebase_uid = Column(String(255), unique=True, nullable=True)  # Firebase UID',
        '# firebase_uid = Column(String(255), unique=True, nullable=True)  # Firebase UID - Temporarily disabled'
    )
    
    # Write the updated content back
    with open(user_model_path, 'w') as f:
        f.write(content)
    
    print("✅ User model updated to work without firebase_uid column")

if __name__ == "__main__":
    fix_user_model()