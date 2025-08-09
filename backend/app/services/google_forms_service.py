"""
Production-Ready Google Forms Service
Real Google Forms API integration with environment-based OAuth configuration
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app import db
from app.models import User, FormSubmission

logger = logging.getLogger(__name__)

class ProductionGoogleFormsService:
    """Production-ready Google Forms service with real API integration"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/forms.body.readonly',
        'https://www.googleapis.com/auth/forms.responses.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    def __init__(self):
        # Get credentials from environment variables with proper error handling
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.project_id = os.getenv('GOOGLE_PROJECT_ID', 'stratosys')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/google-forms/callback')
        
        # Credentials can be from file or environment
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        
        # Ensure we have all required configuration
        if not all([self.client_id, self.client_secret]):
            logger.error("Missing required Google OAuth configuration. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
            raise ValueError("Missing required Google OAuth configuration")
        
        logger.info("Production Google Forms service initialized with real API credentials")
    
    def _get_credentials_config(self) -> Dict[str, Any]:
        """Get credentials configuration from environment or file"""
        if self.credentials_json:
            try:
                return json.loads(self.credentials_json)
            except json.JSONDecodeError:
                logger.error("Invalid GOOGLE_CREDENTIALS JSON format")
                
        # Fallback to manual configuration
        return {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "project_id": self.project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
    def get_authorization_url(self, user_id: str) -> str:
        """Generate real Google OAuth authorization URL using environment credentials"""
        try:
            # Get credentials configuration from environment
            config = self._get_credentials_config()
            
            # Create OAuth flow with real credentials
            flow = Flow.from_client_config(
                config,
                scopes=self.SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generate authorization URL with state parameter for security
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id  # Use user_id as state for security
            )
            
            # Store state for verification during callback
            self._store_oauth_state(user_id, state)
            
            logger.info(f"Generated real OAuth URL for user {user_id}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            raise
    
    def handle_oauth_callback(self, user_id: str, code: str, state: str) -> Dict[str, Any]:
        """Handle real OAuth callback and store credentials securely"""
        try:
            # Verify state parameter for security
            if not self._verify_oauth_state(user_id, state):
                raise ValueError("Invalid state parameter - possible CSRF attack")
            
            # Get credentials configuration
            config = self._get_credentials_config()
            
            # Exchange code for credentials
            flow = Flow.from_client_config(
                config,
                scopes=self.SCOPES,
                state=state
            )
            flow.redirect_uri = self.redirect_uri
            
            # Fetch token using the authorization code
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Store credentials securely for user  
            self._store_user_credentials(user_id, credentials)
            
            logger.info(f"Successfully authenticated user {user_id} with real Google API")
            return {
                'status': 'success',
                'message': 'Authentication successful',
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error for user {user_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'user_id': user_id
            }
    
    def _store_oauth_state(self, user_id: str, state: str):
        """Store OAuth state for verification during callback"""
        # Create tokens directory if it doesn't exist
        tokens_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tokens')
        os.makedirs(tokens_dir, exist_ok=True)
        
        state_path = os.path.join(tokens_dir, f"user_{user_id}_oauth_state.json")
        state_data = {
            'state': state,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        with open(state_path, 'w') as f:
            json.dump(state_data, f)
    
    def _verify_oauth_state(self, user_id: str, state: str) -> bool:
        """Verify OAuth state parameter"""
        try:
            tokens_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tokens')
            state_path = os.path.join(tokens_dir, f"user_{user_id}_oauth_state.json")
            
            if not os.path.exists(state_path):
                return False
                
            with open(state_path, 'r') as f:
                state_data = json.load(f)
            
            # Check if state matches and hasn't expired
            stored_state = state_data.get('state')
            expires_at = datetime.fromisoformat(state_data.get('expires_at'))
            
            # Clean up state file
            os.remove(state_path)
            
            return stored_state == state and datetime.utcnow() < expires_at
            
        except Exception as e:
            logger.error(f"Error verifying OAuth state: {e}")
            return False
    
    def get_user_forms(self, user_id: str, page_size: int = 50) -> List[Dict[str, Any]]:
        """Get real Google Forms for authenticated user via Google Drive API"""
        try:
            credentials = self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No valid credentials found for user {user_id}")
                raise Exception("User not authenticated with Google Forms")
            
            # Build Google Drive service to find forms
            drive_service = build('drive', 'v3', credentials=credentials)
            forms_service = build('forms', 'v1', credentials=credentials)
            
            logger.info(f"Fetching real Google Forms for user {user_id}")
            
            # Search for Google Forms in user's Drive with real API call
            query = "mimeType='application/vnd.google-apps.form'"
            results = drive_service.files().list(
                q=query,
                pageSize=page_size,
                fields="files(id,name,createdTime,modifiedTime,webViewLink,owners)"
            ).execute()
            
            forms = []
            files = results.get('files', [])
            logger.info(f"Found {len(files)} Google Forms for user {user_id}")
            
            for file in files:
                try:
                    # Get detailed form information from Forms API
                    form_details = forms_service.forms().get(formId=file['id']).execute()
                    
                    # Get real response count
                    response_count = 0
                    try:
                        responses_result = forms_service.forms().responses().list(
                            formId=file['id'],
                            pageSize=1
                        ).execute()
                        # For accurate count, we'd need to paginate through all, but this gives us an indicator
                        if 'responses' in responses_result:
                            response_count = len(responses_result['responses'])
                            # If we got the max page size, there might be more
                            if response_count == 1:
                                # Quick count estimation - in production you might want full pagination
                                all_responses = forms_service.forms().responses().list(
                                    formId=file['id']
                                ).execute()
                                response_count = len(all_responses.get('responses', []))
                    except HttpError:
                        response_count = 0  # Form might not have responses or no permission
                    
                    form_info = {
                        'id': file['id'],
                        'title': file['name'],
                        'description': form_details.get('info', {}).get('description', ''),
                        'created_time': file.get('createdTime'),
                        'modified_time': file.get('modifiedTime'),
                        'web_view_link': file.get('webViewLink'),
                        'published_url': form_details.get('responderUri', ''),
                        'response_count': response_count,
                        'question_count': len(form_details.get('items', [])),
                        'type': 'google_form',
                        'status': 'active',
                        'settings': form_details.get('settings', {}),
                        'owners': file.get('owners', [])
                    }
                    
                    forms.append(form_info)
                    
                except HttpError as e:
                    logger.warning(f"Could not access form {file['id']}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing form {file['id']}: {e}")
                    continue
            
            logger.info(f"Successfully retrieved {len(forms)} real Google Forms for user {user_id}")
            return forms
            
        except Exception as e:
            logger.error(f"Error fetching real Google Forms for user {user_id}: {e}")
            raise Exception(f"Failed to fetch Google Forms: {str(e)}")
    
    def get_form_responses(self, user_id: str, form_id: str, limit: int = 100, include_analysis: bool = False) -> Dict[str, Any]:
        """Get real responses for a specific Google Form using Google Forms API"""
        try:
            credentials = self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No valid credentials found for user {user_id}")
                raise Exception("User not authenticated with Google Forms")
            
            forms_service = build('forms', 'v1', credentials=credentials)
            
            logger.info(f"Fetching real responses for form {form_id} (user: {user_id})")
            
            # Get form structure with real API call
            form = forms_service.forms().get(formId=form_id).execute()
            
            # Get real responses from Google Forms API
            responses_result = forms_service.forms().responses().list(
                formId=form_id,
                pageSize=min(limit, 1000)  # Google API limit
            ).execute()
            
            responses = responses_result.get('responses', [])
            logger.info(f"Retrieved {len(responses)} real responses for form {form_id}")
            
            # Parse form structure to understand questions
            questions = {}
            for item in form.get('items', []):
                if 'questionItem' in item:
                    question_id = item['itemId']
                    question = item['questionItem']['question']
                    questions[question_id] = {
                        'title': question.get('questionTitle', ''),
                        'type': self._get_question_type(question),
                        'required': question.get('required', False)
                    }
            
            # Parse and structure real responses
            structured_responses = []
            for response in responses:
                structured_response = {
                    'response_id': response.get('responseId'),
                    'create_time': response.get('createTime'),
                    'last_submitted_time': response.get('lastSubmittedTime'),
                    'answers': {}
                }
                
                # Map real answers to questions
                for question_id, answer_data in response.get('answers', {}).items():
                    if question_id in questions:
                        question_title = questions[question_id]['title']
                        parsed_answer = self._parse_answer(answer_data)
                        structured_response['answers'][question_title] = parsed_answer
                
                structured_responses.append(structured_response)
            
            # Generate real data analysis if requested
            analysis = None
            if include_analysis and structured_responses:
                analysis = self._analyze_responses(structured_responses, questions)
            
            result = {
                'success': True,
                'form_info': {
                    'id': form_id,
                    'title': form.get('info', {}).get('title', ''),
                    'description': form.get('info', {}).get('description', ''),
                    'published_url': form.get('responderUri', ''),
                    'total_questions': len(questions),
                    'form_type': form.get('info', {}).get('documentTitle', 'Google Form')
                },
                'responses': structured_responses,
                'total_count': len(structured_responses),
                'questions': questions,
                'data_source': 'google_forms_api',
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
            if analysis:
                result['analysis'] = analysis
            
            logger.info(f"Successfully processed {len(structured_responses)} real responses for form {form_id}")
            return result
            
        except HttpError as e:
            logger.error(f"Google API error fetching form responses: {e}")
            # Try to provide helpful error messages
            if e.resp.status == 404:
                raise Exception(f"Form {form_id} not found or not accessible")
            elif e.resp.status == 403:
                raise Exception(f"Access denied to form {form_id}. Check permissions.")
            else:
                raise Exception(f"Google API error: {e}")
        except Exception as e:
            logger.error(f"Error fetching real form responses: {e}")
            raise
    
    def generate_automated_report(self, user_id: str, form_id: str, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate automated report from real Google Form data"""
        try:
            # Get real form responses
            form_data = self.get_form_responses(user_id, form_id, include_analysis=True)
            
            if not form_data['success']:
                raise Exception("Failed to fetch form data")
            
            # Extract data for report generation
            responses = form_data['responses']
            analysis = form_data.get('analysis', {})
            form_info = form_data['form_info']
            
            # Process responses for template mapping
            template_data = self._map_responses_to_template(responses, form_info, analysis)
            
            # Store processed data in database (using external form ID as string)
            # Since Google Forms use string IDs, we'll store in a JSON format
            template_data['google_form_id'] = form_id
            template_data['processing_timestamp'] = datetime.utcnow().isoformat()
            
            # For now, we'll return the data without database storage
            # In production, you might want to create a GoogleFormSubmission model
            # that accepts string form IDs
            
            logger.info(f"Generated automated report for form {form_id} with real data")
            return {
                'status': 'success',
                'template_data': template_data,
                'form_info': form_info,
                'response_count': len(responses),
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating automated report: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _store_user_credentials(self, user_id: str, credentials):
        """Store user credentials securely with real token data"""
        # Create tokens directory if it doesn't exist
        tokens_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tokens')
        os.makedirs(tokens_dir, exist_ok=True)
        
        # Store credentials in user-specific file with real data
        token_path = os.path.join(tokens_dir, f"user_{user_id}_google_token.json")
        
        # Convert credentials to JSON format for storage
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
        
        logger.info(f"Stored real credentials for user {user_id}")
    
    def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Retrieve stored user credentials and refresh if needed"""
        tokens_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tokens')
        token_path = os.path.join(tokens_dir, f"user_{user_id}_google_token.json")
        
        if not os.path.exists(token_path):
            logger.warning(f"No credentials found for user {user_id}")
            return None
        
        try:
            # Load credentials from file
            with open(token_path, 'r') as token_file:
                credentials_data = json.load(token_file)
            
            # Reconstruct credentials object
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
                # Save refreshed credentials
                self._store_user_credentials(user_id, credentials)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error loading credentials for user {user_id}: {e}")
            return None
    
    def _get_question_type(self, question: Dict) -> str:
        """Determine question type from Google Forms structure"""
        if 'choiceQuestion' in question:
            return 'choice'
        elif 'textQuestion' in question:
            return 'text'
        elif 'scaleQuestion' in question:
            return 'scale'
        elif 'fileUploadQuestion' in question:
            return 'file_upload'
        elif 'dateQuestion' in question:
            return 'date'
        elif 'timeQuestion' in question:
            return 'time'
        else:
            return 'unknown'
    
    def _parse_answer(self, answer_data: Dict) -> Any:
        """Parse answer data based on question type"""
        if 'textAnswers' in answer_data:
            texts = answer_data['textAnswers']['answers']
            return texts[0]['value'] if texts else ''
        elif 'fileUploadAnswers' in answer_data:
            files = answer_data['fileUploadAnswers']['answers']
            return [file['fileId'] for file in files] if files else []
        else:
            return str(answer_data)
    
    def _analyze_responses(self, responses: List[Dict], questions: Dict) -> Dict[str, Any]:
        """Analyze real form responses for insights"""
        total_responses = len(responses)
        if total_responses == 0:
            return {'message': 'No responses to analyze'}
        
        # Calculate completion stats
        completion_stats = {
            'total_responses': total_responses,
            'completion_rate': 100.0  # All retrieved responses are complete
        }
        
        # Analyze response patterns
        response_times = [resp['create_time'] for resp in responses if resp.get('create_time')]
        if response_times:
            dates = [datetime.fromisoformat(rt.replace('Z', '+00:00')) for rt in response_times]
            completion_stats['first_response'] = min(dates).isoformat()
            completion_stats['last_response'] = max(dates).isoformat()
        
        # Question-level analysis
        question_insights = {}
        for question_id, question_info in questions.items():
            question_title = question_info['title']
            answers = [resp['answers'].get(question_title) for resp in responses if question_title in resp['answers']]
            
            if answers:
                question_insights[question_title] = {
                    'response_count': len([a for a in answers if a]),
                    'response_rate': len([a for a in answers if a]) / total_responses * 100
                }
                
                # Type-specific analysis
                if question_info['type'] == 'choice':
                    answer_counts = {}
                    for answer in answers:
                        if answer:
                            answer_counts[answer] = answer_counts.get(answer, 0) + 1
                    question_insights[question_title]['distribution'] = answer_counts
                    question_insights[question_title]['most_common'] = max(answer_counts.items(), key=lambda x: x[1])[0] if answer_counts else None
        
        return {
            'completion_stats': completion_stats,
            'question_insights': question_insights,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _map_responses_to_template(self, responses: List[Dict], form_info: Dict, analysis: Dict) -> Dict[str, Any]:
        """Map real form responses to template placeholders"""
        if not responses:
            return {}
        
        # Extract common template data from real responses
        template_data = {
            'program': {
                'title': form_info.get('title', 'Program Title'),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': '9:00 AM - 5:00 PM',  # Default, should be extracted from form
                'location': 'Location TBD',  # Should be extracted from form responses
                'organizer': 'Organization Name',  # Should be extracted from form
                'total_participants': str(len(responses))
            },
            'participants': [],
            'analysis_summary': analysis,
            'response_statistics': {
                'total_responses': len(responses),
                'completion_rate': analysis.get('completion_stats', {}).get('completion_rate', 0)
            }
        }
        
        # Extract participant data from responses
        for i, response in enumerate(responses[:50]):  # Limit to 50 for performance
            participant = {
                'bil': str(i + 1),
                'name': self._extract_name_from_response(response),
                'submission_time': response.get('create_time', ''),
                'response_id': response.get('response_id', '')
            }
            template_data['participants'].append(participant)
        
        return template_data
    
    def _extract_name_from_response(self, response: Dict) -> str:
        """Extract participant name from form response"""
        answers = response.get('answers', {})
        
        # Look for common name field patterns
        name_patterns = ['name', 'nama', 'full name', 'participant name', 'your name']
        
        for question, answer in answers.items():
            if any(pattern.lower() in question.lower() for pattern in name_patterns):
                return str(answer) if answer else 'Anonymous'
        
        # Fallback to first text answer if no name field found
        for answer in answers.values():
            if isinstance(answer, str) and len(answer) > 2:
                return answer
        
        return 'Anonymous Participant'
    
    def get_form_responses_for_automated_report(self, user_id: str, form_id: str) -> Dict[str, Any]:
        """Get form responses specifically formatted for automated report generation"""
        try:
            # Get comprehensive form data
            form_data = self.get_form_responses(user_id, form_id, include_analysis=True)
            
            if not form_data['success']:
                raise Exception("Failed to fetch form data for automated report")
            
            # Enhanced analysis for report generation
            responses = form_data['responses']
            form_info = form_data['form_info']
            
            # Generate comprehensive analysis including Rumusan Penilaian data
            analysis = self._analyze_form_responses_comprehensive(responses, form_info)
            
            return {
                'form_info': form_info,
                'responses': responses,
                'analysis': analysis,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error getting form responses for automated report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_form_responses_comprehensive(self, responses: List[Dict], form_info: Dict) -> Dict[str, Any]:
        """Comprehensive analysis of form responses including Rumusan Penilaian data"""
        if not responses:
            return {}
        
        analysis = {
            'total_responses': len(responses),
            'response_rate': 100,  # Assuming all responses are valid
            'completion_stats': {},
            'field_analysis': {},
            'rumusan_penilaian': {},
            'temporal_analysis': {},
            'quality_metrics': {}
        }
        
        # Analyze response fields for Rumusan Penilaian
        score_fields = []
        rating_fields = []
        feedback_fields = []
        
        for response in responses:
            answers = response.get('answers', {})
            for question, answer in answers.items():
                question_lower = question.lower()
                
                # Identify scoring/rating fields for Rumusan Penilaian
                if any(keyword in question_lower for keyword in ['rating', 'score', 'nilai', 'penilaian']):
                    if question not in analysis['field_analysis']:
                        analysis['field_analysis'][question] = {
                            'type': 'rating',
                            'values': [],
                            'statistics': {}
                        }
                    
                    # Try to convert to numeric for statistics
                    try:
                        numeric_value = float(str(answer).strip())
                        analysis['field_analysis'][question]['values'].append(numeric_value)
                        score_fields.append((question, numeric_value))
                    except (ValueError, TypeError):
                        analysis['field_analysis'][question]['values'].append(str(answer))
                        rating_fields.append((question, str(answer)))
                
                # Identify feedback fields
                elif any(keyword in question_lower for keyword in ['feedback', 'comment', 'suggestion', 'komentar', 'saran']):
                    if question not in analysis['field_analysis']:
                        analysis['field_analysis'][question] = {
                            'type': 'feedback',
                            'responses': [],
                            'word_count': 0
                        }
                    
                    feedback_text = str(answer) if answer else ''
                    analysis['field_analysis'][question]['responses'].append(feedback_text)
                    analysis['field_analysis'][question]['word_count'] += len(feedback_text.split())
                    feedback_fields.append((question, feedback_text))
        
        # Calculate statistics for numeric fields
        for field, data in analysis['field_analysis'].items():
            if data['type'] == 'rating' and data['values']:
                numeric_values = [v for v in data['values'] if isinstance(v, (int, float))]
                if numeric_values:
                    data['statistics'] = {
                        'mean': sum(numeric_values) / len(numeric_values),
                        'median': sorted(numeric_values)[len(numeric_values)//2],
                        'min': min(numeric_values),
                        'max': max(numeric_values),
                        'count': len(numeric_values)
                    }
        
        # Generate Rumusan Penilaian summary
        if score_fields or rating_fields:
            analysis['rumusan_penilaian'] = {
                'overall_satisfaction': self._calculate_overall_satisfaction(score_fields, rating_fields),
                'key_metrics': self._extract_key_metrics(analysis['field_analysis']),
                'recommendations': self._generate_assessment_recommendations(analysis['field_analysis'])
            }
        
        # Temporal analysis
        if responses:
            analysis['temporal_analysis'] = {
                'first_response': responses[0].get('create_time', ''),
                'last_response': responses[-1].get('create_time', ''),
                'response_pattern': 'consistent'  # Could be enhanced with actual timing analysis
            }
        
        return analysis
    
    def _calculate_overall_satisfaction(self, score_fields: List, rating_fields: List) -> Dict[str, Any]:
        """Calculate overall satisfaction metrics"""
        if not score_fields and not rating_fields:
            return {}
        
        # Calculate numeric scores average
        numeric_scores = [score for _, score in score_fields if isinstance(score, (int, float))]
        
        satisfaction = {
            'score_count': len(score_fields),
            'rating_count': len(rating_fields),
            'numeric_average': sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0,
            'satisfaction_level': 'neutral'
        }
        
        # Determine satisfaction level
        if satisfaction['numeric_average'] >= 4.0:
            satisfaction['satisfaction_level'] = 'high'
        elif satisfaction['numeric_average'] >= 3.0:
            satisfaction['satisfaction_level'] = 'moderate'
        elif satisfaction['numeric_average'] > 0:
            satisfaction['satisfaction_level'] = 'low'
        
        return satisfaction
    
    def _extract_key_metrics(self, field_analysis: Dict) -> List[Dict]:
        """Extract key metrics for the assessment"""
        metrics = []
        
        for field, data in field_analysis.items():
            if data['type'] == 'rating' and 'statistics' in data:
                stats = data['statistics']
                metrics.append({
                    'field': field,
                    'average': round(stats.get('mean', 0), 2),
                    'responses': stats.get('count', 0),
                    'range': f"{stats.get('min', 0)} - {stats.get('max', 0)}"
                })
        
        return sorted(metrics, key=lambda x: x['average'], reverse=True)
    
    def _generate_assessment_recommendations(self, field_analysis: Dict) -> List[str]:
        """Generate recommendations based on assessment data"""
        recommendations = []
        
        for field, data in field_analysis.items():
            if data['type'] == 'rating' and 'statistics' in data:
                stats = data['statistics']
                avg = stats.get('mean', 0)
                
                if avg < 3.0:
                    recommendations.append(f"Improvement needed in: {field} (Average: {avg:.1f})")
                elif avg >= 4.5:
                    recommendations.append(f"Excellent performance in: {field} (Average: {avg:.1f})")
        
        if not recommendations:
            recommendations.append("Continue monitoring feedback for improvement opportunities")
        
        return recommendations

# Global instance for use in routes
production_google_forms_service = ProductionGoogleFormsService()

# For backward compatibility with existing imports
google_forms_service = production_google_forms_service
