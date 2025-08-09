#!/usr/bin/env python3
"""
JWT Identity Resolution Test Script
Tests JWT token creation, validation, and user lookup functionality.
"""

import requests
import json
from app import create_app
from app.models import User, db
from flask_jwt_extended import create_access_token, decode_token

def test_jwt_configuration():
    """Test JWT configuration is properly set up"""
    print("=== JWT CONFIGURATION TEST ===\n")
    
    app = create_app()
    
    with app.app_context():
        # Test JWT configuration
        config_items = [
            'JWT_SECRET_KEY',
            'JWT_ACCESS_TOKEN_EXPIRES', 
            'JWT_REFRESH_TOKEN_EXPIRES',
            'JWT_ALGORITHM',
            'JWT_TOKEN_LOCATION'
        ]
        
        print("🔐 JWT Configuration:")
        for item in config_items:
            value = app.config.get(item)
            print(f"  {item}: {value}")
        
        # Test user identity loader
        print(f"\n🔍 Testing Identity Functions:")
        try:
            # Test with mock user object
            class MockUser:
                def __init__(self, id):
                    self.id = id
            
            mock_user = MockUser(123)
            identity = app.jwt_manager._user_identity_callback(mock_user)
            print(f"  User object -> Identity: {identity}")
            
            # Test with string
            identity_str = app.jwt_manager._user_identity_callback("456")
            print(f"  String -> Identity: {identity_str}")
            
            # Test with bypass user
            bypass_identity = app.jwt_manager._user_identity_callback("bypass-user")
            print(f"  Bypass user -> Identity: {bypass_identity}")
            
        except Exception as e:
            print(f"  ❌ Identity function error: {e}")

def test_token_creation_and_validation():
    """Test token creation and validation process"""
    print(f"\n=== TOKEN CREATION & VALIDATION TEST ===\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test token creation with different identity types
            print("🎟️  Testing Token Creation:")
            
            # Test with string ID
            token1 = create_access_token(identity="123")
            print(f"  String identity token: {token1[:50]}...")
            
            # Test with integer ID
            token2 = create_access_token(identity=456)
            print(f"  Integer identity token: {token2[:50]}...")
            
            # Test token decoding
            print(f"\n🔍 Testing Token Decoding:")
            decoded1 = decode_token(token1)
            print(f"  Token 1 payload: {decoded1}")
            
            decoded2 = decode_token(token2)
            print(f"  Token 2 payload: {decoded2}")
            
            print(f"\n✅ Token creation and validation successful!")
            
        except Exception as e:
            print(f"❌ Token creation/validation error: {e}")

def test_user_lookup_functionality():
    """Test user lookup from JWT tokens"""
    print(f"\n=== USER LOOKUP TEST ===\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we have any users in the database
            user_count = User.query.count()
            print(f"👥 Users in database: {user_count}")
            
            if user_count > 0:
                # Get first user
                user = User.query.first()
                print(f"  Test user: ID={user.id}, Email={user.email}")
                
                # Create token for this user
                token = create_access_token(identity=str(user.id))
                print(f"  Created token for user {user.id}")
                
                # Test user lookup callback
                mock_jwt_header = {}
                mock_jwt_data = {"sub": str(user.id)}
                
                looked_up_user = app.jwt_manager._user_lookup_callback(mock_jwt_header, mock_jwt_data)
                if looked_up_user:
                    print(f"  ✅ User lookup successful: {looked_up_user.email}")
                else:
                    print(f"  ❌ User lookup failed")
            else:
                print("  ⚠️  No users in database to test with")
                
        except Exception as e:
            print(f"❌ User lookup test error: {e}")

def test_live_endpoints_with_auth():
    """Test authentication endpoints if server is running"""
    print(f"\n=== LIVE AUTHENTICATION TEST ===\n")
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints_to_test = [
        ("/health", "GET", None),
        ("/api/auth/me", "GET", None),  # This should return 401 without token
        ("/api/dashboard/stats", "GET", None)  # This should return 401 without token
    ]
    
    print("🌐 Testing authentication endpoints:")
    for endpoint, method, headers in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers or {}, timeout=5)
            elif method == "POST":
                response = requests.post(f"{base_url}{endpoint}", headers=headers or {}, timeout=5)
            
            status_color = "✅" if response.status_code in [200, 401] else "❌"
            print(f"  {endpoint:30} {status_color} {response.status_code}")
            
            # For auth endpoints, show the response message
            if "auth" in endpoint or "dashboard" in endpoint:
                try:
                    resp_json = response.json()
                    if 'msg' in resp_json:
                        print(f"    Message: {resp_json['msg']}")
                except:
                    pass
                    
        except requests.ConnectionError:
            print(f"  {endpoint:30} 🔌 CONNECTION FAILED (server not running?)")
        except Exception as e:
            print(f"  {endpoint:30} ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_jwt_configuration()
    test_token_creation_and_validation() 
    test_user_lookup_functionality()
    test_live_endpoints_with_auth()
