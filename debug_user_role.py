#!/usr/bin/env python3
"""
Debug user role issue
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.models import User

def debug_user():
    app = create_app()
    with app.app_context():
        print("Testing user query...")
        
        # Get user 2 (the one from the JWT token)
        user = User.query.get(2)
        if user:
            print(f"User found: {user}")
            print(f"User email: {user.email}")
            print(f"Has role attr: {hasattr(user, 'role')}")
            if hasattr(user, 'role'):
                print(f"Role value: {user.role}")
                print(f"Type of role: {type(user.role)}")
            else:
                print("No role attribute found!")
                print(f"User attributes: {dir(user)}")
        else:
            print("User 2 not found")
            
        # List all users
        all_users = User.query.all()
        print(f"\nAll users in database: {len(all_users)}")
        for u in all_users:
            print(f"  User {u.id} ({u.email}): has role = {hasattr(u, 'role')}")

if __name__ == "__main__":
    debug_user()