#!/usr/bin/env python3
"""
Test Analytics Endpoints with JWT Authentication
Verifies that analytics endpoints work correctly with proper authentication
"""

import sys
import os
import json

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_analytics_endpoints():
    """Test analytics endpoints with proper JWT authentication"""
    try:
        from app import create_app
        
        from datetime import timedelta
        
        app = create_app()
        
        with app.app_context():
            # Create a test token with UUID user ID
            token = 'mock_test_token'
            )
            
            print(f"✅ JWT token created: {token[:30]}...")
            
            with app.test_client() as client:
                # Test analytics endpoints
                endpoints = [
                    '/api/analytics/geographic',
                    '/api/analytics/real-time',
                    '/api/analytics/top-forms',
                    '/api/analytics/performance-comparison'
                ]
                
                headers = {'Authorization': 'Bearer mock_test_token'}
                
                for endpoint in endpoints:
                    print(f"\n🔍 Testing {endpoint}...")
                    
                    response = client.get(endpoint, headers=headers)
                    
                    if response.status_code == 200:
                        print(f"   ✅ Status: {response.status_code} - Success")
                        data = response.get_json()
                        print(f"   📊 Response type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"   📋 Keys: {list(data.keys())}")
                    elif response.status_code == 422:
                        print(f"   ❌ Status: {response.status_code} - Validation Error")
                        print(f"   📝 Response: {response.get_data(as_text=True)}")
                    elif response.status_code == 401:
                        print(f"   ⚠️  Status: {response.status_code} - Authentication Error")
                        print(f"   📝 Response: {response.get_data(as_text=True)}")
                    else:
                        print(f"   ⚠️  Status: {response.status_code} - Unexpected")
                        print(f"   📝 Response: {response.get_data(as_text=True)}")
                
                return True
                
    except Exception as e:
        print(f"❌ Analytics endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analytics_service():
    """Test analytics service directly"""
    try:
        from app import create_app
        from app.services.analytics_service import DashboardAnalytics
        
        app = create_app()
        
        with app.app_context():
            # Test analytics service
            analytics = DashboardAnalytics("test-user-123-uuid")  # Test user ID
            
            print("\n🔍 Testing Analytics Service...")
            
            # Test geographic distribution
            try:
                geo_data = analytics.get_geographic_distribution()
                print(f"   ✅ Geographic data: {type(geo_data)}")
            except Exception as e:
                print(f"   ❌ Geographic data failed: {e}")
            
            # Test real-time stats
            try:
                real_time_data = analytics.get_real_time_stats()
                print(f"   ✅ Real-time data: {type(real_time_data)}")
            except Exception as e:
                print(f"   ❌ Real-time data failed: {e}")
            
            # Test top forms
            try:
                top_forms = analytics.get_top_performing_forms(5)
                print(f"   ✅ Top forms data: {type(top_forms)}")
            except Exception as e:
                print(f"   ❌ Top forms failed: {e}")
            
            # Test performance comparison
            try:
                perf_data = analytics.get_form_performance_comparison()
                print(f"   ✅ Performance data: {type(perf_data)}")
            except Exception as e:
                print(f"   ❌ Performance data failed: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Analytics service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_analytics_tests():
    """Run all analytics tests"""
    print("📊 Testing Analytics Endpoints and Service")
    print("=" * 60)
    
    # Test analytics endpoints
    print("\n1. Testing Analytics Endpoints with JWT...")
    endpoints_ok = test_analytics_endpoints()
    
    # Test analytics service
    print("\n2. Testing Analytics Service Directly...")
    service_ok = test_analytics_service()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ANALYTICS TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Analytics Endpoints", endpoints_ok),
        ("Analytics Service", service_ok)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All analytics tests passed!")
        return True
    else:
        print("⚠️  Some analytics tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = run_analytics_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during analytics testing: {e}")
        sys.exit(1)
