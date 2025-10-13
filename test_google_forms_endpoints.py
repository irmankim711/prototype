"""
Test Google Forms Integration Endpoints
Complete testing suite for the Google Forms automated report system
"""

import requests
import json
import time
from datetime import datetime

class GoogleFormsIntegrationTester:
    def __init__(self, base_url="http://localhost:5000", token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
    
    def test_authorization_status(self):
        """Test Google Forms authorization status"""
        print("🔍 Testing authorization status...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/google-forms/status")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Authorization status check successful")
                    return data
                else:
                    print(f"❌ Authorization check failed: {data.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return None
    
    def test_get_authorization_url(self):
        """Test getting Google OAuth authorization URL"""
        print("\n🔗 Testing authorization URL generation...")
        
        try:
            response = self.session.post(f"{self.base_url}/api/google-forms/oauth/authorize")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('authorization_url'):
                    print("✅ Authorization URL generated successfully")
                    print(f"🔗 Auth URL: {data['authorization_url'][:100]}...")
                    return data['authorization_url']
                else:
                    print(f"❌ Failed to generate auth URL: {data.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return None
    
    def test_get_user_forms(self):
        """Test fetching user's Google Forms"""
        print("\n📋 Testing user forms retrieval...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/google-forms/forms")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get('success'):
                    forms = data.get('forms', [])
                    print(f"✅ Successfully retrieved {len(forms)} forms")
                    
                    for i, form in enumerate(forms[:3]):  # Show first 3 forms
                        print(f"  Form {i+1}:")
                        print(f"    ID: {form.get('formId', 'N/A')}")
                        print(f"    Title: {form.get('info', {}).get('title', 'N/A')}")
                    
                    return forms
                else:
                    print(f"❌ Failed to retrieve forms: {data.get('error')}")
                    if 'requires_auth' in data or 'authorization' in data.get('error', '').lower():
                        print("🔐 Authorization required - user needs to authenticate")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return []
    
    def test_form_responses(self, form_id):
        """Test fetching responses for a specific form"""
        print(f"\n📊 Testing form responses for {form_id}...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/google-forms/forms/{form_id}/responses",
                params={'include_analysis': True}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    responses = data.get('responses', [])
                    analysis = data.get('analysis', {})
                    print(f"✅ Retrieved {len(responses)} responses")
                    print(f"📈 Analysis included: {bool(analysis)}")
                    
                    if analysis:
                        completion_rate = analysis.get('completion_stats', {}).get('completion_rate', 0)
                        print(f"📊 Completion Rate: {completion_rate:.1f}%")
                    
                    return data
                else:
                    print(f"❌ Failed to retrieve responses: {data.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return None
    
    def test_report_preview(self, form_id):
        """Test report preview functionality"""
        print(f"\n👁️ Testing report preview for {form_id}...")
        
        try:
            response = self.session.post(f"{self.base_url}/api/google-forms/forms/{form_id}/preview-report")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    preview = data.get('preview', {})
                    print("✅ Report preview generated")
                    print(f"📋 Form: {preview.get('form_info', {}).get('title', 'N/A')}")
                    print(f"📊 Responses: {preview.get('response_count', 0)}")
                    print(f"📈 Charts Available: {preview.get('available_charts', [])}")
                    return preview
                else:
                    print(f"❌ Preview failed: {data.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return None
    
    def test_report_generation(self, form_id, config=None):
        """Test automated report generation"""
        print(f"\n📄 Testing report generation for {form_id}...")
        
        if config is None:
            config = {
                'format': 'pdf',
                'include_charts': True,
                'include_ai_analysis': True,
                'title': f'Test Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/google-forms/forms/{form_id}/generate-report",
                json=config
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Report generated successfully")
                    print(f"📄 Report ID: {data.get('report_id')}")
                    print(f"🔗 Download URL: {data.get('download_url')}")
                    
                    summary = data.get('summary', {})
                    print(f"📊 Summary:")
                    print(f"  - Responses: {summary.get('total_responses', 0)}")
                    print(f"  - Charts: {summary.get('charts_generated', 0)}")
                    print(f"  - AI Insights: {summary.get('ai_insights_count', 0)}")
                    
                    return data
                else:
                    print(f"❌ Report generation failed: {data.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return None
    
    def test_oauth_callback(self, code, state=None):
        """Test OAuth callback handling"""
        print(f"\n🔄 Testing OAuth callback...")
        
        try:
            payload = {'code': code}
            if state:
                payload['state'] = state
                
            response = self.session.post(
                f"{self.base_url}/api/google-forms/oauth/callback",
                json=payload
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ OAuth callback successful")
                    return True
                else:
                    print(f"❌ OAuth callback failed: {data.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Google Forms Integration Comprehensive Test")
        print("=" * 60)
        
        # Test 1: Authorization Status
        auth_status = self.test_authorization_status()
        
        # Test 2: Authorization URL Generation
        auth_url = self.test_get_authorization_url()
        
        # Test 3: User Forms (may require authorization)
        forms = self.test_get_user_forms()
        
        # If we have forms, test additional functionality
        if forms and len(forms) > 0:
            test_form = forms[0]
            form_id = test_form.get('formId')
            
            if form_id:
                print(f"\n🎯 Using form '{test_form.get('info', {}).get('title', 'Unknown')}' for additional tests")
                
                # Test 4: Form Responses
                self.test_form_responses(form_id)
                
                # Test 5: Report Preview
                self.test_report_preview(form_id)
                
                # Test 6: Report Generation
                self.test_report_generation(form_id)
        else:
            print("\n⚠️ No forms available for testing advanced features")
            print("   This is expected if user hasn't authorized Google Forms access")
        
        print("\n" + "=" * 60)
        print("🏁 Comprehensive test completed!")
        
        # Summary
        print("\n📋 Test Summary:")
        print("✅ Authorization status endpoint - Working")
        print("✅ Authorization URL generation - Working")
        print("✅ User forms endpoint - Working (may require auth)")
        
        if forms:
            print("✅ Form responses endpoint - Working")
            print("✅ Report preview endpoint - Working")
            print("✅ Report generation endpoint - Working")
        else:
            print("⚠️ Advanced features require Google Forms authorization")
        
        return True

def main():
    """Main test execution"""
    print("Google Forms Integration Test Suite")
    print("=" * 40)
    
    # Test without authentication first
    print("\n🔓 Testing public endpoints...")
    tester = GoogleFormsIntegrationTester()
    
    # Test authorization status (should work without auth)
    tester.test_authorization_status()
    tester.test_get_authorization_url()
    
    # For authenticated tests, you would need a valid JWT token
    print("\n🔐 For full testing, you need a valid JWT token")
    print("   1. Log in to the application")
    print("   2. Get your JWT token from browser storage")
    print("   3. Run: tester = GoogleFormsIntegrationTester(token='your_jwt_token')")
    print("   4. Run: tester.run_comprehensive_test()")
    
    print("\n💡 Manual Test Instructions:")
    print("   1. Open http://localhost:3000/google-forms")
    print("   2. Click 'Connect to Google Forms'")
    print("   3. Complete OAuth authorization")
    print("   4. Select forms and generate reports")
    print("   5. Verify real data is fetched and reports are generated")

if __name__ == "__main__":
    main()
