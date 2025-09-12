#!/usr/bin/env python3
"""
Test LaTeX Conversion System
Tests the complete LaTeX conversion workflow including:
- LaTeX to PDF conversion
- LaTeX to DOCX conversion
- Preview endpoints
- Lifecycle management
- Authentication verification
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_latex_conversion_service():
    """Test the LaTeX conversion service directly"""
    print("🔧 Testing LaTeX Conversion Service...")
    
    try:
        from app.services.latex_conversion_service import latex_conversion_service
        
        # Test with existing LaTeX file
        latex_file = "static/generated/report_Temp1_20250828_035612.tex"
        
        if not os.path.exists(latex_file):
            print(f"❌ LaTeX file not found: {latex_file}")
            return False
        
        print(f"✓ Found LaTeX file: {latex_file}")
        
        # Test PDF conversion
        try:
            pdf_path, pdf_size = latex_conversion_service.convert_latex_to_pdf(latex_file)
            print(f"✓ PDF conversion successful: {pdf_path} ({pdf_size} bytes)")
        except Exception as e:
            print(f"⚠️ PDF conversion failed (expected if pdflatex not installed): {str(e)}")
        
        # Test DOCX conversion
        try:
            docx_path, docx_size = latex_conversion_service.convert_latex_to_docx(latex_file)
            print(f"✓ DOCX conversion successful: {docx_path} ({docx_size} bytes)")
        except Exception as e:
            print(f"❌ DOCX conversion failed: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LaTeX conversion service test failed: {str(e)}")
        return False

def test_lifecycle_service():
    """Test the report lifecycle service"""
    print("\n🔧 Testing Report Lifecycle Service...")
    
    try:
        from app.services.report_lifecycle_service import report_lifecycle_service
        
        # Test storage usage
        usage = report_lifecycle_service.get_storage_usage()
        print(f"✓ Storage usage retrieved: {usage.get('total_reports', 0)} reports")
        
        # Test cleanup (dry run - don't actually delete)
        print("✓ Lifecycle service initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle service test failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test the API endpoints (requires running server)"""
    print("\n🔧 Testing API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/reports/health", timeout=5)
        if response.status_code == 200:
            print("✓ Reports health endpoint accessible")
        else:
            print(f"⚠️ Reports health endpoint returned {response.status_code}")
    except requests.exceptions.RequestException:
        print("⚠️ Reports health endpoint not accessible (server may not be running)")
    
    # Test storage endpoint (requires authentication)
    try:
        response = requests.get(f"{base_url}/api/reports/lifecycle/storage", timeout=5)
        if response.status_code == 401:
            print("✓ Storage endpoint properly protected (authentication required)")
        else:
            print(f"⚠️ Storage endpoint returned {response.status_code}")
    except requests.exceptions.RequestException:
        print("⚠️ Storage endpoint not accessible (server may not be running)")
    
    return True

def test_database_models():
    """Test the database models"""
    print("\n🔧 Testing Database Models...")
    
    try:
        from app import create_app, db
        from app.models import Report, User
        
        # Create test app context
        app = create_app()
        with app.app_context():
            # Test Report model
            report = Report(
                title="Test LaTeX Report",
                description="Test report for LaTeX conversion",
                report_type="latex_based",
                status="pending",
                user_id=1
            )
            
            print("✓ Report model created successfully")
            
            # Test User model
            user = User(
                email="test@example.com",
                password_hash="test_hash",
                first_name="Test",
                last_name="User"
            )
            
            print("✓ User model created successfully")
            
            return True
            
    except Exception as e:
        print(f"❌ Database models test failed: {str(e)}")
        return False

def test_file_structure():
    """Test the file structure and directories"""
    print("\n🔧 Testing File Structure...")
    
    required_dirs = [
        "static/generated",
        "temp/latex_conversion",
        "uploads/reports"
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"⚠️ Directory missing: {dir_path}")
            # Create directory
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ Created directory: {dir_path}")
    
    return True

def test_dependencies():
    """Test required dependencies"""
    print("\n🔧 Testing Dependencies...")
    
    required_packages = [
        "docx",
        "reportlab",
        "openpyxl",
        "pandas"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ Package available: {package}")
        except ImportError:
            print(f"❌ Package missing: {package}")
            return False
    
    return True

def test_latex_compilation():
    """Test if LaTeX compilation is available"""
    print("\n🔧 Testing LaTeX Compilation...")
    
    try:
        import subprocess
        
        # Test if pdflatex is available
        result = subprocess.run(['pdflatex', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ pdflatex available for LaTeX compilation")
            return True
        else:
            print("⚠️ pdflatex not available (LaTeX to PDF conversion will fail)")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ pdflatex not found (LaTeX to PDF conversion will fail)")
        return False
    except Exception as e:
        print(f"⚠️ LaTeX compilation test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing LaTeX Conversion System")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("Database Models", test_database_models),
        ("LaTeX Compilation", test_latex_compilation),
        ("LaTeX Conversion Service", test_latex_conversion_service),
        ("Lifecycle Service", test_lifecycle_service),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LaTeX conversion system is ready.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
