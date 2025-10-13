#!/usr/bin/env python3
"""
Test script for Data Sources Infrastructure (Task 1)

Tests the core data source services infrastructure including:
- Service registration and dependency injection
- DataSourceManager functionality
- Base service interface compliance
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.data_sources.factory import create_data_source_manager, get_data_source_manager
from app.services.data_sources.manager import DataSourceManager
from app.services.data_sources.excel_service import ExcelDataService
from app.services.data_sources.forms_service import FormsDataService
from app.services.data_sources.google_forms_service import GoogleFormsDataService


def test_service_creation():
    """Test that all services can be created"""
    print("Testing service creation...")
    
    try:
        excel_service = ExcelDataService()
        print(f"✅ Excel service created: {excel_service.service_name}")
        
        forms_service = FormsDataService()
        print(f"✅ Forms service created: {forms_service.service_name}")
        
        google_service = GoogleFormsDataService()
        print(f"✅ Google Forms service created: {google_service.service_name}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating services: {str(e)}")
        return False


def test_manager_creation():
    """Test DataSourceManager creation and service registration"""
    print("\nTesting manager creation...")
    
    try:
        manager = create_data_source_manager()
        print(f"✅ Manager created with {len(manager.get_available_services())} services")
        
        services = manager.get_available_services()
        expected_services = ['excel_data_service', 'forms_data_service', 'google_forms_data_service']
        
        for expected in expected_services:
            if expected in services:
                print(f"✅ Service registered: {expected}")
            else:
                print(f"❌ Service missing: {expected}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error creating manager: {str(e)}")
        return False


def test_service_routing():
    """Test that manager can route requests to appropriate services"""
    print("\nTesting service routing...")
    
    try:
        manager = create_data_source_manager()
        
        # Test Excel service routing
        excel_service = manager.get_service_for_source('excel-upload')
        if excel_service and excel_service.service_name == 'excel_data_service':
            print("✅ Excel service routing works")
        else:
            print("❌ Excel service routing failed")
            return False
        
        # Test Forms service routing
        forms_service = manager.get_service_for_source('form_123')
        if forms_service and forms_service.service_name == 'forms_data_service':
            print("✅ Forms service routing works")
        else:
            print("❌ Forms service routing failed")
            return False
        
        # Test Google Forms service routing
        google_service = manager.get_service_for_source('google-forms')
        if google_service and google_service.service_name == 'google_forms_data_service':
            print("✅ Google Forms service routing works")
        else:
            print("❌ Google Forms service routing failed")
            return False
        
        # Test unknown source
        unknown_service = manager.get_service_for_source('unknown-source')
        if unknown_service is None:
            print("✅ Unknown source correctly returns None")
        else:
            print("❌ Unknown source should return None")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing service routing: {str(e)}")
        return False


def test_error_responses():
    """Test that services return proper error responses for unimplemented methods"""
    print("\nTesting error responses...")
    
    try:
        manager = create_data_source_manager()
        
        # Test Excel service error response
        response = manager.get_data('excel-upload')
        if not response.success and response.error and response.error['code'] == 'NOT_IMPLEMENTED':
            print("✅ Excel service returns proper error response")
        else:
            print("❌ Excel service error response incorrect")
            return False
        
        # Test Forms service error response
        response = manager.get_fields('form_123')
        if not response.success and response.error and response.error['code'] == 'NOT_IMPLEMENTED':
            print("✅ Forms service returns proper error response")
        else:
            print("❌ Forms service error response incorrect")
            return False
        
        # Test unknown source error
        response = manager.get_data('unknown-source')
        if not response.success and response.error and response.error['code'] == 'DATA_SOURCE_NOT_FOUND':
            print("✅ Unknown source returns proper error response")
        else:
            print("❌ Unknown source error response incorrect")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing error responses: {str(e)}")
        return False


def test_singleton_pattern():
    """Test that get_data_source_manager returns the same instance"""
    print("\nTesting singleton pattern...")
    
    try:
        manager1 = get_data_source_manager()
        manager2 = get_data_source_manager()
        
        if manager1 is manager2:
            print("✅ Singleton pattern works correctly")
            return True
        else:
            print("❌ Singleton pattern failed - different instances returned")
            return False
    except Exception as e:
        print(f"❌ Error testing singleton pattern: {str(e)}")
        return False


def main():
    """Run all infrastructure tests"""
    print("🧪 Testing NextGen Data Sources Infrastructure (Task 1)")
    print("=" * 60)
    
    tests = [
        test_service_creation,
        test_manager_creation,
        test_service_routing,
        test_error_responses,
        test_singleton_pattern
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All infrastructure tests passed! Task 1 is complete.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)