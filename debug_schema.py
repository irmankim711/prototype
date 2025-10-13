#!/usr/bin/env python3
"""
Debug UserUpdateSchema validation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.validation.schemas import UserUpdateSchema

def test_schema():
    print("🧪 Testing UserUpdateSchema validation")
    
    schema = UserUpdateSchema()
    print("✅ Schema instantiated successfully")
    
    test_data = {
        "first_name": "Debug",
        "last_name": "User",
        "username": "debuguser_test",
        "phone": "+1-555-123-4567",  # Test phone validation
        "timezone": "UTC",
        "language": "en",
        "theme": "light",
        "email_notifications": True,
        "push_notifications": False
    }
    
    print(f"📤 Testing data: {test_data}")
    
    try:
        validated_data = schema.load(test_data)
        print(f"✅ Validation successful: {validated_data}")
    except Exception as e:
        import traceback
        print(f"❌ Validation failed: {str(e)}")
        print(f"📍 Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_schema()
