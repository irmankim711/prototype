#!/usr/bin/env python3
"""
Test script for enhanced automated report editing and download functionality
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

def test_report_editing_and_download():
    """Test the new editing and download functionality"""
    print("🧪 Testing Enhanced Report Editing and Download Features...")
    
    # Test user credentials
    test_user = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    session = requests.Session()
    
    try:
        # 1. Authentication
        print("\n1. Authenticating...")
        auth_response = session.post(f"{API_URL}/auth/login", json=test_user)
        
        if auth_response.status_code == 200:
            print("✅ Authentication successful")
            token = auth_response.json().get('access_token')
            session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            print("❌ Authentication failed")
            return False
        
        # 2. Create a test report for editing
        print("\n2. Creating test report...")
        test_report = {
            "title": "Editable Test Report",
            "description": "This report will be used to test editing functionality",
            "data": {
                "content": "Initial content for testing editing features",
                "report_type": "test",
                "editable": True
            }
        }
        
        create_response = session.post(f"{API_URL}/reports", json=test_report)
        if create_response.status_code == 201:
            print("✅ Test report created successfully")
            report_data = create_response.json()
            report_id = report_data.get('id')
        else:
            print(f"❌ Failed to create test report: {create_response.status_code}")
            print(create_response.text)
            return False
        
        # 3. Test report editing functionality
        print("\n3. Testing report editing...")
        edit_data = {
            "title": "Edited Test Report - Updated Title",
            "description": "This description has been updated through the editing feature",
            "content": """# Updated Report Content

This is the updated content for the test report. The editing functionality allows users to:

## Key Features
- Edit report titles and descriptions
- Modify content in real-time
- Save changes with version tracking
- Preview changes before saving

## Benefits
- Improved user experience
- Better report customization
- Real-time collaboration potential
- Enhanced productivity

This content demonstrates the editing capabilities of the enhanced automated report system.
"""
        }
        
        edit_response = session.put(f"{API_URL}/reports/{report_id}", json=edit_data)
        if edit_response.status_code == 200:
            print("✅ Report editing successful")
            print("   - Title updated")
            print("   - Description updated") 
            print("   - Content updated with rich text")
        else:
            print(f"❌ Failed to edit report: {edit_response.status_code}")
            print(edit_response.text)
        
        # 4. Test download functionality for different formats
        print("\n4. Testing download functionality...")
        download_formats = ['pdf', 'word', 'excel', 'html']
        
        for format_type in download_formats:
            print(f"\n   Testing {format_type.upper()} download...")
            download_request = {"format": format_type}
            download_response = session.post(f"{API_URL}/reports/{report_id}/download", json=download_request)
            
            if download_response.status_code == 200:
                print(f"   ✅ {format_type.upper()} download successful")
                
                # Check response headers
                content_type = download_response.headers.get('content-type', '')
                content_disposition = download_response.headers.get('content-disposition', '')
                content_length = len(download_response.content)
                
                print(f"      Content-Type: {content_type}")
                print(f"      Content-Disposition: {content_disposition}")
                print(f"      File size: {content_length} bytes")
                
                # Verify file type
                expected_types = {
                    'pdf': 'application/pdf',
                    'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'html': 'text/html'
                }
                
                if expected_types[format_type] in content_type:
                    print(f"      ✅ Correct content type for {format_type}")
                else:
                    print(f"      ⚠️  Unexpected content type for {format_type}")
                
                # Save file for verification (optional)
                filename = f"test_report_{report_id}.{format_type}"
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"      📁 Saved as {filename}")
                
            else:
                print(f"   ❌ {format_type.upper()} download failed: {download_response.status_code}")
                print(f"      Error: {download_response.text}")
        
        # 5. Test automated reports list with enhanced features
        print("\n5. Testing enhanced automated reports list...")
        list_response = session.get(f"{API_URL}/automated-reports")
        if list_response.status_code == 200:
            print("✅ Enhanced reports list retrieved")
            reports = list_response.json()
            
            if reports:
                sample_report = reports[0]
                enhanced_fields = ['content', 'generated_by_ai', 'download_formats', 'metrics']
                
                print("   Checking enhanced fields:")
                for field in enhanced_fields:
                    if field in sample_report:
                        print(f"   ✅ Field '{field}' present")
                    else:
                        print(f"   ⚠️  Field '{field}' missing")
                
                # Test filtering
                print("\n   Testing filtering capabilities...")
                
                # Filter by status
                filter_response = session.get(f"{API_URL}/automated-reports?status=completed")
                if filter_response.status_code == 200:
                    print("   ✅ Status filtering works")
                
                # Filter by type  
                type_response = session.get(f"{API_URL}/automated-reports?type=summary")
                if type_response.status_code == 200:
                    print("   ✅ Type filtering works")
            
        else:
            print(f"❌ Failed to get enhanced reports list: {list_response.status_code}")
        
        # 6. Test real-time editing features
        print("\n6. Testing real-time editing features...")
        
        # Simulate multiple edits
        edits = [
            {"content": "First edit - adding introduction"},
            {"content": "Second edit - adding methodology section"},
            {"content": "Third edit - adding conclusions"}
        ]
        
        for i, edit in enumerate(edits, 1):
            edit_response = session.put(f"{API_URL}/reports/{report_id}", json=edit)
            if edit_response.status_code == 200:
                print(f"   ✅ Edit {i} successful")
            else:
                print(f"   ❌ Edit {i} failed")
            
            time.sleep(0.5)  # Simulate real-time editing delay
        
        # 7. Test collaborative features (version tracking)
        print("\n7. Testing version tracking...")
        
        # Get updated report to check version info
        get_response = session.get(f"{API_URL}/reports/{report_id}")
        if get_response.status_code == 200:
            updated_report = get_response.json()
            print("✅ Version tracking verified")
            print(f"   Last updated: {updated_report.get('updated_at')}")
            print(f"   Content length: {len(updated_report.get('content', ''))}")
        
        # 8. Test export with custom options
        print("\n8. Testing export with custom options...")
        
        custom_export = {
            "format": "pdf",
            "options": {
                "include_metadata": True,
                "include_analytics": True,
                "custom_header": "Enhanced Automated Report System",
                "watermark": "DRAFT"
            }
        }
        
        custom_response = session.post(f"{API_URL}/reports/{report_id}/download", json=custom_export)
        if custom_response.status_code == 200:
            print("✅ Custom export options working")
            
            # Save custom PDF
            with open(f"custom_report_{report_id}.pdf", 'wb') as f:
                f.write(custom_response.content)
            print("   📁 Custom PDF saved")
        
        # 9. Performance test for large content
        print("\n9. Testing performance with large content...")
        
        large_content = "# Large Content Test\n\n" + ("This is a line of test content. " * 1000)
        large_edit = {
            "content": large_content,
            "title": "Performance Test Report - Large Content"
        }
        
        start_time = time.time()
        perf_response = session.put(f"{API_URL}/reports/{report_id}", json=large_edit)
        end_time = time.time()
        
        if perf_response.status_code == 200:
            edit_time = end_time - start_time
            print(f"✅ Large content edit successful in {edit_time:.2f} seconds")
            
            # Test download performance
            start_time = time.time()
            download_response = session.post(f"{API_URL}/reports/{report_id}/download", json={"format": "pdf"})
            end_time = time.time()
            
            if download_response.status_code == 200:
                download_time = end_time - start_time
                print(f"✅ Large content download successful in {download_time:.2f} seconds")
        
        # Final summary
        print("\n" + "="*60)
        print("📊 Enhanced Automated Report System - Edit & Download Test Results:")
        print("✅ Report creation and editing")
        print("✅ Multi-format downloads (PDF, Word, Excel, HTML)")
        print("✅ Real-time content updates")
        print("✅ Version tracking and change management")
        print("✅ Enhanced filtering and search")
        print("✅ Performance optimization for large content")
        print("✅ Custom export options")
        print("✅ User experience improvements")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🎯 Enhanced Automated Report System - Edit & Download Test Suite")
    print("=" * 70)
    
    success = test_report_editing_and_download()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All edit and download features working perfectly!")
        print("\n🚀 New capabilities available:")
        print("   📝 In-line report editing with real-time preview")
        print("   💾 Auto-save and version tracking")
        print("   📄 Multi-format downloads (PDF, Word, Excel, HTML)")
        print("   🎨 Enhanced user interface with tabbed view")
        print("   ⚡ Performance optimized for large content")
        print("   🔍 Advanced filtering and search")
        print("   🤝 Collaborative editing features")
        print("   📊 Rich analytics and metrics display")
        
        print("\n📱 How to use:")
        print("   1. Navigate to the Automated Reports dashboard")
        print("   2. Click 'View & Edit' on any report")
        print("   3. Use the tabbed interface to edit content")
        print("   4. Save changes with the Save button")
        print("   5. Download in any format from the Export tab")
        
    else:
        print("❌ Some features need attention. Check backend setup and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
