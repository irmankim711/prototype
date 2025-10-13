#!/usr/bin/env python3
"""
Check what routes are actually registered in the Flask app
"""
import requests
import json

def main():
    try:
        response = requests.get("http://localhost:5000/__dev/routes")
        if response.status_code == 200:
            data = response.json()
            routes = data.get('routes', [])
            
            print(f"📊 Total routes registered: {data.get('count', 0)}")
            print("\n🔍 Looking for NextGen routes:")
            
            nextgen_routes = [r for r in routes if 'nextgen' in r['rule'].lower()]
            
            if nextgen_routes:
                print(f"✅ Found {len(nextgen_routes)} NextGen routes:")
                for route in nextgen_routes:
                    print(f"   {route['rule']} -> {route['methods']}")
            else:
                print("❌ No NextGen routes found!")
                
            print("\n🔍 Looking for /api/v1/ routes:")
            api_v1_routes = [r for r in routes if '/api/v1/' in r['rule']]
            
            if api_v1_routes:
                print(f"✅ Found {len(api_v1_routes)} /api/v1/ routes:")
                for route in api_v1_routes:
                    print(f"   {route['rule']} -> {route['methods']}")
            else:
                print("❌ No /api/v1/ routes found!")
                
            print("\n🔍 All registered route patterns:")
            unique_prefixes = set()
            for route in routes:
                rule = route['rule']
                if rule.startswith('/api/'):
                    parts = rule.split('/')
                    if len(parts) >= 3:
                        prefix = '/'.join(parts[:3])
                        unique_prefixes.add(prefix)
                        
            for prefix in sorted(unique_prefixes):
                count = len([r for r in routes if r['rule'].startswith(prefix)])
                print(f"   {prefix}/* -> {count} routes")
                
        else:
            print(f"❌ Failed to get routes: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()