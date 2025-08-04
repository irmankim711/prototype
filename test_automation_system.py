"""
Test script for the automated report generation system
"""
import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api/public-forms"
FORM_ID = "test-form-001"

def test_form_submission():
    """Test submitting a form"""
    print("Testing form submission...")
    
    form_data = {
        "form_id": FORM_ID,
        "form_title": "Customer Feedback Survey",
        "data": {
            "customer_name": "John Doe",
            "email": "john.doe@example.com",
            "rating": 5,
            "feedback": "Excellent service! Very satisfied with the product quality.",
            "category": "Product Quality",
            "would_recommend": True,
            "purchase_date": "2024-01-15",
            "age_group": "25-34",
            "location": "New York"
        },
        "source": "public"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/submit", json=form_data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Form submitted successfully: {result['submission_id']}")
            return result['submission_id']
        else:
            print(f"❌ Form submission failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error submitting form: {e}")
        return None

def test_batch_submission():
    """Test batch form submission"""
    print("\nTesting batch form submission...")
    
    batch_data = {
        "submissions": [
            {
                "form_id": FORM_ID,
                "data": {
                    "customer_name": "Alice Smith",
                    "email": "alice@example.com",
                    "rating": 4,
                    "feedback": "Good product, but delivery was slow.",
                    "category": "Delivery",
                    "would_recommend": True,
                    "purchase_date": "2024-01-10",
                    "age_group": "35-44",
                    "location": "California"
                }
            },
            {
                "form_id": FORM_ID,
                "data": {
                    "customer_name": "Bob Johnson",
                    "email": "bob@example.com",
                    "rating": 3,
                    "feedback": "Average experience. Room for improvement.",
                    "category": "Customer Service",
                    "would_recommend": False,
                    "purchase_date": "2024-01-12",
                    "age_group": "45-54",
                    "location": "Texas"
                }
            },
            {
                "form_id": FORM_ID,
                "data": {
                    "customer_name": "Carol Davis",
                    "email": "carol@example.com",
                    "rating": 5,
                    "feedback": "Outstanding! Will definitely buy again.",
                    "category": "Product Quality",
                    "would_recommend": True,
                    "purchase_date": "2024-01-14",
                    "age_group": "25-34",
                    "location": "Florida"
                }
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/batch-submit", json=batch_data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Batch submission successful: {len(result['submission_ids'])} submissions")
            return result['submission_ids']
        else:
            print(f"❌ Batch submission failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error with batch submission: {e}")
        return None

def test_trigger_report():
    """Test triggering report generation"""
    print("\nTesting report generation trigger...")
    
    report_data = {
        "form_id": FORM_ID,
        "title": f"Customer Feedback Analysis - {datetime.now().strftime('%Y-%m-%d')}",
        "include_charts": True,
        "analysis_type": "comprehensive"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-report", json=report_data)
        if response.status_code == 202:
            result = response.json()
            print(f"✅ Report generation triggered: {result['report_id']}")
            return result['report_id']
        else:
            print(f"❌ Report generation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error triggering report: {e}")
        return None

def test_get_reports():
    """Test fetching reports"""
    print("\nTesting report retrieval...")
    
    try:
        response = requests.get(f"{BASE_URL}/reports")
        if response.status_code == 200:
            reports = response.json()
            print(f"✅ Retrieved {len(reports)} reports")
            for report in reports:
                print(f"  - {report['title']} ({report['status']})")
            return reports
        else:
            print(f"❌ Failed to get reports: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting reports: {e}")
        return None

def test_report_status(report_id):
    """Test checking report status"""
    print(f"\nChecking report status for {report_id}...")
    
    max_attempts = 30  # Wait up to 5 minutes
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/reports/{report_id}")
            if response.status_code == 200:
                report = response.json()
                status = report['status']
                print(f"Report status: {status}")
                
                if status == 'completed':
                    print("✅ Report generation completed!")
                    print(f"  - Title: {report['title']}")
                    print(f"  - Submissions: {report['submission_count']}")
                    if report.get('ai_insights'):
                        print(f"  - AI Summary: {report['ai_insights']['summary'][:100]}...")
                    return report
                elif status == 'failed':
                    print(f"❌ Report generation failed: {report.get('error_message', 'Unknown error')}")
                    return report
                else:
                    print(f"⏳ Report still generating... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(10)
                    attempt += 1
            else:
                print(f"❌ Failed to check status: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error checking report status: {e}")
            return None
    
    print("❌ Report generation timed out")
    return None

def main():
    """Run the complete test suite"""
    print("🚀 Starting Automated Report Generation System Test\n")
    print("=" * 60)
    
    # Step 1: Submit individual form
    submission_id = test_form_submission()
    
    # Step 2: Submit batch forms
    batch_ids = test_batch_submission()
    
    # Step 3: Trigger report generation
    report_id = test_trigger_report()
    
    # Step 4: Check existing reports
    existing_reports = test_get_reports()
    
    # Step 5: Monitor report generation (if triggered)
    if report_id:
        final_report = test_report_status(report_id)
        
        if final_report and final_report['status'] == 'completed':
            print("\n🎉 Test completed successfully!")
            print("\nNext steps:")
            print("1. Check the generated Word document")
            print("2. Test the email functionality")
            print("3. Test the frontend React components")
        else:
            print("\n⚠️ Test completed with warnings - report generation may need debugging")
    else:
        print("\n⚠️ Test completed but report generation was not triggered")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"- Form submission: {'✅' if submission_id else '❌'}")
    print(f"- Batch submission: {'✅' if batch_ids else '❌'}")
    print(f"- Report trigger: {'✅' if report_id else '❌'}")
    print(f"- Report retrieval: {'✅' if existing_reports is not None else '❌'}")

if __name__ == "__main__":
    main()
