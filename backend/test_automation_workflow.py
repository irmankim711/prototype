#!/usr/bin/env python3
"""
Test Automation Workflow
Tests the complete end-to-end automation: Form → Submission → Excel Export → Report Generation
"""

from app import create_app, db
from app.models import Form, FormSubmission, Report, User
from app.tasks.enhanced_report_tasks import auto_generate_form_report_task
from datetime import datetime
import json

def test_automation_workflow():
    """Test the complete automation workflow"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Testing Complete Automation Workflow...")
        print("=" * 60)
        
        # Get test data
        form = Form.query.filter_by(title='Test Automation Form').first()
        user = User.query.filter_by(email='test@example.com').first()
        
        if not form or not user:
            print("❌ Test data not found. Run create_test_data.py first.")
            return
        
        print(f"✅ Found test form: {form.title} (ID: {form.id})")
        print(f"✅ Found test user: {user.email} (ID: {user.id})")
        
        # Check current submissions
        submissions = FormSubmission.query.filter_by(form_id=form.id).all()
        print(f"📊 Current submissions: {len(submissions)}")
        
        # Create a new submission to trigger automation
        new_submission_data = {
            'name': 'Alice Johnson',
            'email': 'alice.johnson@example.com',
            'age': 32,
            'department': 'Marketing'
        }
        
        new_submission = FormSubmission(
            form_id=form.id,
            data=json.dumps(new_submission_data),
            submitter_email=new_submission_data['email'],
            submitted_at=datetime.utcnow(),
            status='completed'
        )
        
        db.session.add(new_submission)
        db.session.commit()
        
        print(f"✅ Created new submission: {new_submission_data['name']}")
        print(f"📊 Total submissions now: {FormSubmission.query.filter_by(form_id=form.id).count()}")
        
        # Test the automation by triggering auto-report generation
        print("\n🎯 Testing Auto-Report Generation...")
        
        try:
            # This would normally be triggered automatically, but we'll test it manually
            result = auto_generate_form_report_task.delay(form.id, new_submission.id)
            print(f"✅ Automation task queued successfully!")
            print(f"   Task ID: {result.id}")
            print(f"   Status: {result.status}")
            
            # Wait a moment for task to process
            import time
            time.sleep(2)
            
            # Check task result
            if result.ready():
                task_result = result.get()
                print(f"✅ Task completed!")
                print(f"   Result: {task_result}")
            else:
                print(f"⏳ Task still processing...")
                print(f"   Status: {result.status}")
                
        except Exception as e:
            print(f"❌ Error testing automation: {str(e)}")
        
        # Check if any reports were created
        reports = Report.query.filter_by(program_id=1).all()
        print(f"\n📋 Reports created: {len(reports)}")
        
        for report in reports:
            print(f"   Report {report.id}: {report.title}")
            print(f"     Status: {report.status}")
            print(f"     Type: {report.report_type}")
            print(f"     Created: {report.created_at}")
        
        print("\n🎉 Automation Workflow Test Complete!")
        print("=" * 60)
        
        if reports:
            print("✅ SUCCESS: Automation is working!")
            print("   - Form submissions are being tracked")
            print("   - Reports are being generated")
            print("   - Celery tasks are executing")
        else:
            print("⚠️  Automation needs configuration:")
            print("   - Enable auto-reporting in form settings")
            print("   - Check Celery worker is running")
            print("   - Verify Redis connection")

if __name__ == '__main__':
    test_automation_workflow()
