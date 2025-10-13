#!/usr/bin/env python3
"""
Test the complete Form Automation Service workflow
"""

import os
import sys
import logging
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_form_automation_workflow():
    """Test the complete workflow: Template -> Form -> Export -> Report"""
    try:
        # Import after setting up the path
        from app import create_app
        from app.services.form_automation import FormAutomationService
        
        print("🚀 Starting Form Automation System Test")
        print("=" * 50)
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Initialize the service
            automation_service = FormAutomationService()
            
            # Test 1: Create form from template
            print("\n📝 Test 1: Creating form from Excel template...")
            template_path = "test_template.xlsx"
            
            if not os.path.exists(template_path):
                print(f"❌ Template file not found: {template_path}")
                return False
                
            form_result = automation_service.create_form_from_template(
                template_path=template_path,
                form_title="Test Company Data Collection"
            )
            
            if form_result['success']:
                print(f"✅ Form created successfully!")
                print(f"   - Detected {form_result['detected_fields']} fields")
                print(f"   - Field types: {form_result['field_types']}")
            else:
                print(f"❌ Form creation failed: {form_result['error']}")
                return False
            
            # Test 2: Simulate form data and export
            print("\n📊 Test 2: Testing Excel export (simulated data)...")
            
            # For testing, we'll create a mock form with sample data
            from app.models import db, Form, FormSubmission
            
            # Create a test form in the database
            test_form = Form(
                title="Test Automation Form",
                schema={
                    'fields': [
                        {'id': 'company_name', 'label': 'Company Name', 'type': 'text', 'required': True},
                        {'id': 'contact_person', 'label': 'Contact Person', 'type': 'text', 'required': True},
                        {'id': 'email_address', 'label': 'Email Address', 'type': 'email', 'required': True},
                        {'id': 'annual_revenue', 'label': 'Annual Revenue', 'type': 'number', 'required': False}
                    ]
                },
                is_active=True,
                creator_id=1
            )
            
            db.session.add(test_form)
            db.session.commit()
            
            # Add sample submissions
            sample_submissions = [
                {
                    'company_name': 'Tech Corp',
                    'contact_person': 'John Doe',
                    'email_address': 'john@techcorp.com',
                    'annual_revenue': '1000000'
                },
                {
                    'company_name': 'Digital Solutions',
                    'contact_person': 'Jane Smith',
                    'email_address': 'jane@digitalsolutions.com',
                    'annual_revenue': '500000'
                },
                {
                    'company_name': 'Innovation Labs',
                    'contact_person': 'Mike Johnson',
                    'email_address': 'mike@innovationlabs.com',
                    'annual_revenue': '2000000'
                }
            ]
            
            for submission_data in sample_submissions:
                submission = FormSubmission(
                    form_id=test_form.id,
                    data=submission_data,
                    ip_address='127.0.0.1',
                    submitted_at=datetime.utcnow()
                )
                db.session.add(submission)
            
            db.session.commit()
            
            # Export to Excel
            export_result = automation_service.export_form_data_to_excel(
                form_id=test_form.id,
                include_analytics=True
            )
            
            if export_result['success']:
                print(f"✅ Excel export successful!")
                print(f"   - File saved to: {export_result['file_path']}")
            else:
                print(f"❌ Excel export failed: {export_result['error']}")
                return False
            
            # Test 3: Generate report from Excel
            print("\n📋 Test 3: Generating HTML report from Excel data...")
            
            report_result = automation_service.generate_report_from_excel(
                excel_path=export_result['file_path'],
                template_path='templates/default_report.jinja'
            )
            
            if report_result['success']:
                print(f"✅ Report generation successful!")
                print(f"   - Report saved to: {report_result['report_path']}")
                
                # Read and display first 200 characters of the report
                with open(report_result['report_path'], 'r', encoding='utf-8') as f:
                    report_preview = f.read()[:200]
                print(f"   - Report preview: {report_preview}...")
                
            else:
                print(f"❌ Report generation failed: {report_result['error']}")
                return False
            
            # Test 4: Complete automated workflow
            print("\n🔄 Test 4: Testing complete automated workflow...")
            
            workflow_result = automation_service.create_automated_workflow(
                template_path=template_path,
                workflow_name="Complete Test Workflow"
            )
            
            if workflow_result['success']:
                print(f"✅ Complete workflow successful!")
                print(f"   - Workflow: {workflow_result['workflow_name']}")
                print(f"   - Template: {workflow_result['template_path']}")
                print(f"   - Detected Fields: {workflow_result['automation_steps'][0]['fields_detected']}")
            else:
                print(f"❌ Complete workflow failed: {workflow_result['error']}")
                return False
            
            print("\n🎉 All tests completed successfully!")
            print("=" * 50)
            return True
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_form_automation_workflow()
    if success:
        print("\n✅ Form Automation System is working correctly!")
    else:
        print("\n❌ Form Automation System has issues that need to be resolved.")
    
    sys.exit(0 if success else 1)
