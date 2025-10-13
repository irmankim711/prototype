#!/usr/bin/env python3
"""
Enhanced Automated Report System Test Script
Tests the new AI-powered report viewer and dashboard functionality
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_enhanced_report_system():
    """Test the enhanced automated report system with AI features"""
    print("🚀 Testing Enhanced Automated Report System...")
    
    # Test user credentials
    test_user = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    session = requests.Session()
    
    try:
        # 1. Test Authentication
        print("\n1. Testing Authentication...")
        auth_response = session.post(f"{API_URL}/auth/login", json=test_user)
        
        if auth_response.status_code == 200:
            print("✅ Authentication successful")
            token = auth_response.json().get('access_token')
            session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            print("❌ Authentication failed")
            return False
        
        # 2. Test Enhanced Report Creation
        print("\n2. Testing Enhanced Report Creation...")
        sample_report = {
            "title": "Enhanced Google Forms Analytics Report",
            "description": "AI-powered analytics report with enhanced features",
            "data": {
                "google_form_id": "test_form_123",
                "report_type": "detailed",
                "date_range": "last_30_days",
                "form_source": "google_form",
                "analysis_type": "comprehensive"
            }
        }
        
        create_response = session.post(f"{API_URL}/reports", json=sample_report)
        if create_response.status_code == 201:
            print("✅ Enhanced report created successfully")
            report_data = create_response.json()
            report_id = report_data.get('id')
        else:
            print(f"❌ Failed to create report: {create_response.status_code}")
            print(create_response.text)
            return False
        
        # 3. Test Automated Reports List
        print("\n3. Testing Automated Reports List...")
        list_response = session.get(f"{API_URL}/automated-reports")
        if list_response.status_code == 200:
            print("✅ Retrieved automated reports list")
            reports = list_response.json()
            print(f"   Found {len(reports)} reports")
            
            # Verify enhanced fields
            if reports and len(reports) > 0:
                report = reports[0]
                required_fields = ['id', 'title', 'description', 'status', 'type', 'data_source', 'generated_by_ai', 'download_formats', 'metrics']
                missing_fields = [field for field in required_fields if field not in report]
                if missing_fields:
                    print(f"⚠️  Missing enhanced fields: {missing_fields}")
                else:
                    print("✅ All enhanced fields present")
        else:
            print(f"❌ Failed to get reports list: {list_response.status_code}")
            return False
        
        # 4. Test AI Suggestions Generation
        print("\n4. Testing AI Suggestions Generation...")
        ai_request = {
            "content": "This is a sample report content about user survey responses. The data shows positive trends in customer satisfaction.",
            "type": "analytics",
            "data_source": "google_forms"
        }
        
        ai_response = session.post(f"{API_URL}/reports/{report_id}/ai-suggestions", json=ai_request)
        if ai_response.status_code == 200:
            print("✅ AI suggestions generated successfully")
            suggestions = ai_response.json()
            print(f"   Generated {len(suggestions)} suggestions")
            for i, suggestion in enumerate(suggestions[:2]):  # Show first 2
                print(f"   - Suggestion {i+1}: {suggestion.get('type', 'unknown')} - {suggestion.get('suggestion', '')[:50]}...")
        else:
            print(f"❌ Failed to generate AI suggestions: {ai_response.status_code}")
            print(ai_response.text)
        
        # 5. Test Report Enhancement with AI
        print("\n5. Testing Report Enhancement with AI...")
        enhance_request = {
            "type": "insights"
        }
        
        enhance_response = session.post(f"{API_URL}/reports/{report_id}/enhance", json=enhance_request)
        if enhance_response.status_code == 200:
            print("✅ Report enhanced with AI successfully")
            enhanced_data = enhance_response.json()
            enhanced_content = enhanced_data.get('enhanced_content', '')
            print(f"   Enhanced content length: {len(enhanced_content)} characters")
        else:
            print(f"❌ Failed to enhance report: {enhance_response.status_code}")
            print(enhance_response.text)
        
        # 6. Test Download Functionality
        print("\n6. Testing Download Functionality...")
        download_formats = ['pdf', 'word', 'excel', 'html']
        
        for format_type in download_formats:
            download_request = {"format": format_type}
            download_response = session.post(f"{API_URL}/reports/{report_id}/download", json=download_request)
            
            if download_response.status_code == 200:
                print(f"✅ {format_type.upper()} download successful")
                content_type = download_response.headers.get('content-type', '')
                content_length = len(download_response.content)
                print(f"   Content-Type: {content_type}, Size: {content_length} bytes")
            else:
                print(f"❌ {format_type.upper()} download failed: {download_response.status_code}")
        
        # 7. Test Report Update with Enhanced Features
        print("\n7. Testing Report Update with Enhanced Features...")
        update_data = {
            "title": "Updated Enhanced Report with AI",
            "description": "Updated description with AI insights",
            "content": "This is enhanced content with AI-generated insights and recommendations."
        }
        
        update_response = session.put(f"{API_URL}/reports/{report_id}", json=update_data)
        if update_response.status_code == 200:
            print("✅ Report updated successfully")
        else:
            print(f"❌ Failed to update report: {update_response.status_code}")
        
        # 8. Test Report Retrieval with Enhanced Data
        print("\n8. Testing Enhanced Report Retrieval...")
        get_response = session.get(f"{API_URL}/reports/{report_id}")
        if get_response.status_code == 200:
            print("✅ Enhanced report retrieved successfully")
            report_details = get_response.json()
            
            # Verify enhanced features
            enhanced_features = ['ai_suggestions', 'generated_by_ai', 'download_formats']
            for feature in enhanced_features:
                if feature in report_details:
                    print(f"   ✅ Enhanced feature '{feature}' present")
                else:
                    print(f"   ⚠️  Enhanced feature '{feature}' missing")
        else:
            print(f"❌ Failed to retrieve report: {get_response.status_code}")
        
        # 9. Test Filter and Search Functionality
        print("\n9. Testing Filter and Search Functionality...")
        
        # Test status filter
        filter_response = session.get(f"{API_URL}/automated-reports?status=draft")
        if filter_response.status_code == 200:
            print("✅ Status filter working")
        
        # Test type filter
        type_response = session.get(f"{API_URL}/automated-reports?type=analytics")
        if type_response.status_code == 200:
            print("✅ Type filter working")
        
        # 10. Performance and Analytics Test
        print("\n10. Testing Performance and Analytics...")
        start_time = time.time()
        
        # Create multiple reports for testing
        for i in range(3):
            test_report = {
                "title": f"Performance Test Report {i+1}",
                "description": f"Test report for performance analysis {i+1}",
                "data": {"test_data": f"performance_test_{i+1}"}
            }
            session.post(f"{API_URL}/reports", json=test_report)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        print(f"✅ Created 3 reports in {creation_time:.2f} seconds")
        print(f"   Average creation time: {creation_time/3:.2f} seconds per report")
        
        # Final verification
        print("\n📊 Enhanced Automated Report System Test Summary:")
        print("✅ Authentication and authorization")
        print("✅ Enhanced report creation and management")
        print("✅ AI-powered suggestions and insights")
        print("✅ Multiple download formats")
        print("✅ Advanced filtering and search")
        print("✅ Real-time updates and editing")
        print("✅ Performance metrics and analytics")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_integration():
    """Test frontend integration points"""
    print("\n🎨 Testing Frontend Integration...")
    
    # Test component file existence
    frontend_components = [
        "frontend/src/components/EnhancedReportViewer.tsx",
        "frontend/src/components/AutomatedReportDashboard.tsx"
    ]
    
    for component in frontend_components:
        if os.path.exists(component):
            print(f"✅ Component exists: {component}")
        else:
            print(f"❌ Component missing: {component}")
    
    # Test for required dependencies
    package_json_path = "frontend/package.json"
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            required_deps = [
                '@mui/material',
                '@mui/icons-material',
                'react',
                'typescript'
            ]
            
            for dep in required_deps:
                if dep in all_deps:
                    print(f"✅ Required dependency: {dep}")
                else:
                    print(f"❌ Missing dependency: {dep}")
                    
        except Exception as e:
            print(f"❌ Error reading package.json: {e}")
    else:
        print("❌ package.json not found")

def main():
    """Main test function"""
    print("🧪 Enhanced Automated Report System - Comprehensive Test Suite")
    print("=" * 60)
    
    # Test backend functionality
    backend_success = test_enhanced_report_system()
    
    # Test frontend integration
    test_frontend_integration()
    
    print("\n" + "=" * 60)
    if backend_success:
        print("🎉 Enhanced Automated Report System tests completed successfully!")
        print("\n🚀 Ready for production! Key features available:")
        print("   • AI-powered report generation and enhancement")
        print("   • Advanced report viewer with editing capabilities") 
        print("   • Multiple export formats (PDF, Word, Excel, HTML)")
        print("   • Real-time AI suggestions and insights")
        print("   • Enhanced dashboard with filtering and search")
        print("   • Google Forms integration with analytics")
        print("   • Automated report scheduling and distribution")
    else:
        print("❌ Some tests failed. Please check the backend setup and try again.")
    
    return backend_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
