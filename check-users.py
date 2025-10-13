#!/usr/bin/env python3
"""
Check existing users in the database
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.production.user_models import User

def check_users():
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        print(f"📊 Found {len(users)} users in database:")
        
        for user in users:
            print(f"  - ID: {user.id}")
            print(f"    Email: {user.email}")
            print(f"    Firebase UID: {user.firebase_uid}")
            print(f"    Active: {user.is_active}")
            print(f"    Created: {user.created_at}")
            print()

if __name__ == "__main__":
    check_users()