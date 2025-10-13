"""
Enhanced Google Forms Data Source Service

Handles data access from Google Forms responses via Google APIs with enhanced features:
- Form responses with metadata
- Form schema and question types retrieval  
- Response filtering and pagination for large datasets
- Caching for form metadata to improve performance
- Comprehensive error handling and retry logic

Supports both google-forms (general) and gform_{form_id} (specific form) sources.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import redis

from .base_service import BaseDataSourceService, DataSourceResponse
from app.core.logging import get_logger
from app.core.cache import cache_manager

logger = get_logger(__name__)


@dataclass
class FormSchema:
    """Data class for Google Form schema information"""
    form_id: str
    title: str
    description: str
    questions: List[Dict[str, Any]]
    settings: Dict[str, Any]
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    published_url: Optional[str] = None


@dataclass
class ResponseFilter:
    """Data class for response filtering options"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    question_filters: Optional[Dict[str, Any]] = None
    response_ids: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class GoogleFormsDataService(BaseDataSourceService):
    """
    Enhanced service for accessing data from Google Forms responses.
    
    Features:
    - Enhanced data retrieval with metadata
    - Form schema and question types retrieval
    - Response filtering and pagination for large datasets
    - Caching for form metadata to improve performance
    
    Supports source IDs:
    - 'google-forms': General Google Forms data source
    - 'gform_{form_id}': Specific Google Form by ID
    """

    # Cache TTL settings
    FORM_METADATA_CACHE_TTL = 1800  # 30 minutes
    FORM_SCHEMA_CACHE_TTL = 3600    # 1 hour
    USER_CREDENTIALS_CACHE_TTL = 900  # 15 minutes
    
    # API rate limiting
    API_RATE_LIMIT_DELAY = 0.1  # 100ms between requests
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2.0
    
    # Pagination settings
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000

    def __init__(self):
        super().__init__('google_forms_data_service')
        self.service_type = 'google_forms'
        
        # Initialize Google API configuration
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/v1/auth/google/callback')
        
        # Google API scopes for enhanced functionality
        self.scopes = [
            'https://www.googleapis.com/auth/forms.responses.readonly',
            'https://www.googleapis.com/auth/forms.body.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # Validate configuration
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured - service will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Enhanced Google Forms service initialized")
        
        # Initialize cache
        self.cache = cache_manager
        
        # Token storage directory
        self.tokens_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tokens', 'google')
        os.makedirs(self.tokens_dir, exist_ok=True)

    def supports_source(self, source_id: str) -> bool:
        """Check if this service supports the given source ID"""
        return source_id == 'google-forms' or source_id.startswith('gform_')

    def get_data(self, source_id: str, params: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """
        Retrieve data records from Google Forms responses with enhanced filtering and pagination.
        
        Args:
            source_id: Source identifier ('google-forms' or 'gform_{form_id}')
            params: Optional parameters including:
                - user_id: User ID for authentication
                - form_id: Specific form ID (if not in source_id)
                - limit: Number of responses to retrieve
                - offset: Pagination offset
                - start_date: Filter responses from this date
                - end_date: Filter responses until this date
                - include_metadata: Include response metadata
                - question_filters: Filter by specific question responses
        
        Returns:
            DataSourceResponse with form responses and metadata
        """
        try:
            if not self.enabled:
                return self._create_error_response(
                    'SERVICE_DISABLED',
                    'Google Forms service is not configured',
                    {'missing_config': ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']}
                )
            
            # Extract parameters
            user_id = params.get('user_id') if params else None
            if not user_id:
                return self._create_error_response(
                    'MISSING_USER_ID',
                    'User ID is required for Google Forms access',
                    {'source_id': source_id}
                )
            
            # Extract form ID from source_id or params
            form_id = self._extract_form_id(source_id, params)
            if not form_id:
                return self._create_error_response(
                    'MISSING_FORM_ID',
                    'Form ID is required for data retrieval',
                    {'source_id': source_id}
                )
            
            # Build response filter from parameters
            response_filter = self._build_response_filter(params or {})
            
            # Get user credentials
            credentials = self._get_user_credentials(user_id)
            if not credentials:
                return self._create_error_response(
                    'AUTHENTICATION_REQUIRED',
                    'User must authenticate with Google Forms first',
                    {'user_id': user_id}
                )
            
            # Fetch form responses with enhanced features
            responses_data = self._fetch_form_responses_enhanced(
                credentials, form_id, response_filter, params or {}
            )
            
            return self._create_success_response(responses_data)
            
        except Exception as e:
            logger.error(f"Error retrieving Google Forms data: {e}")
            return self._create_error_response(
                'DATA_RETRIEVAL_ERROR',
                str(e),
                {'source_id': source_id, 'params': params}
            )

    def get_fields(self, source_id: str) -> DataSourceResponse:
        """Get field definitions for Google Forms data source with enhanced schema information"""
        try:
            if not self.enabled:
                return self._create_error_response(
                    'SERVICE_DISABLED',
                    'Google Forms service is not configured'
                )
            
            # For general google-forms source, return generic field structure
            if source_id == 'google-forms':
                fields = self._get_generic_form_fields()
                return self._create_success_response({'fields': fields})
            
            # For specific form, get actual form schema
            form_id = self._extract_form_id(source_id)
            if not form_id:
                return self._create_error_response(
                    'INVALID_SOURCE_ID',
                    'Cannot extract form ID from source identifier',
                    {'source_id': source_id}
                )
            
            # This would require user authentication, so return cached schema if available
            cached_schema = self._get_cached_form_schema(form_id)
            if cached_schema:
                fields = self._convert_schema_to_fields(cached_schema)
                return self._create_success_response({'fields': fields})
            
            # Return generic fields if no cached schema available
            fields = self._get_generic_form_fields()
            return self._create_success_response({
                'fields': fields,
                'note': 'Generic fields returned. Authenticate to get specific form schema.'
            })
            
        except Exception as e:
            logger.error(f"Error retrieving Google Forms fields: {e}")
            return self._create_error_response(
                'FIELDS_RETRIEVAL_ERROR',
                str(e),
                {'source_id': source_id}
            )

    def get_preview(self, source_id: str, limit: int = 10) -> DataSourceResponse:
        """Get preview sample of Google Forms data with enhanced metadata"""
        try:
            # Use get_data with preview parameters
            params = {
                'limit': min(limit, 10),  # Limit preview to 10 items max
                'include_metadata': True,
                'preview_mode': True
            }
            
            return self.get_data(source_id, params)
            
        except Exception as e:
            logger.error(f"Error retrieving Google Forms preview: {e}")
            return self._create_error_response(
                'PREVIEW_ERROR',
                str(e),
                {'source_id': source_id, 'limit': limit}
            )

    def refresh_data(self, source_id: str) -> DataSourceResponse:
        """Refresh Google Forms data (clear cache and fetch fresh data)"""
        try:
            form_id = self._extract_form_id(source_id)
            if form_id:
                # Clear cached data for specific form
                self._clear_form_cache(form_id)
                logger.info(f"Cleared cache for form {form_id}")
            else:
                # Clear all Google Forms cache
                self._clear_all_cache()
                logger.info("Cleared all Google Forms cache")
            
            return self._create_success_response({
                'message': 'Cache cleared successfully',
                'source_id': source_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error refreshing Google Forms data: {e}")
            return self._create_error_response(
                'REFRESH_ERROR',
                str(e),
                {'source_id': source_id}
            )

    def get_status(self, source_id: str) -> DataSourceResponse:
        """Get status of Google Forms data source with enhanced diagnostics"""
        try:
            status = {
                'service_enabled': self.enabled,
                'source_id': source_id,
                'timestamp': datetime.utcnow().isoformat(),
                'configuration': {
                    'client_id_configured': bool(self.client_id),
                    'client_secret_configured': bool(self.client_secret),
                    'scopes': self.scopes
                },
                'cache_status': {
                    'cache_available': bool(self.cache),
                    'cache_type': type(self.cache).__name__ if self.cache else None
                }
            }
            
            # Check specific form status if form_id provided
            form_id = self._extract_form_id(source_id)
            if form_id:
                status['form_status'] = self._get_form_status(form_id)
            
            return self._create_success_response(status)
            
        except Exception as e:
            logger.error(f"Error getting Google Forms status: {e}")
            return self._create_error_response(
                'STATUS_ERROR',
                str(e),
                {'source_id': source_id}
            )

    def validate_source(self, source_config: Dict[str, Any]) -> DataSourceResponse:
        """Validate Google Forms data source configuration with enhanced checks"""
        try:
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'configuration_check': {}
            }
            
            # Check service configuration
            if not self.enabled:
                validation_results['valid'] = False
                validation_results['errors'].append('Google Forms service is not configured')
                validation_results['configuration_check']['service_enabled'] = False
            else:
                validation_results['configuration_check']['service_enabled'] = True
            
            # Validate source configuration
            source_id = source_config.get('source_id')
            if not source_id:
                validation_results['valid'] = False
                validation_results['errors'].append('source_id is required')
            elif not self.supports_source(source_id):
                validation_results['valid'] = False
                validation_results['errors'].append(f'Unsupported source_id: {source_id}')
            
            # Check user authentication if user_id provided
            user_id = source_config.get('user_id')
            if user_id:
                credentials = self._get_user_credentials(user_id)
                if not credentials:
                    validation_results['warnings'].append(f'User {user_id} not authenticated with Google')
                    validation_results['configuration_check']['user_authenticated'] = False
                else:
                    validation_results['configuration_check']['user_authenticated'] = True
            
            # Validate form access if form_id provided
            form_id = self._extract_form_id(source_id, source_config)
            if form_id and user_id:
                form_accessible = self._check_form_accessibility(user_id, form_id)
                validation_results['configuration_check']['form_accessible'] = form_accessible
                if not form_accessible:
                    validation_results['warnings'].append(f'Form {form_id} may not be accessible')
            
            return self._create_success_response(validation_results)
            
        except Exception as e:
            logger.error(f"Error validating Google Forms source: {e}")
            return self._create_error_response(
                'VALIDATION_ERROR',
                str(e),
                {'config': source_config}
            )

    # Enhanced methods for Google Forms integration

    def get_form_schema(self, user_id: str, form_id: str, use_cache: bool = True) -> DataSourceResponse:
        """
        Get comprehensive form schema with question types and metadata.
        
        Args:
            user_id: User ID for authentication
            form_id: Google Form ID
            use_cache: Whether to use cached schema if available
            
        Returns:
            DataSourceResponse with form schema information
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cached_schema = self._get_cached_form_schema(form_id)
                if cached_schema:
                    return self._create_success_response(cached_schema.__dict__)
            
            # Get user credentials
            credentials = self._get_user_credentials(user_id)
            if not credentials:
                return self._create_error_response(
                    'AUTHENTICATION_REQUIRED',
                    'User must authenticate with Google Forms first',
                    {'user_id': user_id}
                )
            
            # Fetch form schema from Google API
            schema = self._fetch_form_schema(credentials, form_id)
            
            # Cache the schema
            if use_cache:
                self._cache_form_schema(form_id, schema)
            
            return self._create_success_response(schema.__dict__)
            
        except Exception as e:
            logger.error(f"Error retrieving form schema: {e}")
            return self._create_error_response(
                'SCHEMA_RETRIEVAL_ERROR',
                str(e),
                {'user_id': user_id, 'form_id': form_id}
            )

    def get_form_responses_paginated(
        self, 
        user_id: str, 
        form_id: str, 
        page_size: int = None, 
        page_token: str = None,
        response_filter: ResponseFilter = None
    ) -> DataSourceResponse:
        """
        Get form responses with pagination support for large datasets.
        
        Args:
            user_id: User ID for authentication
            form_id: Google Form ID
            page_size: Number of responses per page (max 1000)
            page_token: Token for next page of results
            response_filter: Filter criteria for responses
            
        Returns:
            DataSourceResponse with paginated responses and next page token
        """
        try:
            # Validate page size
            if page_size is None:
                page_size = self.DEFAULT_PAGE_SIZE
            page_size = min(page_size, self.MAX_PAGE_SIZE)
            
            # Get user credentials
            credentials = self._get_user_credentials(user_id)
            if not credentials:
                return self._create_error_response(
                    'AUTHENTICATION_REQUIRED',
                    'User must authenticate with Google Forms first',
                    {'user_id': user_id}
                )
            
            # Fetch paginated responses
            responses_data = self._fetch_responses_paginated(
                credentials, form_id, page_size, page_token, response_filter
            )
            
            return self._create_success_response(responses_data)
            
        except Exception as e:
            logger.error(f"Error retrieving paginated responses: {e}")
            return self._create_error_response(
                'PAGINATED_RETRIEVAL_ERROR',
                str(e),
                {'user_id': user_id, 'form_id': form_id}
            )

    # Private helper methods

    def _extract_form_id(self, source_id: str, params: Dict[str, Any] = None) -> Optional[str]:
        """Extract form ID from source_id or parameters"""
        if source_id.startswith('gform_'):
            return source_id[6:]  # Remove 'gform_' prefix
        
        if params and 'form_id' in params:
            return params['form_id']
        
        return None

    def _build_response_filter(self, params: Dict[str, Any]) -> ResponseFilter:
        """Build response filter from parameters"""
        response_filter = ResponseFilter()
        
        # Date filters
        if 'start_date' in params:
            if isinstance(params['start_date'], str):
                response_filter.start_date = datetime.fromisoformat(params['start_date'])
            elif isinstance(params['start_date'], datetime):
                response_filter.start_date = params['start_date']
        
        if 'end_date' in params:
            if isinstance(params['end_date'], str):
                response_filter.end_date = datetime.fromisoformat(params['end_date'])
            elif isinstance(params['end_date'], datetime):
                response_filter.end_date = params['end_date']
        
        # Pagination
        response_filter.limit = params.get('limit')
        response_filter.offset = params.get('offset', 0)
        
        # Question filters
        response_filter.question_filters = params.get('question_filters')
        response_filter.response_ids = params.get('response_ids')
        
        return response_filter

    def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Retrieve and refresh user credentials with caching"""
        # Check cache first
        cache_key = f"google_credentials_{user_id}"
        cached_creds = self.cache.get(cache_key) if self.cache else None
        
        if cached_creds:
            try:
                credentials = Credentials.from_authorized_user_info(cached_creds)
                if not credentials.expired:
                    return credentials
            except Exception as e:
                logger.warning(f"Error loading cached credentials: {e}")
        
        # Load from file storage
        token_path = os.path.join(self.tokens_dir, f"user_{user_id}_google_token.json")
        
        if not os.path.exists(token_path):
            return None
        
        try:
            with open(token_path, 'r') as token_file:
                credentials_data = json.load(token_file)
            
            credentials = Credentials(
                token=credentials_data.get('token'),
                refresh_token=credentials_data.get('refresh_token'),
                token_uri=credentials_data.get('token_uri'),
                client_id=credentials_data.get('client_id'),
                client_secret=credentials_data.get('client_secret'),
                scopes=credentials_data.get('scopes')
            )
            
            # Set expiry if available
            if credentials_data.get('expiry'):
                credentials.expiry = datetime.fromisoformat(credentials_data['expiry'])
            
            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                logger.info(f"Refreshing expired credentials for user {user_id}")
                credentials.refresh(Request())
                self._store_user_credentials(user_id, credentials)
            
            # Cache valid credentials
            if self.cache and not credentials.expired:
                self.cache.set(
                    cache_key, 
                    credentials.to_json(), 
                    ttl=self.USER_CREDENTIALS_CACHE_TTL
                )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error loading credentials for user {user_id}: {e}")
            return None

    def _store_user_credentials(self, user_id: str, credentials: Credentials):
        """Store user credentials securely"""
        token_path = os.path.join(self.tokens_dir, f"user_{user_id}_google_token.json")
        
        credentials_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        with open(token_path, 'w') as token_file:
            json.dump(credentials_data, token_file, indent=2)
        
        logger.info(f"Stored credentials for user {user_id}")

    def _fetch_form_schema(self, credentials: Credentials, form_id: str) -> FormSchema:
        """Fetch comprehensive form schema from Google Forms API"""
        try:
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Add rate limiting
            time.sleep(self.API_RATE_LIMIT_DELAY)
            
            # Get form with retry logic
            form_data = self._api_call_with_retry(
                lambda: forms_service.forms().get(formId=form_id).execute()
            )
            
            # Parse form structure
            questions = []
            for item in form_data.get('items', []):
                if 'questionItem' in item:
                    question = self._parse_question_item(item)
                    questions.append(question)
            
            # Create schema object
            schema = FormSchema(
                form_id=form_id,
                title=form_data.get('info', {}).get('title', ''),
                description=form_data.get('info', {}).get('description', ''),
                questions=questions,
                settings=form_data.get('settings', {}),
                published_url=form_data.get('responderUri', '')
            )
            
            return schema
            
        except Exception as e:
            logger.error(f"Error fetching form schema: {e}")
            raise

    def _parse_question_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a question item from Google Forms API response"""
        question_item = item['questionItem']
        question = question_item['question']
        
        parsed_question = {
            'item_id': item['itemId'],
            'title': question.get('questionTitle', ''),
            'description': item.get('description', ''),
            'required': question.get('required', False),
            'question_type': self._determine_question_type(question),
            'options': []
        }
        
        # Parse question-specific options
        if 'choiceQuestion' in question:
            choice_question = question['choiceQuestion']
            parsed_question['choice_type'] = choice_question.get('type', 'RADIO')
            parsed_question['options'] = [
                option.get('value', '') for option in choice_question.get('options', [])
            ]
            parsed_question['shuffle'] = choice_question.get('shuffle', False)
        
        elif 'textQuestion' in question:
            text_question = question['textQuestion']
            parsed_question['paragraph'] = text_question.get('paragraph', False)
        
        elif 'scaleQuestion' in question:
            scale_question = question['scaleQuestion']
            parsed_question['low'] = scale_question.get('low', 1)
            parsed_question['high'] = scale_question.get('high', 5)
            parsed_question['low_label'] = scale_question.get('lowLabel', '')
            parsed_question['high_label'] = scale_question.get('highLabel', '')
        
        elif 'dateQuestion' in question:
            date_question = question['dateQuestion']
            parsed_question['include_time'] = date_question.get('includeTime', False)
            parsed_question['include_year'] = date_question.get('includeYear', True)
        
        elif 'timeQuestion' in question:
            time_question = question['timeQuestion']
            parsed_question['duration'] = time_question.get('duration', False)
        
        elif 'fileUploadQuestion' in question:
            file_question = question['fileUploadQuestion']
            parsed_question['folder_id'] = file_question.get('folderId', '')
            parsed_question['max_files'] = file_question.get('maxFiles', 1)
            parsed_question['max_file_size'] = file_question.get('maxFileSize', 10485760)  # 10MB default
            parsed_question['types'] = file_question.get('types', [])
        
        return parsed_question

    def _determine_question_type(self, question: Dict[str, Any]) -> str:
        """Determine the type of question from Google Forms structure"""
        if 'choiceQuestion' in question:
            return 'choice'
        elif 'textQuestion' in question:
            return 'text'
        elif 'scaleQuestion' in question:
            return 'scale'
        elif 'dateQuestion' in question:
            return 'date'
        elif 'timeQuestion' in question:
            return 'time'
        elif 'fileUploadQuestion' in question:
            return 'file_upload'
        else:
            return 'unknown'

    def _fetch_form_responses_enhanced(
        self, 
        credentials: Credentials, 
        form_id: str, 
        response_filter: ResponseFilter,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch form responses with enhanced filtering and metadata"""
        try:
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Get form schema for response parsing
            schema = self._fetch_form_schema(credentials, form_id)
            
            # Fetch responses with pagination
            all_responses = []
            page_token = None
            total_fetched = 0
            limit = response_filter.limit or 1000
            
            while total_fetched < limit:
                # Calculate page size for this request
                page_size = min(self.MAX_PAGE_SIZE, limit - total_fetched)
                
                # Add rate limiting
                time.sleep(self.API_RATE_LIMIT_DELAY)
                
                # Fetch responses page
                request_params = {'formId': form_id, 'pageSize': page_size}
                if page_token:
                    request_params['pageToken'] = page_token
                
                responses_result = self._api_call_with_retry(
                    lambda: forms_service.forms().responses().list(**request_params).execute()
                )
                
                responses = responses_result.get('responses', [])
                if not responses:
                    break
                
                # Filter responses based on criteria
                filtered_responses = self._filter_responses(responses, response_filter)
                all_responses.extend(filtered_responses)
                
                total_fetched += len(responses)
                page_token = responses_result.get('nextPageToken')
                
                if not page_token:
                    break
            
            # Parse and enhance responses
            enhanced_responses = []
            for response in all_responses:
                enhanced_response = self._enhance_response_data(response, schema, params)
                enhanced_responses.append(enhanced_response)
            
            # Apply offset if specified
            if response_filter.offset:
                enhanced_responses = enhanced_responses[response_filter.offset:]
            
            # Apply final limit
            if response_filter.limit:
                enhanced_responses = enhanced_responses[:response_filter.limit]
            
            return {
                'form_id': form_id,
                'form_title': schema.title,
                'form_description': schema.description,
                'responses': enhanced_responses,
                'total_count': len(enhanced_responses),
                'schema': schema.__dict__,
                'filter_applied': response_filter.__dict__,
                'retrieved_at': datetime.utcnow().isoformat(),
                'has_more': bool(page_token),
                'next_page_token': page_token
            }
            
        except Exception as e:
            logger.error(f"Error fetching enhanced form responses: {e}")
            raise

    def _filter_responses(self, responses: List[Dict], response_filter: ResponseFilter) -> List[Dict]:
        """Filter responses based on criteria"""
        if not response_filter:
            return responses
        
        filtered = responses
        
        # Date filtering
        if response_filter.start_date or response_filter.end_date:
            date_filtered = []
            for response in filtered:
                create_time_str = response.get('createTime', '')
                if create_time_str:
                    try:
                        create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                        
                        if response_filter.start_date and create_time < response_filter.start_date:
                            continue
                        if response_filter.end_date and create_time > response_filter.end_date:
                            continue
                        
                        date_filtered.append(response)
                    except ValueError:
                        # Skip responses with invalid timestamps
                        continue
            filtered = date_filtered
        
        # Response ID filtering
        if response_filter.response_ids:
            filtered = [r for r in filtered if r.get('responseId') in response_filter.response_ids]
        
        # Question-based filtering
        if response_filter.question_filters:
            question_filtered = []
            for response in filtered:
                answers = response.get('answers', {})
                match = True
                
                for question_id, expected_value in response_filter.question_filters.items():
                    if question_id not in answers:
                        match = False
                        break
                    
                    answer_data = answers[question_id]
                    actual_value = self._extract_answer_value(answer_data)
                    
                    if actual_value != expected_value:
                        match = False
                        break
                
                if match:
                    question_filtered.append(response)
            
            filtered = question_filtered
        
        return filtered

    def _enhance_response_data(
        self, 
        response: Dict[str, Any], 
        schema: FormSchema, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance response data with metadata and parsed answers"""
        enhanced = {
            'response_id': response.get('responseId'),
            'create_time': response.get('createTime'),
            'last_submitted_time': response.get('lastSubmittedTime'),
            'answers': {},
            'metadata': {}
        }
        
        # Add metadata if requested
        if params.get('include_metadata', False):
            enhanced['metadata'] = {
                'total_score': response.get('totalScore'),
                'respondent_email': response.get('respondentEmail'),
                'response_url': f"https://docs.google.com/forms/d/{schema.form_id}/edit#response={response.get('responseId')}"
            }
        
        # Parse answers with question context
        question_map = {q['item_id']: q for q in schema.questions}
        
        for question_id, answer_data in response.get('answers', {}).items():
            question_info = question_map.get(question_id, {})
            question_title = question_info.get('title', f'Question_{question_id}')
            
            parsed_answer = self._parse_answer_enhanced(answer_data, question_info)
            enhanced['answers'][question_title] = parsed_answer
        
        return enhanced

    def _parse_answer_enhanced(self, answer_data: Dict[str, Any], question_info: Dict[str, Any]) -> Any:
        """Parse answer data with enhanced type handling"""
        question_type = question_info.get('question_type', 'unknown')
        
        if 'textAnswers' in answer_data:
            texts = answer_data['textAnswers']['answers']
            if question_type == 'text' and question_info.get('paragraph', False):
                # Multi-line text
                return '\n'.join([text['value'] for text in texts])
            else:
                # Single line text or choice
                return texts[0]['value'] if texts else ''
        
        elif 'fileUploadAnswers' in answer_data:
            files = answer_data['fileUploadAnswers']['answers']
            return [{
                'file_id': file['fileId'],
                'file_name': file.get('fileName', ''),
                'mime_type': file.get('mimeType', '')
            } for file in files]
        
        else:
            return str(answer_data)

    def _extract_answer_value(self, answer_data: Dict[str, Any]) -> Any:
        """Extract simple answer value for filtering"""
        if 'textAnswers' in answer_data:
            texts = answer_data['textAnswers']['answers']
            return texts[0]['value'] if texts else ''
        elif 'fileUploadAnswers' in answer_data:
            files = answer_data['fileUploadAnswers']['answers']
            return [file['fileId'] for file in files]
        else:
            return str(answer_data)

    def _fetch_responses_paginated(
        self,
        credentials: Credentials,
        form_id: str,
        page_size: int,
        page_token: Optional[str],
        response_filter: Optional[ResponseFilter]
    ) -> Dict[str, Any]:
        """Fetch responses with pagination support"""
        try:
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Build request parameters
            request_params = {
                'formId': form_id,
                'pageSize': page_size
            }
            
            if page_token:
                request_params['pageToken'] = page_token
            
            # Add rate limiting
            time.sleep(self.API_RATE_LIMIT_DELAY)
            
            # Fetch responses
            responses_result = self._api_call_with_retry(
                lambda: forms_service.forms().responses().list(**request_params).execute()
            )
            
            responses = responses_result.get('responses', [])
            next_page_token = responses_result.get('nextPageToken')
            
            # Apply filtering if specified
            if response_filter:
                responses = self._filter_responses(responses, response_filter)
            
            # Get form schema for response enhancement
            schema = self._fetch_form_schema(credentials, form_id)
            
            # Enhance responses
            enhanced_responses = []
            for response in responses:
                enhanced_response = self._enhance_response_data(response, schema, {})
                enhanced_responses.append(enhanced_response)
            
            return {
                'form_id': form_id,
                'form_title': schema.title,
                'responses': enhanced_responses,
                'page_size': page_size,
                'next_page_token': next_page_token,
                'has_more': bool(next_page_token),
                'total_in_page': len(enhanced_responses),
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching paginated responses: {e}")
            raise

    def _api_call_with_retry(self, api_call_func, max_retries: int = None) -> Any:
        """Execute API call with retry logic and exponential backoff"""
        if max_retries is None:
            max_retries = self.MAX_RETRIES
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return api_call_func()
            
            except HttpError as e:
                last_exception = e
                
                # Don't retry on certain errors
                if e.resp.status in [400, 401, 403, 404]:
                    raise e
                
                # Retry on rate limiting and server errors
                if e.resp.status in [429, 500, 502, 503, 504] and attempt < max_retries:
                    delay = (self.RETRY_BACKOFF_FACTOR ** attempt) + (attempt * 0.1)  # Add jitter
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
                    continue
                
                raise e
            
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = (self.RETRY_BACKOFF_FACTOR ** attempt)
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
                    continue
                
                raise e
        
        # If we get here, all retries failed
        raise last_exception

    # Caching methods

    def _get_cached_form_schema(self, form_id: str) -> Optional[FormSchema]:
        """Get cached form schema"""
        if not self.cache:
            return None
        
        cache_key = f"form_schema_{form_id}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            try:
                return FormSchema(**cached_data)
            except Exception as e:
                logger.warning(f"Error loading cached schema: {e}")
        
        return None

    def _cache_form_schema(self, form_id: str, schema: FormSchema):
        """Cache form schema"""
        if not self.cache:
            return
        
        cache_key = f"form_schema_{form_id}"
        self.cache.set(cache_key, schema.__dict__, ttl=self.FORM_SCHEMA_CACHE_TTL)

    def _clear_form_cache(self, form_id: str):
        """Clear cache for specific form"""
        if not self.cache:
            return
        
        cache_keys = [
            f"form_schema_{form_id}",
            f"form_metadata_{form_id}",
            f"form_responses_{form_id}"
        ]
        
        for key in cache_keys:
            self.cache.delete(key)

    def _clear_all_cache(self):
        """Clear all Google Forms cache"""
        if not self.cache:
            return
        
        # This is a simplified implementation
        # In production, you might want to use cache key patterns
        try:
            if hasattr(self.cache, 'clear'):
                self.cache.clear()
            else:
                logger.warning("Cache clear not supported")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")

    # Utility methods

    def _get_generic_form_fields(self) -> List[Dict[str, Any]]:
        """Get generic field definitions for Google Forms"""
        return [
            {
                'name': 'response_id',
                'type': 'string',
                'description': 'Unique response identifier',
                'required': True
            },
            {
                'name': 'create_time',
                'type': 'datetime',
                'description': 'Response creation timestamp',
                'required': True
            },
            {
                'name': 'last_submitted_time',
                'type': 'datetime',
                'description': 'Last submission timestamp',
                'required': False
            },
            {
                'name': 'answers',
                'type': 'object',
                'description': 'Form answers mapped by question title',
                'required': True
            },
            {
                'name': 'metadata',
                'type': 'object',
                'description': 'Additional response metadata',
                'required': False
            }
        ]

    def _convert_schema_to_fields(self, schema: FormSchema) -> List[Dict[str, Any]]:
        """Convert form schema to field definitions"""
        fields = self._get_generic_form_fields()
        
        # Add question-specific fields
        for question in schema.questions:
            field = {
                'name': question['title'],
                'type': self._map_question_type_to_field_type(question['question_type']),
                'description': question.get('description', ''),
                'required': question.get('required', False),
                'question_id': question['item_id'],
                'question_type': question['question_type']
            }
            
            # Add type-specific properties
            if question['question_type'] == 'choice':
                field['options'] = question.get('options', [])
                field['choice_type'] = question.get('choice_type', 'RADIO')
            elif question['question_type'] == 'scale':
                field['scale_low'] = question.get('low', 1)
                field['scale_high'] = question.get('high', 5)
                field['scale_low_label'] = question.get('low_label', '')
                field['scale_high_label'] = question.get('high_label', '')
            
            fields.append(field)
        
        return fields

    def _map_question_type_to_field_type(self, question_type: str) -> str:
        """Map Google Forms question type to generic field type"""
        mapping = {
            'text': 'string',
            'choice': 'string',
            'scale': 'integer',
            'date': 'date',
            'time': 'time',
            'file_upload': 'array',
            'unknown': 'string'
        }
        return mapping.get(question_type, 'string')

    def _get_form_status(self, form_id: str) -> Dict[str, Any]:
        """Get status information for specific form"""
        return {
            'form_id': form_id,
            'cached_schema': bool(self._get_cached_form_schema(form_id)),
            'cache_available': bool(self.cache),
            'last_accessed': datetime.utcnow().isoformat()
        }

    def _check_form_accessibility(self, user_id: str, form_id: str) -> bool:
        """Check if user can access the specified form"""
        try:
            credentials = self._get_user_credentials(user_id)
            if not credentials:
                return False
            
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Try to access form metadata
            forms_service.forms().get(formId=form_id).execute()
            return True
            
        except HttpError as e:
            if e.resp.status in [403, 404]:
                return False
            # For other errors, assume accessible but with issues
            return True
        except Exception:
            return False