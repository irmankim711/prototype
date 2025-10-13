"""
Unit Tests for Enhanced Google Forms Data Source Service

Tests the enhanced functionality including:
- Form responses with metadata
- Form schema and question types retrieval
- Response filtering and pagination for large datasets
- Caching for form metadata
- Error handling and retry logic
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.services.data_sources.google_forms_service import (
    GoogleFormsDataService, 
    FormSchema, 
    ResponseFilter
)


class TestEnhancedGoogleFormsService:
    """Test suite for enhanced Google Forms service functionality"""

    def setup_method(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_vars = {
            'GOOGLE_CLIENT_ID': 'test_client_id.apps.googleusercontent.com',
            'GOOGLE_CLIENT_SECRET': 'test_client_secret',
            'GOOGLE_REDIRECT_URI': 'http://localhost:5000/api/v1/auth/google/callback'
        }
        
        # Create service instance
        with patch.dict(os.environ, self.env_vars):
            self.service = GoogleFormsDataService()
        
        # Mock credentials
        self.mock_credentials = Mock(spec=Credentials)
        self.mock_credentials.token = 'test_access_token'
        self.mock_credentials.refresh_token = 'test_refresh_token'
        self.mock_credentials.expired = False
        self.mock_credentials.expiry = datetime.utcnow() + timedelta(hours=1)
        
        # Test data
        self.test_form_id = 'test_form_123'
        self.test_user_id = 'test_user_456'
        
        self.sample_form_data = {
            'formId': self.test_form_id,
            'info': {
                'title': 'Test Form',
                'description': 'A test form for unit testing'
            },
            'items': [
                {
                    'itemId': 'question_1',
                    'questionItem': {
                        'question': {
                            'questionTitle': 'What is your name?',
                            'required': True,
                            'textQuestion': {'paragraph': False}
                        }
                    }
                },
                {
                    'itemId': 'question_2',
                    'questionItem': {
                        'question': {
                            'questionTitle': 'Rate your experience',
                            'required': False,
                            'scaleQuestion': {
                                'low': 1,
                                'high': 5,
                                'lowLabel': 'Poor',
                                'highLabel': 'Excellent'
                            }
                        }
                    }
                }
            ],
            'settings': {'quizSettings': {'isQuiz': False}},
            'responderUri': 'https://docs.google.com/forms/d/test_form_123/viewform'
        }
        
        self.sample_responses = [
            {
                'responseId': 'response_1',
                'createTime': '2024-01-15T10:30:00Z',
                'lastSubmittedTime': '2024-01-15T10:30:00Z',
                'answers': {
                    'question_1': {
                        'textAnswers': {
                            'answers': [{'value': 'John Doe'}]
                        }
                    },
                    'question_2': {
                        'textAnswers': {
                            'answers': [{'value': '4'}]
                        }
                    }
                }
            },
            {
                'responseId': 'response_2',
                'createTime': '2024-01-15T11:00:00Z',
                'lastSubmittedTime': '2024-01-15T11:00:00Z',
                'answers': {
                    'question_1': {
                        'textAnswers': {
                            'answers': [{'value': 'Jane Smith'}]
                        }
                    },
                    'question_2': {
                        'textAnswers': {
                            'answers': [{'value': '5'}]
                        }
                    }
                }
            }
        ]

    def test_service_initialization(self):
        """Test service initialization with proper configuration"""
        with patch.dict(os.environ, self.env_vars):
            service = GoogleFormsDataService()
            
            assert service.enabled is True
            assert service.service_type == 'google_forms'
            assert service.client_id == self.env_vars['GOOGLE_CLIENT_ID']
            assert service.client_secret == self.env_vars['GOOGLE_CLIENT_SECRET']
            assert len(service.scopes) == 3

    def test_service_initialization_missing_credentials(self):
        """Test service initialization with missing credentials"""
        with patch.dict(os.environ, {}, clear=True):
            service = GoogleFormsDataService()
            
            assert service.enabled is False

    def test_supports_source(self):
        """Test source ID support validation"""
        assert self.service.supports_source('google-forms') is True
        assert self.service.supports_source('gform_123') is True
        assert self.service.supports_source('invalid_source') is False

    @patch('app.services.data_sources.google_forms_service.build')
    def test_get_form_schema_success(self, mock_build):
        """Test successful form schema retrieval"""
        # Mock Google API service
        mock_forms_service = Mock()
        mock_build.return_value = mock_forms_service
        mock_forms_service.forms().get().execute.return_value = self.sample_form_data
        
        # Mock credentials retrieval
        with patch.object(self.service, '_get_user_credentials', return_value=self.mock_credentials):
            response = self.service.get_form_schema(self.test_user_id, self.test_form_id)
        
        assert response.success is True
        assert response.data['form_id'] == self.test_form_id
        assert response.data['title'] == 'Test Form'
        assert len(response.data['questions']) == 2
        
        # Verify question parsing
        questions = response.data['questions']
        assert questions[0]['title'] == 'What is your name?'
        assert questions[0]['question_type'] == 'text'
        assert questions[0]['required'] is True
        
        assert questions[1]['title'] == 'Rate your experience'
        assert questions[1]['question_type'] == 'scale'
        assert questions[1]['low'] == 1
        assert questions[1]['high'] == 5

    def test_get_form_schema_no_credentials(self):
        """Test form schema retrieval without credentials"""
        with patch.object(self.service, '_get_user_credentials', return_value=None):
            response = self.service.get_form_schema(self.test_user_id, self.test_form_id)
        
        assert response.success is False
        assert response.error['code'] == 'AUTHENTICATION_REQUIRED'

    @patch('app.services.data_sources.google_forms_service.build')
    def test_get_form_responses_paginated_success(self, mock_build):
        """Test successful paginated form responses retrieval"""
        # Mock Google API service
        mock_forms_service = Mock()
        mock_build.return_value = mock_forms_service
        
        # Mock form schema call
        mock_forms_service.forms().get().execute.return_value = self.sample_form_data
        
        # Mock responses call
        mock_forms_service.forms().responses().list().execute.return_value = {
            'responses': self.sample_responses,
            'nextPageToken': 'next_page_token_123'
        }
        
        # Mock credentials retrieval
        with patch.object(self.service, '_get_user_credentials', return_value=self.mock_credentials):
            response = self.service.get_form_responses_paginated(
                self.test_user_id, 
                self.test_form_id, 
                page_size=50
            )
        
        assert response.success is True
        assert response.data['form_id'] == self.test_form_id
        assert response.data['form_title'] == 'Test Form'
        assert len(response.data['responses']) == 2
        assert response.data['has_more'] is True
        assert response.data['next_page_token'] == 'next_page_token_123'
        
        # Verify response enhancement
        responses = response.data['responses']
        assert responses[0]['response_id'] == 'response_1'
        assert 'What is your name?' in responses[0]['answers']
        assert responses[0]['answers']['What is your name?'] == 'John Doe'

    @patch('app.services.data_sources.google_forms_service.build')
    def test_get_data_with_filtering(self, mock_build):
        """Test data retrieval with response filtering"""
        # Mock Google API service
        mock_forms_service = Mock()
        mock_build.return_value = mock_forms_service
        
        # Mock form schema call
        mock_forms_service.forms().get().execute.return_value = self.sample_form_data
        
        # Mock responses call
        mock_forms_service.forms().responses().list().execute.return_value = {
            'responses': self.sample_responses
        }
        
        # Mock credentials retrieval
        with patch.object(self.service, '_get_user_credentials', return_value=self.mock_credentials):
            # Test with date filtering
            params = {
                'user_id': self.test_user_id,
                'form_id': self.test_form_id,
                'start_date': '2024-01-15T10:00:00Z',
                'end_date': '2024-01-15T12:00:00Z',
                'limit': 10,
                'include_metadata': True
            }
            
            response = self.service.get_data(f'gform_{self.test_form_id}', params)
        
        assert response.success is True
        assert len(response.data['responses']) == 2

    def test_build_response_filter(self):
        """Test response filter building from parameters"""
        params = {
            'start_date': '2024-01-15T10:00:00Z',
            'end_date': '2024-01-15T12:00:00Z',
            'limit': 50,
            'offset': 10,
            'question_filters': {'question_1': 'John Doe'},
            'response_ids': ['response_1', 'response_2']
        }
        
        response_filter = self.service._build_response_filter(params)
        
        assert response_filter.start_date == datetime.fromisoformat('2024-01-15T10:00:00+00:00')
        assert response_filter.end_date == datetime.fromisoformat('2024-01-15T12:00:00+00:00')
        assert response_filter.limit == 50
        assert response_filter.offset == 10
        assert response_filter.question_filters == {'question_1': 'John Doe'}
        assert response_filter.response_ids == ['response_1', 'response_2']

    def test_filter_responses_by_date(self):
        """Test response filtering by date range"""
        response_filter = ResponseFilter(
            start_date=datetime.fromisoformat('2024-01-15T10:45:00+00:00'),
            end_date=datetime.fromisoformat('2024-01-15T11:30:00+00:00')
        )
        
        filtered = self.service._filter_responses(self.sample_responses, response_filter)
        
        # Should only include response_2 (11:00:00)
        assert len(filtered) == 1
        assert filtered[0]['responseId'] == 'response_2'

    def test_filter_responses_by_question(self):
        """Test response filtering by question answers"""
        response_filter = ResponseFilter(
            question_filters={'question_1': 'John Doe'}
        )
        
        # Mock answer extraction
        with patch.object(self.service, '_extract_answer_value', side_effect=['John Doe', 'Jane Smith']):
            filtered = self.service._filter_responses(self.sample_responses, response_filter)
        
        # Should only include response_1
        assert len(filtered) == 1
        assert filtered[0]['responseId'] == 'response_1'

    def test_parse_question_item_text(self):
        """Test parsing of text question items"""
        item = {
            'itemId': 'question_1',
            'description': 'Enter your full name',
            'questionItem': {
                'question': {
                    'questionTitle': 'What is your name?',
                    'required': True,
                    'textQuestion': {'paragraph': False}
                }
            }
        }
        
        parsed = self.service._parse_question_item(item)
        
        assert parsed['item_id'] == 'question_1'
        assert parsed['title'] == 'What is your name?'
        assert parsed['description'] == 'Enter your full name'
        assert parsed['required'] is True
        assert parsed['question_type'] == 'text'
        assert parsed['paragraph'] is False

    def test_parse_question_item_choice(self):
        """Test parsing of choice question items"""
        item = {
            'itemId': 'question_2',
            'questionItem': {
                'question': {
                    'questionTitle': 'Choose your favorite color',
                    'required': False,
                    'choiceQuestion': {
                        'type': 'RADIO',
                        'options': [
                            {'value': 'Red'},
                            {'value': 'Blue'},
                            {'value': 'Green'}
                        ],
                        'shuffle': True
                    }
                }
            }
        }
        
        parsed = self.service._parse_question_item(item)
        
        assert parsed['question_type'] == 'choice'
        assert parsed['choice_type'] == 'RADIO'
        assert parsed['options'] == ['Red', 'Blue', 'Green']
        assert parsed['shuffle'] is True

    def test_parse_question_item_scale(self):
        """Test parsing of scale question items"""
        item = {
            'itemId': 'question_3',
            'questionItem': {
                'question': {
                    'questionTitle': 'Rate your satisfaction',
                    'required': True,
                    'scaleQuestion': {
                        'low': 1,
                        'high': 10,
                        'lowLabel': 'Very Dissatisfied',
                        'highLabel': 'Very Satisfied'
                    }
                }
            }
        }
        
        parsed = self.service._parse_question_item(item)
        
        assert parsed['question_type'] == 'scale'
        assert parsed['low'] == 1
        assert parsed['high'] == 10
        assert parsed['low_label'] == 'Very Dissatisfied'
        assert parsed['high_label'] == 'Very Satisfied'

    def test_parse_question_item_file_upload(self):
        """Test parsing of file upload question items"""
        item = {
            'itemId': 'question_4',
            'questionItem': {
                'question': {
                    'questionTitle': 'Upload your resume',
                    'required': True,
                    'fileUploadQuestion': {
                        'folderId': 'folder_123',
                        'maxFiles': 3,
                        'maxFileSize': 5242880,  # 5MB
                        'types': ['PDF', 'DOC', 'DOCX']
                    }
                }
            }
        }
        
        parsed = self.service._parse_question_item(item)
        
        assert parsed['question_type'] == 'file_upload'
        assert parsed['folder_id'] == 'folder_123'
        assert parsed['max_files'] == 3
        assert parsed['max_file_size'] == 5242880
        assert parsed['types'] == ['PDF', 'DOC', 'DOCX']

    def test_determine_question_type(self):
        """Test question type determination"""
        # Text question
        text_question = {'textQuestion': {'paragraph': False}}
        assert self.service._determine_question_type(text_question) == 'text'
        
        # Choice question
        choice_question = {'choiceQuestion': {'type': 'RADIO'}}
        assert self.service._determine_question_type(choice_question) == 'choice'
        
        # Scale question
        scale_question = {'scaleQuestion': {'low': 1, 'high': 5}}
        assert self.service._determine_question_type(scale_question) == 'scale'
        
        # Date question
        date_question = {'dateQuestion': {'includeTime': False}}
        assert self.service._determine_question_type(date_question) == 'date'
        
        # Time question
        time_question = {'timeQuestion': {'duration': False}}
        assert self.service._determine_question_type(time_question) == 'time'
        
        # File upload question
        file_question = {'fileUploadQuestion': {'maxFiles': 1}}
        assert self.service._determine_question_type(file_question) == 'file_upload'
        
        # Unknown question
        unknown_question = {'unknownQuestion': {}}
        assert self.service._determine_question_type(unknown_question) == 'unknown'

    def test_parse_answer_enhanced_text(self):
        """Test enhanced answer parsing for text responses"""
        answer_data = {
            'textAnswers': {
                'answers': [{'value': 'This is a text response'}]
            }
        }
        question_info = {'question_type': 'text', 'paragraph': False}
        
        parsed = self.service._parse_answer_enhanced(answer_data, question_info)
        assert parsed == 'This is a text response'

    def test_parse_answer_enhanced_paragraph(self):
        """Test enhanced answer parsing for paragraph responses"""
        answer_data = {
            'textAnswers': {
                'answers': [
                    {'value': 'Line 1'},
                    {'value': 'Line 2'},
                    {'value': 'Line 3'}
                ]
            }
        }
        question_info = {'question_type': 'text', 'paragraph': True}
        
        parsed = self.service._parse_answer_enhanced(answer_data, question_info)
        assert parsed == 'Line 1\nLine 2\nLine 3'

    def test_parse_answer_enhanced_file_upload(self):
        """Test enhanced answer parsing for file upload responses"""
        answer_data = {
            'fileUploadAnswers': {
                'answers': [
                    {
                        'fileId': 'file_123',
                        'fileName': 'resume.pdf',
                        'mimeType': 'application/pdf'
                    },
                    {
                        'fileId': 'file_456',
                        'fileName': 'cover_letter.docx',
                        'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    }
                ]
            }
        }
        question_info = {'question_type': 'file_upload'}
        
        parsed = self.service._parse_answer_enhanced(answer_data, question_info)
        
        assert len(parsed) == 2
        assert parsed[0]['file_id'] == 'file_123'
        assert parsed[0]['file_name'] == 'resume.pdf'
        assert parsed[0]['mime_type'] == 'application/pdf'
        assert parsed[1]['file_id'] == 'file_456'

    def test_enhance_response_data(self):
        """Test response data enhancement with metadata"""
        response = self.sample_responses[0]
        schema = FormSchema(
            form_id=self.test_form_id,
            title='Test Form',
            description='Test Description',
            questions=[
                {
                    'item_id': 'question_1',
                    'title': 'What is your name?',
                    'question_type': 'text'
                },
                {
                    'item_id': 'question_2',
                    'title': 'Rate your experience',
                    'question_type': 'scale'
                }
            ],
            settings={}
        )
        params = {'include_metadata': True}
        
        enhanced = self.service._enhance_response_data(response, schema, params)
        
        assert enhanced['response_id'] == 'response_1'
        assert enhanced['create_time'] == '2024-01-15T10:30:00Z'
        assert 'What is your name?' in enhanced['answers']
        assert enhanced['answers']['What is your name?'] == 'John Doe'
        assert 'metadata' in enhanced
        assert 'response_url' in enhanced['metadata']

    @patch('app.services.data_sources.google_forms_service.build')
    def test_api_call_with_retry_success(self, mock_build):
        """Test successful API call with retry mechanism"""
        mock_api_call = Mock(return_value={'success': True})
        
        result = self.service._api_call_with_retry(mock_api_call)
        
        assert result == {'success': True}
        mock_api_call.assert_called_once()

    @patch('app.services.data_sources.google_forms_service.build')
    @patch('time.sleep')
    def test_api_call_with_retry_transient_error(self, mock_sleep, mock_build):
        """Test API call retry on transient errors"""
        # Mock HttpError for rate limiting
        mock_response = Mock()
        mock_response.status = 429
        http_error = HttpError(mock_response, b'Rate limit exceeded')
        
        mock_api_call = Mock(side_effect=[http_error, {'success': True}])
        
        result = self.service._api_call_with_retry(mock_api_call, max_retries=2)
        
        assert result == {'success': True}
        assert mock_api_call.call_count == 2
        mock_sleep.assert_called_once()

    @patch('app.services.data_sources.google_forms_service.build')
    def test_api_call_with_retry_permanent_error(self, mock_build):
        """Test API call failure on permanent errors"""
        # Mock HttpError for forbidden access
        mock_response = Mock()
        mock_response.status = 403
        http_error = HttpError(mock_response, b'Forbidden')
        
        mock_api_call = Mock(side_effect=http_error)
        
        with pytest.raises(HttpError):
            self.service._api_call_with_retry(mock_api_call)
        
        mock_api_call.assert_called_once()

    def test_extract_form_id_from_source_id(self):
        """Test form ID extraction from source identifiers"""
        # Test gform_ prefix
        assert self.service._extract_form_id('gform_123456') == '123456'
        
        # Test with parameters
        params = {'form_id': 'param_form_id'}
        assert self.service._extract_form_id('google-forms', params) == 'param_form_id'
        
        # Test no form ID
        assert self.service._extract_form_id('google-forms') is None

    def test_get_generic_form_fields(self):
        """Test generic form fields generation"""
        fields = self.service._get_generic_form_fields()
        
        assert len(fields) >= 4
        field_names = [field['name'] for field in fields]
        assert 'response_id' in field_names
        assert 'create_time' in field_names
        assert 'answers' in field_names
        assert 'metadata' in field_names

    def test_convert_schema_to_fields(self):
        """Test conversion of form schema to field definitions"""
        schema = FormSchema(
            form_id=self.test_form_id,
            title='Test Form',
            description='Test Description',
            questions=[
                {
                    'item_id': 'question_1',
                    'title': 'What is your name?',
                    'question_type': 'text',
                    'required': True,
                    'description': 'Enter your full name'
                },
                {
                    'item_id': 'question_2',
                    'title': 'Choose color',
                    'question_type': 'choice',
                    'required': False,
                    'options': ['Red', 'Blue', 'Green'],
                    'choice_type': 'RADIO'
                }
            ],
            settings={}
        )
        
        fields = self.service._convert_schema_to_fields(schema)
        
        # Should include generic fields plus question fields
        assert len(fields) >= 6
        
        # Find question fields
        question_fields = [f for f in fields if f['name'] in ['What is your name?', 'Choose color']]
        assert len(question_fields) == 2
        
        name_field = next(f for f in question_fields if f['name'] == 'What is your name?')
        assert name_field['type'] == 'string'
        assert name_field['required'] is True
        assert name_field['question_type'] == 'text'
        
        color_field = next(f for f in question_fields if f['name'] == 'Choose color')
        assert color_field['type'] == 'string'
        assert color_field['required'] is False
        assert color_field['question_type'] == 'choice'
        assert color_field['options'] == ['Red', 'Blue', 'Green']

    def test_map_question_type_to_field_type(self):
        """Test question type to field type mapping"""
        assert self.service._map_question_type_to_field_type('text') == 'string'
        assert self.service._map_question_type_to_field_type('choice') == 'string'
        assert self.service._map_question_type_to_field_type('scale') == 'integer'
        assert self.service._map_question_type_to_field_type('date') == 'date'
        assert self.service._map_question_type_to_field_type('time') == 'time'
        assert self.service._map_question_type_to_field_type('file_upload') == 'array'
        assert self.service._map_question_type_to_field_type('unknown') == 'string'

    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('json.load')
    def test_get_user_credentials_from_file(self, mock_json_load, mock_open, mock_exists):
        """Test user credentials retrieval from file storage"""
        mock_exists.return_value = True
        
        credentials_data = {
            'token': 'test_token',
            'refresh_token': 'test_refresh_token',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'scopes': ['scope1', 'scope2'],
            'expiry': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        mock_json_load.return_value = credentials_data
        
        # Mock cache to avoid caching issues
        with patch.object(self.service, 'cache', None):
            credentials = self.service._get_user_credentials(self.test_user_id)
        
        assert credentials is not None
        assert credentials.token == 'test_token'
        assert credentials.refresh_token == 'test_refresh_token'

    @patch('os.path.exists')
    def test_get_user_credentials_no_file(self, mock_exists):
        """Test user credentials retrieval when no file exists"""
        mock_exists.return_value = False
        
        credentials = self.service._get_user_credentials(self.test_user_id)
        
        assert credentials is None

    def test_get_status_service_enabled(self):
        """Test status retrieval for enabled service"""
        response = self.service.get_status('google-forms')
        
        assert response.success is True
        assert response.data['service_enabled'] is True
        assert response.data['source_id'] == 'google-forms'
        assert 'configuration' in response.data
        assert 'cache_status' in response.data

    def test_get_status_service_disabled(self):
        """Test status retrieval for disabled service"""
        self.service.enabled = False
        
        response = self.service.get_status('google-forms')
        
        assert response.success is True
        assert response.data['service_enabled'] is False

    def test_validate_source_valid_config(self):
        """Test source validation with valid configuration"""
        source_config = {
            'source_id': 'gform_123',
            'user_id': self.test_user_id
        }
        
        with patch.object(self.service, '_get_user_credentials', return_value=self.mock_credentials):
            with patch.object(self.service, '_check_form_accessibility', return_value=True):
                response = self.service.validate_source(source_config)
        
        assert response.success is True
        assert response.data['valid'] is True
        assert len(response.data['errors']) == 0

    def test_validate_source_invalid_config(self):
        """Test source validation with invalid configuration"""
        source_config = {
            'source_id': 'invalid_source'
        }
        
        response = self.service.validate_source(source_config)
        
        assert response.success is True
        assert response.data['valid'] is False
        assert len(response.data['errors']) > 0

    def test_refresh_data_specific_form(self):
        """Test data refresh for specific form"""
        with patch.object(self.service, '_clear_form_cache') as mock_clear:
            response = self.service.refresh_data(f'gform_{self.test_form_id}')
        
        assert response.success is True
        mock_clear.assert_called_once_with(self.test_form_id)

    def test_refresh_data_all_forms(self):
        """Test data refresh for all forms"""
        with patch.object(self.service, '_clear_all_cache') as mock_clear:
            response = self.service.refresh_data('google-forms')
        
        assert response.success is True
        mock_clear.assert_called_once()

    def test_get_fields_generic(self):
        """Test field retrieval for generic google-forms source"""
        response = self.service.get_fields('google-forms')
        
        assert response.success is True
        assert 'fields' in response.data
        assert len(response.data['fields']) >= 4

    def test_get_fields_specific_form_cached(self):
        """Test field retrieval for specific form with cached schema"""
        schema = FormSchema(
            form_id=self.test_form_id,
            title='Test Form',
            description='Test Description',
            questions=[],
            settings={}
        )
        
        with patch.object(self.service, '_get_cached_form_schema', return_value=schema):
            response = self.service.get_fields(f'gform_{self.test_form_id}')
        
        assert response.success is True
        assert 'fields' in response.data

    def test_get_preview(self):
        """Test data preview retrieval"""
        with patch.object(self.service, 'get_data') as mock_get_data:
            mock_get_data.return_value = Mock(success=True, data={'responses': []})
            
            response = self.service.get_preview('gform_123', limit=5)
        
        assert response.success is True
        mock_get_data.assert_called_once()
        
        # Verify preview parameters
        call_args = mock_get_data.call_args
        params = call_args[0][1]  # Second argument (params)
        assert params['limit'] == 5
        assert params['include_metadata'] is True
        assert params['preview_mode'] is True


class TestFormSchemaDataClass:
    """Test FormSchema data class"""

    def test_form_schema_creation(self):
        """Test FormSchema creation with all fields"""
        schema = FormSchema(
            form_id='test_form_123',
            title='Test Form',
            description='A test form',
            questions=[{'item_id': 'q1', 'title': 'Question 1'}],
            settings={'quiz': False},
            created_time='2024-01-15T10:00:00Z',
            modified_time='2024-01-15T11:00:00Z',
            published_url='https://forms.google.com/test'
        )
        
        assert schema.form_id == 'test_form_123'
        assert schema.title == 'Test Form'
        assert schema.description == 'A test form'
        assert len(schema.questions) == 1
        assert schema.settings == {'quiz': False}
        assert schema.created_time == '2024-01-15T10:00:00Z'
        assert schema.modified_time == '2024-01-15T11:00:00Z'
        assert schema.published_url == 'https://forms.google.com/test'

    def test_form_schema_minimal(self):
        """Test FormSchema creation with minimal required fields"""
        schema = FormSchema(
            form_id='test_form_123',
            title='Test Form',
            description='A test form',
            questions=[],
            settings={}
        )
        
        assert schema.form_id == 'test_form_123'
        assert schema.title == 'Test Form'
        assert schema.created_time is None
        assert schema.published_url is None


class TestResponseFilterDataClass:
    """Test ResponseFilter data class"""

    def test_response_filter_creation(self):
        """Test ResponseFilter creation with all fields"""
        start_date = datetime(2024, 1, 15, 10, 0, 0)
        end_date = datetime(2024, 1, 15, 12, 0, 0)
        
        response_filter = ResponseFilter(
            start_date=start_date,
            end_date=end_date,
            question_filters={'q1': 'answer1'},
            response_ids=['r1', 'r2'],
            limit=50,
            offset=10
        )
        
        assert response_filter.start_date == start_date
        assert response_filter.end_date == end_date
        assert response_filter.question_filters == {'q1': 'answer1'}
        assert response_filter.response_ids == ['r1', 'r2']
        assert response_filter.limit == 50
        assert response_filter.offset == 10

    def test_response_filter_defaults(self):
        """Test ResponseFilter creation with default values"""
        response_filter = ResponseFilter()
        
        assert response_filter.start_date is None
        assert response_filter.end_date is None
        assert response_filter.question_filters is None
        assert response_filter.response_ids is None
        assert response_filter.limit is None
        assert response_filter.offset is None


if __name__ == '__main__':
    pytest.main([__file__])