#!/usr/bin/env python3
"""
Route Registration Test Script
Tests all Flask routes to ensure they're properly registered and accessible.
"""

from app import create_app
import requests
import json
from flask import url_for

def test_route_registration():
    """Test that all routes are properly registered"""
    app = create_app()
    
    print("=== FLASK ROUTE REGISTRATION TEST ===\n")
    
    # List all registered routes
    with app.app_context():
        print("📋 REGISTERED ROUTES:")
        print("-" * 50)
        
        routes_by_prefix = {}
        
        for rule in app.url_map.iter_rules():
            endpoint = rule.endpoint
            methods = ', '.join(sorted((rule.methods or set()) - {'HEAD', 'OPTIONS'}))
            url = rule.rule
            
            # Group by URL prefix
            prefix = url.split('/')[1] if len(url.split('/')) > 1 else 'root'
            if prefix not in routes_by_prefix:
                routes_by_prefix[prefix] = []
            
            routes_by_prefix[prefix].append({
                'url': url,
                'methods': methods,
                'endpoint': endpoint
            })
        
        # Display routes organized by prefix
        for prefix, routes in sorted(routes_by_prefix.items()):
            print(f"\n🔗 /{prefix}/ routes:")
            for route in sorted(routes, key=lambda x: x['url']):
                print(f"  {route['methods']:15} {route['url']:40} -> {route['endpoint']}")
        
        print(f"\n📊 SUMMARY:")
        print(f"Total routes registered: {len(list(app.url_map.iter_rules()))}")
        print(f"Route prefixes: {', '.join(sorted(routes_by_prefix.keys()))}")
        
        # Check critical routes
        critical_routes = [
            '/api/dashboard/stats',
            '/api/dashboard/charts', 
            '/api/dashboard/summary',
            '/api/auth/login',
            '/api/auth/refresh',
            '/api/forms/',
            '/api/reports',
            '/health'
        ]
        
        print(f"\n🔍 CRITICAL ROUTE CHECK:")
        print("-" * 30)
        
        registered_urls = [rule.rule for rule in app.url_map.iter_rules()]
        
        for route in critical_routes:
            status = "✅ FOUND" if route in registered_urls else "❌ MISSING"
            print(f"  {route:30} {status}")
        
        # Check for duplicate routes
        url_counts = {}
        for rule in app.url_map.iter_rules():
            url = rule.rule
            if url in url_counts:
                url_counts[url] += 1
            else:
                url_counts[url] = 1
        
        duplicates = {url: count for url, count in url_counts.items() if count > 1}
        if duplicates:
            print(f"\n⚠️  DUPLICATE ROUTES DETECTED:")
            for url, count in duplicates.items():
                print(f"  {url}: {count} registrations")
        else:
            print(f"\n✅ No duplicate routes detected")

def test_live_endpoints():
    """Test live endpoints if server is running"""
    print(f"\n=== LIVE ENDPOINT TEST ===\n")
    
    base_url = "http://localhost:5000"
    
    # Test endpoints that should be publicly accessible
    public_endpoints = [
        "/health",
        "/api/public/forms",
        "/api/forms/field-types"
    ]
    
    print("🌐 Testing public endpoints:")
    for endpoint in public_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = f"✅ {response.status_code}" if response.status_code < 400 else f"❌ {response.status_code}"
            print(f"  {endpoint:30} {status}")
        except requests.ConnectionError:
            print(f"  {endpoint:30} 🔌 CONNECTION FAILED (server not running?)")
        except Exception as e:
            print(f"  {endpoint:30} ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_route_registration()
    test_live_endpoints()
