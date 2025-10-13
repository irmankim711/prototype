#!/usr/bin/env python3
"""
API Routes Debugger for ENDPOINT_NOT_FOUND Issues

This script helps debug API routing issues by:
1. Listing all registered routes in your Flask app
2. Comparing frontend calls with backend routes
3. Identifying missing or mismatched endpoints

Usage:
    python debug_api_routes.py
"""

import sys
import os
import json
from typing import Dict, List, Set

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def analyze_routes():
    """Analyze and compare frontend vs backend routes."""

    print("🔍 API ROUTES DEBUGGER")
    print("=" * 50)

    # Backend routes analysis
    print("\n📋 BACKEND ROUTES ANALYSIS:")
    print("-" * 30)

    backend_routes = get_backend_routes()
    print(f"Found {len(backend_routes)} route patterns")

    for prefix, routes in backend_routes.items():
        print(f"\n🔹 Prefix: {prefix}")
        for route in routes:
            print(f"   {route['methods']} {route['path']}")

    # Frontend routes analysis
    print("\n📱 FRONTEND ROUTES ANALYSIS:")
    print("-" * 30)

    frontend_calls = get_frontend_api_calls()
    print(f"Found {len(frontend_calls)} API call patterns")

    for call in frontend_calls:
        print(f"   {call['method']} {call['endpoint']}")

    # Route comparison
    print("\n⚖️  ROUTE COMPARISON:")
    print("-" * 25)

    issues = compare_routes(backend_routes, frontend_calls)

    if issues['missing_routes']:
        print("\n❌ MISSING BACKEND ROUTES:")
        for missing in issues['missing_routes']:
            print(f"   Frontend calls: {missing['method']} {missing['endpoint']}")
            print(f"   But backend has no matching route!")

    if issues['route_mismatches']:
        print("\n⚠️  ROUTE METHOD MISMATCHES:")
        for mismatch in issues['route_mismatches']:
            print(f"   Frontend: {mismatch['frontend_method']} {mismatch['endpoint']}")
            print(f"   Backend:  {mismatch['backend_methods']} {mismatch['endpoint']}")

    if not issues['missing_routes'] and not issues['route_mismatches']:
        print("✅ All frontend calls have matching backend routes!")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 20)

    if issues['missing_routes']:
        print("1. Add missing routes to your backend")
        print("2. Check blueprint registration in __init__.py")
        print("3. Verify URL prefixes are correct")

    if issues['route_mismatches']:
        print("1. Fix HTTP method mismatches")
        print("2. Ensure frontend uses correct HTTP verbs")

    print("3. Run your backend server and check logs")
    print("4. Use browser DevTools Network tab to inspect actual requests")

def get_backend_routes() -> Dict[str, List[Dict]]:
    """Extract routes from backend code without running the app."""
    routes = {}

    # Common route files to check
    route_files = [
        'backend/app/routes/reports_api.py',
        'backend/app/routes/api.py',
        'backend/app/routes/nextgen_report_builder.py',
        'backend/app/routes/enhanced_reports_api.py',
        'backend/app/__init__.py'  # For blueprint registration
    ]

    for file_path in route_files:
        if os.path.exists(file_path):
            try:
                routes.update(parse_route_file(file_path))
            except Exception as e:
                print(f"⚠️  Error parsing {file_path}: {e}")

    return routes

def parse_route_file(file_path: str) -> Dict[str, List[Dict]]:
    """Parse a route file to extract route definitions."""
    routes = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract blueprint prefix
    import re
    prefix_match = re.search(r'Blueprint\([^,]+,\s*[^,]*,\s*url_prefix\s*=\s*[\'"]([^\'"]*)[\'"]', content)
    if prefix_match:
        prefix = prefix_match.group(1)
    else:
        prefix = ""

    # Extract route definitions
    route_pattern = r'@(\w+_bp|app)\.route\([\'"]([^\'"]*)[\'"],?\s*methods\s*=\s*\[([^\]]*)\]'
    matches = re.findall(route_pattern, content, re.MULTILINE | re.DOTALL)

    route_list = []
    for blueprint, path, methods in matches:
        # Clean up methods
        method_list = [m.strip().strip('"\'') for m in methods.split(',')]

        route_list.append({
            'path': path,
            'methods': method_list,
            'full_path': f"{prefix}{path}" if prefix else path
        })

    if route_list:
        routes[prefix or "root"] = route_list

    return routes

def get_frontend_api_calls() -> List[Dict]:
    """Extract API calls from frontend code."""
    calls = []

    frontend_files = [
        'frontend/src/services/reportService.ts',
        'frontend/src/services/nextGenReportService.ts',
        'frontend/src/components/ReportPreviewEdit.tsx',
        'frontend/src/components/DocumentPreview.tsx'
    ]

    for file_path in frontend_files:
        if os.path.exists(file_path):
            try:
                calls.extend(parse_frontend_file(file_path))
            except Exception as e:
                print(f"⚠️  Error parsing {file_path}: {e}")

    return calls

def parse_frontend_file(file_path: str) -> List[Dict]:
    """Parse frontend file to extract API calls."""
    calls = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract axios calls
    import re

    # axios.get/post/put/delete calls
    patterns = [
        (r'axios\.get\([\'"`]([^\'"`]+)[\'"`]', 'GET'),
        (r'axios\.post\([\'"`]([^\'"`]+)[\'"`]', 'POST'),
        (r'axios\.put\([\'"`]([^\'"`]+)[\'"`]', 'PUT'),
        (r'axios\.delete\([\'"`]([^\'"`]+)[\'"`]', 'DELETE'),
        (r'fetch\([\'"`]([^\'"`]+)[\'"`]', 'GET'),  # fetch calls
    ]

    for pattern, method in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # Clean up the URL
            url = match.strip()
            if url.startswith('${API_BASE_URL}'):
                url = url.replace('${API_BASE_URL}', '')
            elif url.startswith('http://localhost:5000'):
                url = url.replace('http://localhost:5000', '')

            calls.append({
                'method': method,
                'endpoint': url,
                'file': file_path
            })

    return calls

def compare_routes(backend_routes: Dict[str, List[Dict]], frontend_calls: List[Dict]) -> Dict:
    """Compare frontend calls with backend routes."""
    issues = {
        'missing_routes': [],
        'route_mismatches': []
    }

    # Create a set of backend route patterns
    backend_patterns = set()
    backend_methods = {}  # endpoint -> methods

    for prefix, routes in backend_routes.items():
        for route in routes:
            backend_patterns.add(route['full_path'])
            backend_methods[route['full_path']] = route['methods']

    # Check each frontend call
    for call in frontend_calls:
        endpoint = call['endpoint']
        method = call['method']

        if endpoint not in backend_patterns:
            issues['missing_routes'].append(call)
        elif method not in backend_methods.get(endpoint, []):
            issues['route_mismatches'].append({
                'endpoint': endpoint,
                'frontend_method': method,
                'backend_methods': backend_methods.get(endpoint, [])
            })

    return issues

def main():
    """Main entry point."""
    try:
        analyze_routes()
    except Exception as e:
        print(f"❌ Error running route analysis: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're in the project root directory")
        print("2. Ensure Python can find the backend modules")
        print("3. Check that all required dependencies are installed")

if __name__ == "__main__":
    main()
