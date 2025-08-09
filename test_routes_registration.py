#!/usr/bin/env python3
"""
Test script to verify Google Forms routes are properly registered
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app

def test_routes_registration():
    """Test that Google Forms routes are properly registered"""
    print("🔍 Testing Google Forms routes registration...")
    
    try:
        # Create the Flask app
        app = create_app()
        
        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        
        # Filter for Google Forms routes
        google_forms_routes = [
            route for route in routes 
            if '/google-forms' in route['path']
        ]
        
        print(f"✅ Found {len(google_forms_routes)} Google Forms routes:")
        for route in google_forms_routes:
            print(f"  - {route['path']} [{', '.join(method for method in route['methods'] if method not in ['HEAD', 'OPTIONS'])}]")
        
        # Check for specific expected routes
        expected_routes = [
            '/api/google-forms/status',
            '/api/google-forms/forms',
            '/api/google-forms/oauth/authorize',
            '/api/google-forms/oauth/callback'
        ]
        
        found_routes = [route['path'] for route in google_forms_routes]
        
        print(f"\n🔍 Checking for expected routes:")
        for expected in expected_routes:
            if any(expected in found for found in found_routes):
                print(f"  ✅ {expected} - Found")
            else:
                print(f"  ❌ {expected} - Missing")
        
        if google_forms_routes:
            print(f"\n🎉 Google Forms routes are properly registered!")
            return True
        else:
            print(f"\n❌ No Google Forms routes found. Check blueprint registration.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        return False

def main():
    """Main function"""
    print("Google Forms Routes Registration Test")
    print("=" * 40)
    
    success = test_routes_registration()
    
    if success:
        print("\n✅ Routes registration test passed!")
        print("💡 To start the server: cd backend && python app.py")
        print("🌐 Then test: http://localhost:5000/api/google-forms/status")
    else:
        print("\n❌ Routes registration test failed!")
        print("🔧 Check the blueprint import and registration in app/__init__.py")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
