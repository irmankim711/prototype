#!/usr/bin/env python3
"""
Quick test to validate the main 500 error fix
"""

import requests
import json

def test_public_forms_quick():
    """Quick test of the public forms endpoint fix"""
    try:
        response = requests.get("http://127.0.0.1:5000/api/forms/public")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            if isinstance(data, dict) and 'forms' in data:
                forms = data['forms']
                print(f"✅ SUCCESS: Found {len(forms)} public forms")
                print(f"Response structure: {list(data.keys())}")
                
                if forms:
                    print(f"Sample form keys: {list(forms[0].keys())}")
                    print(f"Sample form: {json.dumps(forms[0], indent=2)}")
                
                return True
            else:
                print(f"❌ Unexpected response structure: {data}")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Public Forms Endpoint Fix")
    print("=" * 40)
    success = test_public_forms_quick()
    
    if success:
        print("\n🎉 MAIN FIX CONFIRMED: Public forms endpoint working!")
        print("The 500 error has been resolved!")
    else:
        print("\n❌ Still have issues with the endpoint")
