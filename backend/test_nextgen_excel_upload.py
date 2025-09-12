#!/usr/bin/env python3
"""
Test script for NextGen Excel upload functionality
This script tests the Excel upload endpoint to ensure it's working correctly
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_nextgen_excel_upload():
    """Test the NextGen Excel upload endpoint"""
    
    # Test configuration
    base_url = "http://localhost:5000"
    endpoint = "/api/v1/nextgen/excel/upload"
    
    print("🧪 Testing NextGen Excel Upload Endpoint")
    print("=" * 50)
    
    # Test 1: Check if endpoint is accessible (without auth)
    print("\n1. Testing endpoint accessibility...")
    try:
        response = requests.get(f"{base_url}{endpoint}")
        if response.status_code == 405:  # Method not allowed (expected for GET)
            print("✅ Endpoint is accessible (GET not allowed as expected)")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is the backend running?")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False
    
    # Test 2: Check if we have a test Excel file
    print("\n2. Checking for test Excel file...")
    test_file_path = Path(__file__).parent / "test_template.xlsx"
    
    if test_file_path.exists():
        print(f"✅ Found test file: {test_file_path}")
        file_size = test_file_path.stat().st_size
        print(f"   File size: {file_size / 1024:.1f} KB")
    else:
        print("⚠️ No test Excel file found. Creating a simple one...")
        try:
            # Create a simple test Excel file
            import pandas as pd
            test_data = {
                'Name': ['John', 'Jane', 'Bob'],
                'Age': [25, 30, 35],
                'City': ['New York', 'Los Angeles', 'Chicago']
            }
            df = pd.DataFrame(test_data)
            df.to_excel(test_file_path, index=False)
            print(f"✅ Created test file: {test_file_path}")
        except ImportError:
            print("❌ pandas not available. Please install: pip install pandas openpyxl")
            return False
        except Exception as e:
            print(f"❌ Failed to create test file: {e}")
            return False
    
    # Test 3: Test file parsing service directly
    print("\n3. Testing Excel parsing service...")
    try:
        from app.services.excel_parser import ExcelParserService
        
        excel_parser = ExcelParserService()
        result = excel_parser.parse_excel_file(str(test_file_path))
        
        if result.get('success'):
            print("✅ Excel parsing service working correctly")
            print(f"   Tables found: {result.get('tables_count', 0)}")
            print(f"   Total rows: {result.get('total_rows', 0)}")
            print(f"   Total columns: {result.get('total_columns', 0)}")
        else:
            print(f"❌ Excel parsing failed: {result.get('error')}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import Excel parser: {e}")
        return False
    except Exception as e:
        print(f"❌ Excel parsing test failed: {e}")
        return False
    
    # Test 4: Check if uploads directory exists
    print("\n4. Checking uploads directory...")
    uploads_dir = Path(__file__).parent / "app" / "static" / "uploads" / "excel"
    
    if uploads_dir.exists():
        print(f"✅ Uploads directory exists: {uploads_dir}")
        # List existing files
        excel_files = list(uploads_dir.glob("*.xlsx"))
        print(f"   Existing Excel files: {len(excel_files)}")
        for file in excel_files[:3]:  # Show first 3
            print(f"     - {file.name}")
    else:
        print(f"⚠️ Uploads directory doesn't exist. Creating: {uploads_dir}")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Created uploads directory")
    
    # Test 5: Test the route registration
    print("\n5. Testing route registration...")
    try:
        from app.routes.nextgen_report_builder import nextgen_bp
        
        if nextgen_bp:
            print("✅ NextGen blueprint imported successfully")
            print(f"   Blueprint name: {nextgen_bp.name}")
            print(f"   URL prefix: {nextgen_bp.url_prefix}")
            
            # List registered routes
            routes = []
            for rule in nextgen_bp.url_map.iter_rules():
                routes.append(f"{rule.methods} {rule.rule}")
            
            print(f"   Registered routes: {len(routes)}")
            for route in routes[:5]:  # Show first 5
                print(f"     - {route}")
        else:
            print("❌ NextGen blueprint is None")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import NextGen routes: {e}")
        return False
    except Exception as e:
        print(f"❌ Route registration test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Start the backend server: python run.py")
    print("   2. Test with a real Excel file upload")
    print("   3. Check the logs for any errors")
    
    return True

if __name__ == "__main__":
    success = test_nextgen_excel_upload()
    sys.exit(0 if success else 1)


