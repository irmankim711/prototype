"""
Unit Tests for Real Data Integration
Tests Google Forms and Microsoft Graph services with real API integration
"""
import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import our services
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.google_forms_service import ProductionGoogleFormsService
from app.services.microsoft_graph_service_real import RealMicrosoftGraphService

class TestRealGoogleFormsService:
    """Test Google Forms service with real API integration"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        self.env_vars = {
            'GOOGLE_CLIENT_ID': 'test_client_id.apps.googleusercontent.com',
            'GOOGLE_CLIENT_SECRET': 'test_client_secret',
            'GOOGLE_PROJECT_ID': 'test_project',
            'GOOGLE_REDIRECT_URI': 'http://localhost:5000/api/google-forms/callback'
        }
        
        with patch.dict(os.environ, self.env_vars):
            self.service = ProductionGoogleFormsService()
    
    def test_service_initialization(self):
        """Test service initializes with environment variables"""
        with patch.dict(os.environ, self.env_vars):
            service = ProductionGoogleFormsService()
            assert service.client_id == 'test_client_id.apps.googleusercontent.com'
            assert service.client_secret == 'test_client_secret'
            assert service.project_id == 'test_project'
    
    def test_missing_credentials_raises_error(self):
        """Test that missing credentials raise proper error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Google OAuth configuration"):
                ProductionGoogleFormsService()
    
    def test_credentials_configuration(self):
        """Test credentials configuration generation"""
        config = self.service._get_credentials_config()
        
        assert 'installed' in config
        assert config['installed']['client_id'] == 'test_client_id.apps.googleusercontent.com'
        assert config['installed']['client_secret'] == 'test_client_secret'
        assert 'auth_uri' in config['installed']
        assert 'token_uri' in config['installed']
    
    def test_authorization_url_generation(self):
        """Test OAuth authorization URL generation"""
        user_id = 'test_user_123'
        
        with patch.object(self.service, '_store_oauth_state') as mock_store:
            with patch('app.services.google_forms_service.Flow') as mock_flow_class:
                mock_flow = Mock()
                mock_flow.authorization_url.return_value = ('https://accounts.google.com/oauth/authorize?...', 'test_state')
                mock_flow_class.from_client_config.return_value = mock_flow
                
                auth_url = self.service.get_authorization_url(user_id)
                
                assert auth_url.startswith('https://accounts.google.com/oauth/authorize')
                mock_store.assert_called_once()
                mock_flow.authorization_url.assert_called_once()
    
    def test_oauth_state_storage_and_verification(self):
        """Test OAuth state storage and verification"""
        user_id = 'test_user_123'
        state = 'test_state_value'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the tokens directory
            with patch('os.path.join') as mock_join:
                mock_join.return_value = os.path.join(temp_dir, f"user_{user_id}_oauth_state.json")
                
                # Store state
                self.service._store_oauth_state(user_id, state)
                
                # Verify state (should be valid)
                assert self.service._verify_oauth_state(user_id, state) == True
                
                # Verify with wrong state (should be invalid)
                assert self.service._verify_oauth_state(user_id, 'wrong_state') == False
    
    @patch('app.services.google_forms_service.build')
    def test_get_user_forms_real_api(self, mock_build):
        """Test fetching real user forms from Google API"""
        user_id = 'test_user_123'
        
        # Mock credentials
        mock_credentials = Mock()
        with patch.object(self.service, '_get_user_credentials', return_value=mock_credentials):
            
            # Mock Drive API response
            mock_drive_service = Mock()
            mock_forms_service = Mock()
            
            mock_build.side_effect = [mock_drive_service, mock_forms_service]
            
            # Mock Drive API list response
            mock_drive_service.files().list().execute.return_value = {
                'files': [
                    {
                        'id': 'form_123',
                        'name': 'Test Form',
                        'createdTime': '2025-01-01T00:00:00Z',
                        'modifiedTime': '2025-01-01T12:00:00Z',
                        'webViewLink': 'https://docs.google.com/forms/d/form_123/edit'
                    }
                ]
            }
            
            # Mock Forms API get response
            mock_forms_service.forms().get().execute.return_value = {
                'info': {
                    'title': 'Test Form',
                    'description': 'A test form'
                },
                'responderUri': 'https://docs.google.com/forms/d/form_123/viewform',
                'items': [{'itemId': 'item1'}, {'itemId': 'item2'}],
                'settings': {}
            }
            
            # Mock responses count
            mock_forms_service.forms().responses().list().execute.return_value = {
                'responses': [{'responseId': 'resp1'}, {'responseId': 'resp2'}]
            }
            
            forms = self.service.get_user_forms(user_id)
            
            assert len(forms) == 1
            assert forms[0]['id'] == 'form_123'
            assert forms[0]['title'] == 'Test Form'
            assert forms[0]['type'] == 'google_form'
            assert forms[0]['response_count'] == 2
            assert forms[0]['question_count'] == 2
    
    @patch('app.services.google_forms_service.build')
    def test_get_form_responses_real_api(self, mock_build):
        """Test fetching real form responses from Google API"""
        user_id = 'test_user_123'
        form_id = 'form_123'
        
        # Mock credentials
        mock_credentials = Mock()
        with patch.object(self.service, '_get_user_credentials', return_value=mock_credentials):
            
            mock_forms_service = Mock()
            mock_build.return_value = mock_forms_service
            
            # Mock form structure
            mock_forms_service.forms().get().execute.return_value = {
                'info': {
                    'title': 'Test Form',
                    'description': 'Test Description'
                },
                'responderUri': 'https://docs.google.com/forms/d/form_123/viewform',
                'items': [
                    {
                        'itemId': 'item1',
                        'questionItem': {
                            'question': {
                                'questionTitle': 'What is your name?',
                                'textQuestion': {}
                            }
                        }
                    }
                ]
            }
            
            # Mock responses
            mock_forms_service.forms().responses().list().execute.return_value = {
                'responses': [
                    {
                        'responseId': 'resp_123',
                        'createTime': '2025-01-01T10:00:00Z',
                        'lastSubmittedTime': '2025-01-01T10:05:00Z',
                        'answers': {
                            'item1': {
                                'textAnswers': {
                                    'answers': [{'value': 'John Doe'}]
                                }
                            }
                        }
                    }
                ]
            }
            
            result = self.service.get_form_responses(user_id, form_id, include_analysis=True)
            
            assert result['success'] == True
            assert result['form_info']['id'] == form_id
            assert result['form_info']['title'] == 'Test Form'
            assert len(result['responses']) == 1
            assert result['responses'][0]['response_id'] == 'resp_123'
            assert result['responses'][0]['answers']['What is your name?'] == 'John Doe'
            assert result['data_source'] == 'google_forms_api'
    
    def test_credentials_storage_and_retrieval(self):
        """Test credentials storage and retrieval"""
        user_id = 'test_user_123'
        
        # Mock credentials object
        mock_credentials = Mock()
        mock_credentials.token = 'test_access_token'
        mock_credentials.refresh_token = 'test_refresh_token'
        mock_credentials.token_uri = 'https://oauth2.googleapis.com/token'
        mock_credentials.client_id = 'test_client_id'
        mock_credentials.client_secret = 'test_client_secret'
        mock_credentials.scopes = ['scope1', 'scope2']
        mock_credentials.expiry = datetime.utcnow() + timedelta(hours=1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the tokens directory
            with patch('os.path.join') as mock_join:
                token_path = os.path.join(temp_dir, f"user_{user_id}_google_token.json")
                mock_join.return_value = token_path
                
                # Store credentials
                self.service._store_user_credentials(user_id, mock_credentials)
                
                # Verify file was created
                assert os.path.exists(token_path)
                
                # Verify content
                with open(token_path, 'r') as f:
                    stored_data = json.load(f)
                
                assert stored_data['token'] == 'test_access_token'
                assert stored_data['refresh_token'] == 'test_refresh_token'
                assert stored_data['client_id'] == 'test_client_id'

class TestRealMicrosoftGraphService:
    """Test Microsoft Graph service with real API integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.env_vars = {
            'MICROSOFT_CLIENT_ID': 'test_ms_client_id',
            'MICROSOFT_CLIENT_SECRET': 'test_ms_client_secret',
            'MICROSOFT_TENANT_ID': 'test_tenant_id',
            'MICROSOFT_REDIRECT_URI': 'http://localhost:5000/api/microsoft-forms/callback'
        }
        
        with patch.dict(os.environ, self.env_vars):
            with patch('app.services.microsoft_graph_service_real.msal.ConfidentialClientApplication'):
                self.service = RealMicrosoftGraphService()
    
    def test_service_initialization(self):
        """Test Microsoft Graph service initialization"""
        with patch.dict(os.environ, self.env_vars):
            with patch('app.services.microsoft_graph_service_real.msal.ConfidentialClientApplication'):
                service = RealMicrosoftGraphService()
                assert service.client_id == 'test_ms_client_id'
                assert service.client_secret == 'test_ms_client_secret'
                assert service.tenant_id == 'test_tenant_id'
    
    def test_missing_microsoft_credentials_raises_error(self):
        """Test that missing Microsoft credentials raise proper error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Microsoft Graph configuration"):
                RealMicrosoftGraphService()
    
    def test_authorization_url_generation(self):
        """Test Microsoft Graph authorization URL generation"""
        user_id = 'test_user_123'
        
        mock_app = Mock()
        mock_app.get_authorization_request_url.return_value = 'https://login.microsoftonline.com/oauth/authorize?...'
        
        with patch.object(self.service, 'app', mock_app):
            auth_url = self.service.get_authorization_url(user_id)
            
            assert auth_url.startswith('https://login.microsoftonline.com/oauth/authorize')
            mock_app.get_authorization_request_url.assert_called_once()
    
    @patch('app.services.microsoft_graph_service_real.requests.get')
    def test_get_user_forms_real_api(self, mock_get):
        """Test fetching real Microsoft Forms"""
        user_id = 'test_user_123'
        
        # Mock credentials
        mock_credentials = {
            'access_token': 'test_access_token',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        with patch.object(self.service, '_get_user_credentials', return_value=mock_credentials):
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'value': [
                    {
                        'id': 'ms_form_123',
                        'name': 'Microsoft Test Form',
                        'createdDateTime': '2025-01-01T00:00:00Z',
                        'lastModifiedDateTime': '2025-01-01T12:00:00Z',
                        'webUrl': 'https://forms.office.com/r/form_123'
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            # Mock form details
            with patch.object(self.service, '_get_form_details', return_value={'description': 'Test description'}):
                forms = self.service.get_user_forms(user_id)
                
                assert len(forms) == 1
                assert forms[0]['id'] == 'ms_form_123'
                assert forms[0]['title'] == 'Microsoft Test Form'
                assert forms[0]['type'] == 'microsoft_form'
    
    @patch('app.services.microsoft_graph_service_real.requests.get')
    def test_get_form_responses_real_api(self, mock_get):
        """Test fetching real Microsoft Form responses"""
        user_id = 'test_user_123'
        form_id = 'ms_form_123'
        
        # Mock credentials
        mock_credentials = {
            'access_token': 'test_access_token',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        with patch.object(self.service, '_get_user_credentials', return_value=mock_credentials):
            # Mock API responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'values': [
                    ['Name', 'Email', 'Response'],  # Headers
                    ['John Doe', 'john@example.com', 'Great service'],  # Data
                    ['Jane Smith', 'jane@example.com', 'Very helpful']
                ]
            }
            mock_get.return_value = mock_response
            
            # Mock form details
            with patch.object(self.service, '_get_form_details', return_value={'name': 'Test Form'}):
                result = self.service.get_form_responses(user_id, form_id)
                
                assert result['success'] == True
                assert result['form_info']['id'] == form_id
                assert len(result['responses']) == 2
                assert result['responses'][0]['answers']['Name'] == 'John Doe'
                assert result['responses'][0]['answers']['Email'] == 'john@example.com'
                assert result['data_source'] == 'microsoft_graph_api'

class TestDataMappingAndTemplateIntegration:
    """Test data mapping to Temp1.docx placeholders"""
    
    def test_google_forms_template_mapping(self):
        """Test mapping Google Forms data to template placeholders"""
        # Sample real Google Forms response data
        responses = [
            {
                'response_id': 'resp_1',
                'create_time': '2025-01-01T10:00:00Z',
                'answers': {
                    'What is your name?': 'John Doe',
                    'What is your email?': 'john@example.com',
                    'Rate your satisfaction (1-5)': '4',
                    'Any additional comments?': 'Great service!'
                }
            },
            {
                'response_id': 'resp_2',
                'create_time': '2025-01-01T11:00:00Z',
                'answers': {
                    'What is your name?': 'Jane Smith',
                    'What is your email?': 'jane@example.com',
                    'Rate your satisfaction (1-5)': '5',
                    'Any additional comments?': 'Excellent experience!'
                }
            }
        ]
        
        form_info = {
            'title': 'Customer Satisfaction Survey',
            'description': 'Quarterly customer feedback'
        }
        
        analysis = {
            'completion_stats': {
                'total_responses': 2,
                'completion_rate': 100.0
            }
        }
        
        # Initialize service
        with patch.dict(os.environ, {
            'GOOGLE_CLIENT_ID': 'test_id',
            'GOOGLE_CLIENT_SECRET': 'test_secret'
        }):
            service = ProductionGoogleFormsService()
            
            template_data = service._map_responses_to_template(responses, form_info, analysis)
            
            # Test template mapping
            assert template_data['program']['title'] == 'Customer Satisfaction Survey'
            assert template_data['program']['total_participants'] == '2'
            assert len(template_data['participants']) == 2
            assert template_data['participants'][0]['name'] == 'John Doe'
            assert template_data['participants'][0]['bil'] == '1'
            assert template_data['participants'][1]['name'] == 'Jane Smith'
            assert template_data['response_statistics']['total_responses'] == 2
    
    def test_microsoft_forms_template_mapping(self):
        """Test mapping Microsoft Forms data to template placeholders"""
        # Sample Microsoft Forms response data
        responses = [
            {
                'response_id': 'ms_resp_1',
                'create_time': '2025-01-01T10:00:00Z',
                'answers': {
                    'Name': 'Alice Johnson',
                    'Email': 'alice@company.com',
                    'Department': 'Engineering',
                    'Satisfaction Rating': '5'
                }
            }
        ]
        
        form_info = {
            'title': 'Employee Feedback Form',
            'type': 'microsoft_form'
        }
        
        # Initialize service
        with patch.dict(os.environ, {
            'MICROSOFT_CLIENT_ID': 'test_id',
            'MICROSOFT_CLIENT_SECRET': 'test_secret',
            'MICROSOFT_TENANT_ID': 'test_tenant'
        }):
            with patch('app.services.microsoft_graph_service_real.msal.ConfidentialClientApplication'):
                service = RealMicrosoftGraphService()
                
                template_data = service.map_responses_to_template(responses, form_info)
                
                # Test template mapping
                assert template_data['program']['title'] == 'Employee Feedback Form'
                assert template_data['program']['source'] == 'microsoft_forms'
                assert len(template_data['participants']) == 1
                assert template_data['participants'][0]['name'] == 'Alice Johnson'
                assert template_data['participants'][0]['email'] == 'alice@company.com'

def run_integration_tests():
    """Run integration tests with real API endpoints (if credentials available)"""
    print("🧪 Running Real Data Integration Tests")
    print("=" * 50)
    
    # Check if real credentials are available
    google_creds_available = all([
        os.getenv('GOOGLE_CLIENT_ID'),
        os.getenv('GOOGLE_CLIENT_SECRET')
    ])
    
    microsoft_creds_available = all([
        os.getenv('MICROSOFT_CLIENT_ID'),
        os.getenv('MICROSOFT_CLIENT_SECRET'),
        os.getenv('MICROSOFT_TENANT_ID')
    ])
    
    print(f"Google Credentials Available: {'✅' if google_creds_available else '❌'}")
    print(f"Microsoft Credentials Available: {'✅' if microsoft_creds_available else '❌'}")
    
    if google_creds_available:
        print("\n🔍 Testing Google Forms Service...")
        try:
            service = ProductionGoogleFormsService()
            print("✅ Google Forms service initialized successfully")
        except Exception as e:
            print(f"❌ Google Forms service initialization failed: {e}")
    
    if microsoft_creds_available:
        print("\n🔍 Testing Microsoft Graph Service...")
        try:
            service = RealMicrosoftGraphService()
            print("✅ Microsoft Graph service initialized successfully")
        except Exception as e:
            print(f"❌ Microsoft Graph service initialization failed: {e}")
    
    print("\n✅ Integration tests completed!")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
    
    # Run integration tests if credentials available
    run_integration_tests()
