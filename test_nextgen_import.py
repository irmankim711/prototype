#!/usr/bin/env python3
"""
Test script to check if NextGen report builder can be imported
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_nextgen_import():
    """Test importing the NextGen report builder"""
    try:
        print("🔍 Testing NextGen report builder import...")
        
        from app.routes.nextgen_report_builder import nextgen_bp
        print("✅ NextGen report builder import successful")
        
        # Check if the blueprint has routes
        routes = []
        for rule in nextgen_bp.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': str(rule)
            })
        
        print(f"📊 Found {len(routes)} routes:")
        for route in routes[:5]:  # Show first 5 routes
            print(f"  - {route['rule']} ({', '.join(route['methods'])})")
        
        if len(routes) > 5:
            print(f"  ... and {len(routes) - 5} more routes")
        
        return True
        
    except Exception as e:
        print(f"❌ NextGen report builder import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 NextGen Report Builder Import Test")
    print("=" * 50)
    
    success = test_nextgen_import()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Import test passed!")
    else:
        print("❌ Import test failed!")
    print("🏁 Test completed")
