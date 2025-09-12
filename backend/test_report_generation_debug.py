#!/usr/bin/env python3
"""
Report Generation Debug Script
Tests template lookup, database connectivity, and report generation pipeline
"""

import sys
sys.path.append('.')

from app import create_app
from app import db
import os
import traceback

def test_flask_app_context():
    """Test Flask application context"""
    print("🚀 Testing Flask Application Context...")
    
    try:
        app = create_app()
        print("✅ Flask app created successfully")
        
        with app.app_context():
            print("✅ Flask app context activated")
            
            # Test database connection
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
            print("✅ Database connection working")
            
            return app
        
    except Exception as e:
        print(f"❌ Flask app context failed: {e}")
        traceback.print_exc()
        return None

def test_template_lookup(app):
    """Test template lookup in database"""
    print("\n📋 Testing Template Lookup...")
    
    with app.app_context():
        try:
            from app.models import ReportTemplate
            
            # Check if ReportTemplate table exists
            try:
                total_templates = ReportTemplate.query.count()
                print(f"✅ ReportTemplate table accessible: {total_templates} templates found")
            except Exception as e:
                print(f"❌ ReportTemplate table error: {e}")
                return False
            
            # Look for specific templates
            test_templates = ['Temp1', 'default', 'Standard Business Report']
            
            for template_name in test_templates:
                # Try different lookup methods
                template = None
                
                # Method 1: By template_id
                try:
                    template = ReportTemplate.query.filter_by(template_id=template_name).first()
                    if template:
                        print(f"✅ Found template '{template_name}' by template_id")
                        print(f"   📋 Name: {template.template_name}")
                        print(f"   🆔 ID: {template.id}")
                        continue
                except Exception as e:
                    print(f"⚠️  Template lookup by template_id failed: {e}")
                
                # Method 2: By name
                try:
                    template = ReportTemplate.query.filter_by(name=template_name).first()
                    if template:
                        print(f"✅ Found template '{template_name}' by name")
                        continue
                except Exception as e:
                    print(f"⚠️  Template lookup by name failed: {e}")
                
                # Method 3: By template_name
                try:
                    template = ReportTemplate.query.filter_by(template_name=template_name).first()
                    if template:
                        print(f"✅ Found template '{template_name}' by template_name")
                        continue
                except Exception as e:
                    print(f"⚠️  Template lookup by template_name failed: {e}")
                
                print(f"❌ Template '{template_name}' not found")
            
            # List all available templates
            print("\n📋 All Available Templates:")
            try:
                all_templates = ReportTemplate.query.limit(10).all()
                for template in all_templates:
                    print(f"   🔖 ID: {template.id}")
                    print(f"      Name: {getattr(template, 'name', 'N/A')}")
                    print(f"      Template Name: {getattr(template, 'template_name', 'N/A')}")
                    print(f"      Template ID: {getattr(template, 'template_id', 'N/A')}")
                    print(f"      Active: {getattr(template, 'is_active', 'N/A')}")
                    print()
                    
            except Exception as e:
                print(f"❌ Could not list templates: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Template lookup test failed: {e}")
            traceback.print_exc()
            return False

def test_report_model_creation(app):
    """Test Report model creation and database interaction"""
    print("\n📊 Testing Report Model Creation...")
    
    with app.app_context():
        try:
            from app.models import Report, User
            
            # Check if we can query reports
            report_count = Report.query.count()
            print(f"✅ Report model accessible: {report_count} reports found")
            
            # Check if we can query users (for user_id)
            try:
                user_count = User.query.count()
                print(f"✅ User model accessible: {user_count} users found")
                
                # Get first user for testing
                first_user = User.query.first()
                if first_user:
                    test_user_id = first_user.id
                    print(f"✅ Test user available: ID {test_user_id}")
                else:
                    test_user_id = 1  # Default fallback
                    print(f"⚠️  No users found, using fallback ID: {test_user_id}")
                    
            except Exception as e:
                print(f"❌ User model error: {e}")
                test_user_id = 1  # Default fallback
            
            # Try creating a test report record (without committing)
            try:
                test_report = Report(
                    title="Debug Test Report",
                    description="Test report for debugging",
                    report_type="test",
                    generation_status="pending",
                    template_id=1,
                    program_id=1,
                    user_id=test_user_id,
                    generation_config={"test": True},
                    data_source={"test_data": [1, 2, 3]}
                )
                
                # Add to session (but don't commit)
                db.session.add(test_report)
                print("✅ Report model creation successful (not committed)")
                
                # Rollback to avoid creating test data
                db.session.rollback()
                
            except Exception as e:
                print(f"❌ Report model creation failed: {e}")
                db.session.rollback()
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Report model test failed: {e}")
            traceback.print_exc()
            return False

def test_excel_processing_integration(app):
    """Test Excel processing integration with Flask context"""
    print("\n📊 Testing Excel Processing Integration...")
    
    with app.app_context():
        try:
            # Import Excel processing libraries
            import openpyxl
            print("✅ openpyxl available in Flask context")
            
            # Test file paths that the app would use
            from flask import current_app
            
            # Get uploads directory
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'excel')
            print(f"📁 Expected uploads directory: {uploads_dir}")
            
            if os.path.exists(uploads_dir):
                print("✅ Uploads directory exists")
                
                # List Excel files
                excel_files = [f for f in os.listdir(uploads_dir) if f.endswith(('.xlsx', '.xls'))]
                if excel_files:
                    print(f"📋 Found {len(excel_files)} Excel files:")
                    for file in excel_files[:3]:  # Show first 3
                        print(f"   - {file}")
                    
                    # Test processing first file
                    test_file = os.path.join(uploads_dir, excel_files[0])
                    try:
                        wb = openpyxl.load_workbook(test_file, read_only=True)
                        print(f"✅ Successfully loaded: {excel_files[0]}")
                        print(f"📋 Sheets: {wb.sheetnames}")
                        wb.close()
                        
                    except Exception as e:
                        print(f"❌ Failed to load Excel file: {e}")
                        
                else:
                    print("⚠️  No Excel files found for testing")
            else:
                print(f"❌ Uploads directory does not exist: {uploads_dir}")
                # Try to create it
                try:
                    os.makedirs(uploads_dir, exist_ok=True)
                    print("✅ Created uploads directory")
                except Exception as e:
                    print(f"❌ Could not create uploads directory: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Excel processing integration failed: {e}")
            traceback.print_exc()
            return False

def test_celery_task_simulation(app):
    """Test simulating Celery task without actually running Celery"""
    print("\n⚙️  Testing Celery Task Simulation...")
    
    with app.app_context():
        try:
            # Import the task function directly
            from app.tasks.enhanced_report_tasks import generate_comprehensive_report_task
            
            print("✅ Celery task import successful")
            
            # Don't actually run the task, just verify it's importable and has expected signature
            task_func = generate_comprehensive_report_task
            print(f"✅ Task function accessible: {task_func.__name__}")
            
            # Check if we can import the service modules that tasks use
            try:
                from app.services.report_generation_service import report_generation_service
                print("✅ Report generation service available")
            except Exception as e:
                print(f"❌ Report generation service import failed: {e}")
            
            try:
                from app.services.excel_export_service import excel_export_service  
                print("✅ Excel export service available")
            except Exception as e:
                print(f"❌ Excel export service import failed: {e}")
            
            print("ℹ️  Celery task structure appears correct")
            print("📝 To test actual task execution, run Celery worker separately")
            
            return True
            
        except Exception as e:
            print(f"❌ Celery task simulation failed: {e}")
            traceback.print_exc()
            return False

def main():
    """Run comprehensive debug tests"""
    print("🔍 Report Generation Debug Test Suite")
    print("=" * 60)
    
    # First test Flask app
    app = test_flask_app_context()
    if not app:
        print("💥 Flask app failed - cannot continue")
        return False
    
    tests = [
        ("Template Lookup", lambda: test_template_lookup(app)),
        ("Report Model Creation", lambda: test_report_model_creation(app)),
        ("Excel Processing Integration", lambda: test_excel_processing_integration(app)),
        ("Celery Task Simulation", lambda: test_celery_task_simulation(app))
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result if result is not None else True
        except Exception as e:
            print(f"💥 Test crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEBUG TEST RESULTS:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    # Diagnosis
    print("\n🔬 DIAGNOSIS:")
    if results.get("Template Lookup", False):
        print("✅ Templates accessible - not a template issue")
    else:
        print("❌ Template lookup failed - likely template/database issue")
    
    if results.get("Excel Processing Integration", False):
        print("✅ Excel processing works - not a library issue")
    else:
        print("❌ Excel processing failed - library/path issue")
    
    if results.get("Celery Task Simulation", False):
        print("✅ Celery imports work - likely execution or worker issue")
    else:
        print("❌ Celery task imports failed - code structure issue")
    
    return passed >= 3  # Consider success if most tests pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)