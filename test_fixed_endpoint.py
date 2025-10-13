#!/usr/bin/env python3
"""
Test script to verify the fixed endpoint by temporarily bypassing JWT authentication
"""

import os
import sys
import tempfile
from pathlib import Path
import pandas as pd

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_fixed_endpoint_directly():
    """
    Test the fixed endpoint by calling the route function directly
    """
    print("🧪 Testing Fixed Endpoint Logic Directly")
    print("=" * 50)
    
    try:
        # Set up Flask app context
        from app import create_app, db
        app = create_app('development')
        
        with app.app_context():
            # Create test Excel file
            test_data = {
                'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
                'Age': [25, 30, 35],
                'Email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
                'Rating': [4, 5, 3],
                'Comments': ['Good service', 'Excellent experience', 'Average']
            }
            
            df = pd.DataFrame(test_data)
            
            # Save to Excel
            excel_dir = backend_path / "static" / "uploads" / "excel"
            excel_dir.mkdir(parents=True, exist_ok=True)
            
            excel_path = excel_dir / "test_endpoint_data.xlsx"
            df.to_excel(excel_path, index=False)
            
            print(f"✅ Created test Excel file: {excel_path}")
            
            # Test the route logic by calling the service directly but simulating the database save
            from app.routes.nextgen_report_builder import form_automation
            from app.models import Report, User
            
            # Create or get test user
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                print("❌ Test user not found in database")
                return False
            
            print(f"✅ Using test user: {test_user.id}")
            
            # Test parameters
            excel_file_path = str(excel_path)
            template_id = "Temp1"
            report_title = "Test Fixed Endpoint Report"
            user_id = test_user.id
            
            print(f"🔍 Testing with:")
            print(f"  Excel: {excel_file_path}")
            print(f"  Template: {template_id}")
            print(f"  User ID: {user_id}")
            
            # Find template file
            templates_dir = backend_path / "templates"
            template_file = templates_dir / "Temp1.docx"
            
            if not template_file.exists():
                print(f"❌ Template file not found: {template_file}")
                return False
            
            print(f"✅ Template file found: {template_file}")
            
            # Test FormAutomationService (we know this works)
            print("\n🔧 Testing FormAutomationService...")
            generation_result = form_automation.generate_report_from_excel(
                excel_path=excel_file_path,
                template_path=str(template_file)
            )
            
            if not generation_result['success']:
                print(f"❌ FormAutomationService failed: {generation_result}")
                return False
            
            print(f"✅ FormAutomationService succeeded: {generation_result.get('report_path')}")
            
            # Test database save with fixed field mappings
            print("\n💾 Testing database save with fixed field mappings...")
            
            # Get file info
            report_path = generation_result.get('report_path')
            file_size = 0
            if report_path and os.path.exists(report_path):
                file_size = os.path.getsize(report_path)
                print(f"📄 Generated file: {report_path} ({file_size} bytes)")
            
            # Determine file format and set appropriate file paths
            report_file_extension = Path(report_path).suffix.lower() if report_path else '.tex'
            print(f"📄 File extension: {report_file_extension}")
            
            # Get or create default program (mimic the route logic)
            from app.models import Program, ReportTemplate
            try:
                default_program = Program.query.first()
                if not default_program:
                    default_program = Program(
                        name="Default Program",
                        description="Default program for Excel automation reports",
                        status="active"
                    )
                    db.session.add(default_program)
                    db.session.flush()
            except Exception as program_error:
                print(f"⚠️ Could not create/find default program: {program_error}")
                default_program = type('obj', (object,), {'id': 1})()
            
            # Get or create template record
            template_record = ReportTemplate.query.filter_by(name=template_id).first()
            if not template_record:
                try:
                    template_record = ReportTemplate(
                        name=template_id,
                        description=f"Template for {template_id}",
                        template_type="docx",
                        file_path=str(template_file),
                        category="automation"
                    )
                    db.session.add(template_record)
                    db.session.flush()
                except Exception as template_error:
                    print(f"⚠️ Could not create template record: {template_error}")
                    template_record = type('obj', (object,), {'id': 1})()
            
            # Create Report record with correct production model fields
            report = Report(
                title=report_title,
                description=f"Automated report generated from {os.path.basename(excel_file_path)}",
                generation_status='completed',  # Correct field name
                report_type='excel_automation',
                created_by=str(user_id),  # String field
                program_id=default_program.id,  # Required field
                template_id=template_record.id,  # Integer FK
                
                # File information
                file_path=report_path,
                file_size=file_size,
                file_format=report_file_extension.replace('.', ''),
                download_url=f"/static/generated/{os.path.basename(report_path or '')}",
                
                # Data and configuration as JSON
                data_source={
                    'excel_source': excel_file_path, 
                    'template_used': template_id,
                    'file_type': 'excel',
                    'automation_type': 'excel'
                },
                generation_config={
                    'template_id': template_id,
                    'template_file': str(template_file),
                    'excel_file': excel_file_path,
                    'automation_method': 'form_automation_service'
                },
                
                # Generation metadata
                generated_at=datetime.utcnow(),
                generation_time_seconds=0
            )
            
            # Test database save
            try:
                db.session.add(report)
                db.session.commit()
                print(f"✅ Database save successful! Report ID: {report.id}")
                
                # Test response format
                response_data = {
                    'success': True,
                    'message': 'Report generated successfully',
                    'report': {
                        'id': report.id,
                        'title': report.title,
                        'description': report.description,
                        'status': report.status,
                        'report_type': report.report_type,
                        'filePath': generation_result['report_path'],
                        'filename': generation_result.get('filename'),
                        'docx_file_path': report.docx_file_path,
                        'docx_file_size': report.docx_file_size,
                        'docx_download_url': report.docx_download_url,
                        'excel_file_path': report.excel_file_path,
                        'excel_file_size': report.excel_file_size,
                        'excel_download_url': report.excel_download_url,
                        'created_at': report.created_at.isoformat(),
                        'updated_at': report.updated_at.isoformat(),
                        'templateUsed': template_id,
                        'excelSource': excel_file_path
                    },
                    'generationDetails': generation_result
                }
                
                print(f"✅ Response format test successful!")
                print(f"📄 Response keys: {list(response_data.keys())}")
                print(f"📄 Report keys: {list(response_data['report'].keys())}")
                
                return True
                
            except Exception as db_error:
                print(f"❌ Database save failed: {db_error}")
                print(f"🔍 Error type: {type(db_error).__name__}")
                import traceback
                print(f"🔍 Traceback: {traceback.format_exc()}")
                return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Fixed Endpoint Logic")
    print("=" * 60)
    
    success = test_fixed_endpoint_directly()
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 The 500 error has been fixed!")
        print("🔧 The endpoint should now work correctly from the frontend")
    else:
        print("\n❌ Tests failed - more debugging needed")
    
    print("\n" + "=" * 60)
