#!/usr/bin/env python3
"""
Test script to debug import issues
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    print("Testing imports...")
    from app import create_app
    print("✅ create_app imported successfully")
    
    app = create_app()
    print("✅ App created successfully")
    
    with app.app_context():
        from app.models import User, Report
        print("✅ Models imported successfully")
        
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {list(rule.methods)} {rule.rule}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
