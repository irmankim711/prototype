#!/usr/bin/env python3
"""
Verify AI Suggestions Fix
Confirms that the duplicate function issue has been resolved
"""

import ast
import re
from pathlib import Path

def check_nextgen_file():
    """Check the NextGen report builder file for issues"""
    print("🔍 Analyzing NextGen report builder file...")

    nextgen_file = Path("backend/app/routes/nextgen_report_builder.py")

    if not nextgen_file.exists():
        print("   ❌ NextGen file not found")
        return False

    with open(nextgen_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for duplicate function names
    function_pattern = r'def (get_ai_suggestions|get_ai_text_suggestions)\('
    functions = re.findall(function_pattern, content)

    print(f"   Functions found: {functions}")

    # Check for route registrations
    ai_routes = re.findall(r"@nextgen_bp\.route\('([^']*ai[^']*)'", content)
    print(f"   AI routes found: {ai_routes}")

    # Verify the fix
    has_ai_suggestions = '/ai/suggestions' in ai_routes
    has_text_suggestions = '/ai/text-suggestions' in ai_routes
    no_duplicate_functions = functions.count('get_ai_suggestions') <= 1

    if has_ai_suggestions and has_text_suggestions and no_duplicate_functions:
        print("   ✅ Function names and routes are properly separated")
        return True
    else:
        print("   ❌ Issues still present:")
        if not has_ai_suggestions:
            print("     - Missing /ai/suggestions route")
        if not has_text_suggestions:
            print("     - Missing /ai/text-suggestions route")
        if not no_duplicate_functions:
            print("     - Duplicate function names still exist")
        return False

def check_route_registration():
    """Check that NextGen routes are included in app registration"""
    print("🔍 Checking route registration in app.py...")

    app_file = Path("backend/app/__init__.py")

    if not app_file.exists():
        print("   ❌ App file not found")
        return False

    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for NextGen blueprint import and registration
    has_nextgen_import = 'from .routes.nextgen_report_builder import nextgen_bp' in content
    has_nextgen_registration = "app.register_blueprint(nextgen_bp, url_prefix='/api/v1/nextgen')" in content

    print(f"   NextGen import found: {has_nextgen_import}")
    print(f"   NextGen registration found: {has_nextgen_registration}")

    if has_nextgen_import and has_nextgen_registration:
        print("   ✅ NextGen blueprint properly registered")
        return True
    else:
        print("   ❌ NextGen blueprint registration issues")
        return False

def verify_route_structure():
    """Verify that the app can load routes without errors"""
    print("🔍 Verifying route structure...")

    try:
        # Test importing the NextGen blueprint
        import sys
        sys.path.append('backend')

        from app.routes.nextgen_report_builder import nextgen_bp

        print(f"   Blueprint name: {nextgen_bp.name}")
        print(f"   Blueprint has deferred functions: {len(nextgen_bp.deferred_functions)}")

        # Check registered routes
        routes = []
        for rule in nextgen_bp.url_map.iter_rules():
            routes.append(str(rule))

        ai_routes = [r for r in routes if 'ai' in r]
        print(f"   AI routes in blueprint: {ai_routes}")

        print("   ✅ NextGen blueprint loads successfully")
        return True

    except Exception as e:
        print(f"   ❌ Error loading NextGen blueprint: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🔧 AI Suggestions Fix Verification")
    print("=" * 50)

    checks = [
        ("NextGen File Analysis", check_nextgen_file),
        ("Route Registration Check", check_route_registration),
        ("Route Structure Verification", verify_route_structure),
    ]

    results = []

    for check_name, check_func in checks:
        print(f"\n🔍 Running: {check_name}")
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            results.append((check_name, False))

    print("\n" + "=" * 50)
    print("📊 Verification Results:")

    passed = 0
    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {check_name}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} checks passed")

    if passed == len(results):
        print("🎉 All checks passed! The AI suggestions fix is complete.")
        print("\n📋 Summary of changes:")
        print("   ✅ Renamed second function to 'get_ai_text_suggestions'")
        print("   ✅ Separated routes: /ai/suggestions and /ai/text-suggestions")
        print("   ✅ Added NextGen blueprint to fallback registration")
        print("   ✅ No more duplicate function conflicts")
        print("\n🚀 The frontend should now be able to call both endpoints successfully!")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")

if __name__ == "__main__":
    main()