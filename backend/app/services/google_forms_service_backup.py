"""
Google Forms integration service for fetching forms and responses
"""
import os
import json
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleFormsService:
    """Service for interacting with Google Forms API"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/forms.body.readonly',
        'https://www.googleapis.com/auth/forms.responses.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    def __init__(self):
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.token_file = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
        self.client_id = os.getenv('GOOGLE_CLIENT_ID', '1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls.apps.googleusercontent.com')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET', 'your_google_client_secret_here')
        self.redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:5000/api/google-forms/callback')
        
        # Check if credentials file exists
        self.mock_mode = not os.path.exists(self.credentials_file)
        
        if self.mock_mode:
            logger.warning("Google credentials file not found. Running in mock mode.")
        else:
            logger.info(f"Google Forms service initialized with client ID: {self.client_id[:20]}...")
        
    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get stored credentials for a user"""
        if self.mock_mode:
            return None
            
        try:
            # In a real implementation, you'd store user-specific tokens in the database
            # For now, we'll use a simple file-based approach
            token_path = f"tokens/user_{user_id}_token.json"
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
                if creds and creds.valid:
                    return creds
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    return creds
            return None
        except Exception as e:
            logger.error(f"Error getting credentials for user {user_id}: {e}")
            return None
    
    def get_authorization_url(self, user_id: str) -> str:
        """Get Google OAuth authorization URL"""
        if self.mock_mode:
            # Return a mock URL for testing
            return f"https://accounts.google.com/o/oauth2/auth?mock=true&user_id={user_id}"
        
        try:
            logger.info(f"Creating OAuth flow for user {user_id}")
            logger.info(f"Using credentials file: {self.credentials_file}")
            logger.info(f"Client ID: {self.client_id[:20]}...")
            logger.info(f"Redirect URI: {self.redirect_uri}")
            
            # Create flow with proper error handling
            try:
                flow = Flow.from_client_secrets_file(
                    self.credentials_file,
                    scopes=self.SCOPES,
                    redirect_uri=self.redirect_uri
                )
            except Exception as flow_error:
                logger.error(f"Error creating OAuth flow: {flow_error}")
                logger.info("Attempting to create flow with manual configuration...")
                
                # Fallback: Create flow manually if file-based creation fails
                flow = Flow.from_client_config(
                    {
                        "installed": {
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": [self.redirect_uri]
                        }
                    },
                    scopes=self.SCOPES
                )
                flow.redirect_uri = self.redirect_uri
            
            logger.info(f"OAuth flow created successfully")
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,  # Pass user_id as state parameter
                prompt='consent'  # Force consent to ensure refresh token
            )
            
            logger.info(f"Authorization URL generated: {auth_url}")
            return auth_url
        except FileNotFoundError as e:
            logger.error(f"Google credentials file not found: {e}")
            raise Exception("Google Forms integration not configured. Please add credentials.json file.")
        except Exception as e:
            logger.error(f"Error creating authorization URL: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            raise
    
    def handle_oauth_callback(self, code: str, user_id: str) -> bool:
        """Handle OAuth callback and store credentials"""
        if self.mock_mode:
            # In mock mode, pretend authentication succeeded
            logger.info(f"Mock OAuth callback for user {user_id} with code {code}")
            return True
        
        try:
            logger.info(f"Handling OAuth callback for user {user_id}")
            logger.info(f"Authorization code received: {code[:20]}...")
            
            # Create the same flow configuration as in get_auth_url
            try:
                flow = Flow.from_client_secrets_file(
                    self.credentials_file,
                    scopes=self.SCOPES,
                    redirect_uri=self.redirect_uri
                )
            except Exception as flow_error:
                logger.error(f"Error creating OAuth flow in callback: {flow_error}")
                logger.info("Using manual flow configuration for callback...")
                
                # Fallback: Create flow manually
                flow = Flow.from_client_config(
                    {
                        "installed": {
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": [self.redirect_uri]
                        }
                    },
                    scopes=self.SCOPES
                )
                flow.redirect_uri = self.redirect_uri
            
            logger.info("Fetching token with authorization code")
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            logger.info("Token fetched successfully")
            
            # Ensure tokens directory exists
            os.makedirs('tokens', exist_ok=True)
            
            # Save credentials
            token_path = f"tokens/user_{user_id}_token.json"
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            logger.info(f"Credentials saved to {token_path}")
            return True
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            return False
    
    def get_user_forms(self, user_id: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Get Google Forms accessible to the user"""
        if self.mock_mode:
            # Return mock forms for testing
            return [
                {
                    'id': 'mock_form_1',
                    'title': 'Sample Customer Feedback Form',
                    'description': 'A sample form for collecting customer feedback',
                    'publishedUrl': 'https://forms.gle/mock1',
                    'responseCount': 45,
                    'createdTime': '2024-01-01T10:00:00Z',
                    'lastModifiedTime': '2024-01-15T14:30:00Z'
                },
                {
                    'id': 'mock_form_2',
                    'title': 'Employee Survey 2024',
                    'description': 'Annual employee satisfaction survey',
                    'publishedUrl': 'https://forms.gle/mock2',
                    'responseCount': 123,
                    'createdTime': '2024-01-10T09:00:00Z',
                    'lastModifiedTime': '2024-01-20T16:45:00Z'
                },
                {
                    'id': 'mock_form_3',
                    'title': 'Event Registration Form',
                    'description': 'Registration form for upcoming conference',
                    'publishedUrl': 'https://forms.gle/mock3',
                    'responseCount': 67,
                    'createdTime': '2024-01-05T11:30:00Z',
                    'lastModifiedTime': '2024-01-12T13:20:00Z'
                }
            ]
        
        try:
            creds = self.get_credentials(user_id)
            if not creds:
                raise Exception("No valid credentials found. Please authorize access to Google Forms.")
            
            service = build('forms', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Search for Google Forms in Drive
            query = "mimeType='application/vnd.google-apps.form'"
            results = drive_service.files().list(
                q=query,
                pageSize=page_size,
                fields="files(id,name,createdTime,modifiedTime,webViewLink)"
            ).execute()
            
            forms = []
            for file in results.get('files', []):
                try:
                    # Get form details
                    form = service.forms().get(formId=file['id']).execute()
                    
                    forms.append({
                        'id': file['id'],
                        'title': file['name'],
                        'description': form.get('info', {}).get('description', ''),
                        'created_time': file.get('createdTime'),
                        'modified_time': file.get('modifiedTime'),
                        'web_view_link': file.get('webViewLink'),
                        'response_count': len(form.get('responses', [])) if 'responses' in form else 0,
                        'question_count': len(form.get('items', [])),
                        'type': 'google_form'
                    })
                except HttpError as e:
                    logger.warning(f"Could not access form {file['id']}: {e}")
                    continue
            
            return forms
            
        except Exception as e:
            logger.error(f"Error fetching Google Forms: {e}")
            raise
    
    def get_form_responses(self, user_id: str, form_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get responses for a specific Google Form"""
        try:
            creds = self.get_credentials(user_id)
            if not creds:
                raise Exception("No valid credentials found")
            
            service = build('forms', 'v1', credentials=creds)
            
            # Get form structure
            form = service.forms().get(formId=form_id).execute()
            
            # Get responses
            responses_result = service.forms().responses().list(
                formId=form_id,
                pageSize=limit
            ).execute()
            
            responses = responses_result.get('responses', [])
            
            # Parse form structure
            questions = {}
            for item in form.get('items', []):
                if 'questionItem' in item:
                    question_id = item['itemId']
                    question = item['questionItem']['question']
                    questions[question_id] = {
                        'title': question.get('questionTitle', ''),
                        'type': list(question.keys())[0] if question else 'unknown'
                    }
            
            # Parse responses
            parsed_responses = []
            for response in responses:
                parsed_response = {
                    'response_id': response.get('responseId'),
                    'create_time': response.get('createTime'),
                    'last_submitted_time': response.get('lastSubmittedTime'),
                    'answers': {}
                }
                
                for question_id, answer in response.get('answers', {}).items():
                    question_info = questions.get(question_id, {})
                    parsed_response['answers'][question_id] = {
                        'question_title': question_info.get('title', f'Question {question_id}'),
                        'question_type': question_info.get('type', 'unknown'),
                        'answer': self._extract_answer_value(answer)
                    }
                
                parsed_responses.append(parsed_response)
            
            return {
                'form_id': form_id,
                'form_title': form.get('info', {}).get('title', 'Untitled Form'),
                'form_description': form.get('info', {}).get('description', ''),
                'questions': questions,
                'responses': parsed_responses,
                'total_responses': len(parsed_responses)
            }
            
        except Exception as e:
            logger.error(f"Error fetching form responses: {e}")
            raise
    
    def _extract_answer_value(self, answer: Dict[str, Any]) -> Any:
        """Extract the actual answer value from Google Forms answer object"""
        if 'textAnswers' in answer:
            values = answer['textAnswers'].get('answers', [])
            return [v.get('value', '') for v in values]
        elif 'fileUploadAnswers' in answer:
            return [f.get('fileName', '') for f in answer['fileUploadAnswers'].get('answers', [])]
        elif 'gradeInfo' in answer:
            return answer['gradeInfo'].get('score', 0)
        else:
            return str(answer)
    
    def get_form_responses_for_automated_report(self, user_id: str, form_id: str, 
                                             date_range: str = 'last_30_days') -> Dict[str, Any]:
        """
        Enhanced method to get Google Form responses specifically for automated reports
        Includes comprehensive data processing and analysis
        """
        if self.mock_mode:
            # Return mock responses for testing
            return self._generate_mock_responses_for_report(form_id, date_range)
        
        try:
            creds = self.get_credentials(user_id)
            if not creds:
                raise Exception("No valid credentials found")

            service = build('forms', 'v1', credentials=creds)
            
            # Get form structure
            form = service.forms().get(formId=form_id).execute()
            
            # Get all responses
            responses_result = service.forms().responses().list(formId=form_id).execute()
            responses = responses_result.get('responses', [])
            
            # Filter responses by date range
            filtered_responses = self._filter_responses_by_date(responses, date_range)
            
            # Process form structure for better analysis
            form_structure = self._process_form_structure(form)
            
            # Process and analyze responses
            processed_responses = []
            for response in filtered_responses:
                processed_response = self._process_response_for_analysis(response, form_structure)
                if processed_response:
                    processed_responses.append(processed_response)
            
            # Generate comprehensive analysis
            analysis = self._generate_comprehensive_analysis(processed_responses, form_structure)
            
            return {
                'status': 'success',
                'form_info': {
                    'id': form_id,
                    'title': form.get('info', {}).get('title', 'Untitled Form'),
                    'description': form.get('info', {}).get('description', ''),
                    'published_url': form.get('publishedUrl', ''),
                    'total_questions': len(form_structure['questions'])
                },
                'responses_summary': {
                    'total_responses': len(responses),
                    'filtered_responses': len(filtered_responses),
                    'date_range': date_range,
                    'first_response': min([r.get('createTime') for r in filtered_responses if r.get('createTime')], default=None),
                    'last_response': max([r.get('createTime') for r in filtered_responses if r.get('createTime')], default=None)
                },
                'form_structure': form_structure,
                'processed_responses': processed_responses,
                'analysis': analysis,
                'raw_responses': filtered_responses  # For additional processing if needed
            }
            
        except Exception as e:
            logger.error(f"Error fetching Google Form responses for automated report: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'form_id': form_id
            }
    
    def _generate_mock_responses_for_report(self, form_id: str, date_range: str) -> Dict[str, Any]:
        """Generate mock responses for testing automated reports"""
        from datetime import datetime, timedelta
        import random
        
        # Mock form structure
        form_structure = {
            'questions': [
                {
                    'id': 'q1',
                    'title': 'What is your overall satisfaction?',
                    'type': 'choice',
                    'choices': ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied', 'Very Dissatisfied']
                },
                {
                    'id': 'q2', 
                    'title': 'Please provide additional feedback',
                    'type': 'text'
                },
                {
                    'id': 'q3',
                    'title': 'How likely are you to recommend us?',
                    'type': 'scale',
                    'scale_range': (1, 10)
                }
            ]
        }
        
        # Generate mock responses
        num_responses = random.randint(20, 100)
        base_date = datetime.now() - timedelta(days=30 if date_range == 'last_30_days' else 7)
        
        processed_responses = []
        for i in range(num_responses):
            response_date = base_date + timedelta(days=random.randint(0, 30))
            
            processed_responses.append({
                'response_id': f'mock_response_{i}',
                'create_time': response_date.isoformat() + 'Z',
                'answers': {
                    'What is your overall satisfaction?': random.choice(['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied']),
                    'Please provide additional feedback': f'Mock feedback response {i}. This is sample text.',
                    'How likely are you to recommend us?': random.randint(1, 10)
                }
            })
        
        # Generate mock analysis
        analysis = {
            'response_patterns': {
                'peak_response_days': ['Monday', 'Wednesday', 'Friday'],
                'avg_daily_responses': num_responses / 30,
                'response_trend': 'increasing' if random.random() > 0.5 else 'stable'
            },
            'question_insights': {
                'What is your overall satisfaction?': {
                    'most_common': 'Satisfied',
                    'satisfaction_score': random.uniform(3.5, 4.5),
                    'response_distribution': {
                        'Very Satisfied': random.randint(10, 30),
                        'Satisfied': random.randint(20, 40),
                        'Neutral': random.randint(5, 15),
                        'Dissatisfied': random.randint(2, 8)
                    }
                },
                'How likely are you to recommend us?': {
                    'average_score': random.uniform(6.5, 8.5),
                    'nps_score': random.randint(20, 60)
                }
            },
            'completion_stats': {
                'fully_completed': random.randint(int(num_responses * 0.8), num_responses),
                'partially_completed': random.randint(0, int(num_responses * 0.2)),
                'completion_rate': random.uniform(85, 95)
            }
        }
        
        return {
            'status': 'success',
            'form_info': {
                'id': form_id,
                'title': 'Mock Customer Satisfaction Survey',
                'description': 'A sample survey for testing automated reports',
                'published_url': f'https://forms.gle/{form_id}',
                'total_questions': len(form_structure['questions'])
            },
            'responses_summary': {
                'total_responses': num_responses,
                'filtered_responses': num_responses,
                'date_range': date_range
            },
            'form_structure': form_structure,
            'processed_responses': processed_responses,
            'analysis': analysis
        }
    
    def _filter_responses_by_date(self, responses: List[Dict], date_range: str) -> List[Dict]:
        """Filter responses based on date range"""
        from datetime import datetime, timedelta
        
        if not responses:
            return []
        
        # Calculate date threshold
        now = datetime.utcnow()
        if date_range == 'last_7_days':
            threshold = now - timedelta(days=7)
        elif date_range == 'last_30_days':
            threshold = now - timedelta(days=30)
        elif date_range == 'last_90_days':
            threshold = now - timedelta(days=90)
        elif date_range == 'last_year':
            threshold = now - timedelta(days=365)
        else:
            threshold = now - timedelta(days=30)  # Default to 30 days
        
        filtered = []
        for response in responses:
            create_time = response.get('createTime')
            if create_time:
                try:
                    response_date = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    if response_date >= threshold.replace(tzinfo=response_date.tzinfo):
                        filtered.append(response)
                except Exception as e:
                    logger.warning(f"Error parsing date {create_time}: {e}")
                    # Include response if we can't parse the date
                    filtered.append(response)
            else:
                # Include responses without dates
                filtered.append(response)
        
        return filtered
    
    def _process_form_structure(self, form: Dict) -> Dict:
        """Process Google Form structure for better analysis"""
        structure = {
            'questions': [],
            'metadata': {
                'title': form.get('info', {}).get('title', ''),
                'description': form.get('info', {}).get('description', ''),
                'revision_id': form.get('revisionId', ''),
                'settings': form.get('settings', {})
            }
        }
        
        items = form.get('items', [])
        for item in items:
            if 'questionItem' in item:
                question_item = item['questionItem']
                question = question_item.get('question', {})
                
                question_data = {
                    'id': item.get('itemId'),
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'required': question.get('required', False),
                    'question_id': question.get('questionId'),
                    'type': self._determine_question_type(question)
                }
                
                # Add type-specific information
                if 'choiceQuestion' in question:
                    choice_question = question['choiceQuestion']
                    question_data['choices'] = [
                        option.get('value', '') for option in choice_question.get('options', [])
                    ]
                    question_data['type_details'] = {
                        'type': choice_question.get('type', 'RADIO'),
                        'shuffle': choice_question.get('shuffle', False)
                    }
                
                elif 'scaleQuestion' in question:
                    scale_question = question['scaleQuestion']
                    question_data['scale_details'] = {
                        'low': scale_question.get('low', 1),
                        'high': scale_question.get('high', 5),
                        'low_label': scale_question.get('lowLabel', ''),
                        'high_label': scale_question.get('highLabel', '')
                    }
                
                elif 'textQuestion' in question:
                    text_question = question['textQuestion']
                    question_data['text_details'] = {
                        'paragraph': text_question.get('paragraph', False)
                    }
                
                structure['questions'].append(question_data)
        
        return structure
    
    def _determine_question_type(self, question: Dict) -> str:
        """Determine the type of a Google Forms question"""
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
        elif 'rowQuestion' in question:
            return 'grid'
        else:
            return 'unknown'
    
    def _process_response_for_analysis(self, response: Dict, form_structure: Dict) -> Dict:
        """Process individual response for comprehensive analysis"""
        processed = {
            'response_id': response.get('responseId'),
            'create_time': response.get('createTime'),
            'last_submitted_time': response.get('lastSubmittedTime'),
            'respondent_email': response.get('respondentEmail'),
            'answers': {},
            'completion_status': 'complete'
        }
        
        # Create question mapping for easier processing
        question_map = {q['id']: q for q in form_structure['questions']}
        
        # Process answers
        answers = response.get('answers', {})
        answered_questions = 0
        
        for question_id, answer_data in answers.items():
            question_info = question_map.get(question_id)
            if not question_info:
                continue
            
            question_title = question_info['title']
            question_type = question_info['type']
            
            # Extract answer based on type
            answer_value = self._extract_answer_by_type(answer_data, question_type)
            
            processed['answers'][question_title] = {
                'value': answer_value,
                'type': question_type,
                'question_id': question_id
            }
            answered_questions += 1
        
        # Calculate completion status
        total_questions = len(form_structure['questions'])
        if answered_questions == total_questions:
            processed['completion_status'] = 'complete'
        elif answered_questions > 0:
            processed['completion_status'] = 'partial'
        else:
            processed['completion_status'] = 'empty'
        
        processed['completion_percentage'] = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        return processed
    
    def _extract_answer_by_type(self, answer_data: Dict, question_type: str) -> Any:
        """Extract answer value based on question type"""
        if 'textAnswers' in answer_data:
            answers = answer_data['textAnswers'].get('answers', [])
            values = [a.get('value', '') for a in answers]
            return values[0] if len(values) == 1 else values
        
        elif 'choiceAnswers' in answer_data:
            answers = answer_data['choiceAnswers'].get('answers', [])
            values = [a.get('value', '') for a in answers]
            return values[0] if len(values) == 1 else values
        
        elif 'scaleAnswer' in answer_data:
            return answer_data['scaleAnswer'].get('value')
        
        elif 'dateAnswer' in answer_data:
            date_data = answer_data['dateAnswer']
            return f"{date_data.get('year')}-{date_data.get('month', 1):02d}-{date_data.get('day', 1):02d}"
        
        elif 'timeAnswer' in answer_data:
            time_data = answer_data['timeAnswer']
            return f"{time_data.get('hours', 0):02d}:{time_data.get('minutes', 0):02d}"
        
        elif 'fileUploadAnswers' in answer_data:
            files = answer_data['fileUploadAnswers'].get('answers', [])
            return [f.get('fileName', '') for f in files]
        
        else:
            return str(answer_data)
    
    def _generate_comprehensive_analysis(self, responses: List[Dict], form_structure: Dict) -> Dict:
        """Generate comprehensive analysis of form responses"""
        if not responses:
            return {'message': 'No responses to analyze'}
        
        analysis = {
            'response_patterns': self._analyze_response_patterns(responses),
            'question_insights': self._analyze_questions(responses, form_structure),
            'completion_stats': self._analyze_completion(responses),
            'quality_metrics': self._analyze_quality(responses),
            'temporal_analysis': self._analyze_temporal_patterns(responses)
        }
        
        return analysis
    
    def _analyze_response_patterns(self, responses: List[Dict]) -> Dict:
        """Analyze response submission patterns"""
        from collections import Counter
        import pandas as pd
        
        if not responses:
            return {}
        
        # Extract submission times
        submission_times = []
        for response in responses:
            create_time = response.get('create_time')
            if create_time:
                try:
                    dt = pd.to_datetime(create_time)
                    submission_times.append(dt)
                except:
                    continue
        
        if not submission_times:
            return {'message': 'No valid submission times found'}
        
        # Analyze patterns
        df = pd.DataFrame({'submission_time': submission_times})
        df['hour'] = df['submission_time'].dt.hour
        df['day_of_week'] = df['submission_time'].dt.day_name()
        df['date'] = df['submission_time'].dt.date
        
        return {
            'total_responses': len(responses),
            'date_range': {
                'first': min(submission_times).isoformat(),
                'last': max(submission_times).isoformat(),
                'span_days': (max(submission_times) - min(submission_times)).days
            },
            'hourly_distribution': df['hour'].value_counts().to_dict(),
            'daily_distribution': df['day_of_week'].value_counts().to_dict(),
            'peak_hour': df['hour'].value_counts().index[0] if not df.empty else None,
            'peak_day': df['day_of_week'].value_counts().index[0] if not df.empty else None,
            'avg_responses_per_day': len(responses) / max((max(submission_times) - min(submission_times)).days, 1)
        }
    
    def _analyze_questions(self, responses: List[Dict], form_structure: Dict) -> Dict:
        """Analyze individual questions"""
        question_analysis = {}
        
        for question in form_structure['questions']:
            question_title = question['title']
            question_type = question['type']
            
            # Collect answers for this question
            answers = []
            for response in responses:
                if question_title in response['answers']:
                    answer_data = response['answers'][question_title]
                    answers.append(answer_data['value'])
            
            if not answers:
                continue
            
            analysis = {
                'response_count': len(answers),
                'response_rate': len(answers) / len(responses) * 100,
                'question_type': question_type
            }
            
            # Type-specific analysis
            if question_type == 'choice':
                from collections import Counter
                answer_counts = Counter([str(a) for a in answers if a])
                analysis.update({
                    'most_common_answer': answer_counts.most_common(1)[0] if answer_counts else None,
                    'answer_distribution': dict(answer_counts),
                    'unique_answers': len(answer_counts)
                })
            
            elif question_type == 'scale':
                numeric_answers = [a for a in answers if isinstance(a, (int, float))]
                if numeric_answers:
                    import statistics
                    analysis.update({
                        'average_score': statistics.mean(numeric_answers),
                        'median_score': statistics.median(numeric_answers),
                        'min_score': min(numeric_answers),
                        'max_score': max(numeric_answers),
                        'score_distribution': Counter(numeric_answers)
                    })
            
            elif question_type == 'text':
                text_answers = [str(a) for a in answers if a]
                if text_answers:
                    analysis.update({
                        'avg_length': sum(len(a) for a in text_answers) / len(text_answers),
                        'max_length': max(len(a) for a in text_answers),
                        'min_length': min(len(a) for a in text_answers),
                        'empty_responses': len([a for a in answers if not a or str(a).strip() == ''])
                    })
            
            question_analysis[question_title] = analysis
        
        return question_analysis
    
    def _analyze_completion(self, responses: List[Dict]) -> Dict:
        """Analyze response completion rates"""
        if not responses:
            return {}
        
        completion_stats = {
            'complete': 0,
            'partial': 0,
            'empty': 0
        }
        
        completion_percentages = []
        
        for response in responses:
            status = response.get('completion_status', 'unknown')
            if status in completion_stats:
                completion_stats[status] += 1
            
            percentage = response.get('completion_percentage', 0)
            completion_percentages.append(percentage)
        
        total_responses = len(responses)
        
        return {
            'completion_counts': completion_stats,
            'completion_rates': {
                'complete': completion_stats['complete'] / total_responses * 100,
                'partial': completion_stats['partial'] / total_responses * 100,
                'empty': completion_stats['empty'] / total_responses * 100
            },
            'average_completion': sum(completion_percentages) / len(completion_percentages) if completion_percentages else 0,
            'total_responses': total_responses
        }
    
    def _analyze_quality(self, responses: List[Dict]) -> Dict:
        """Analyze response quality metrics"""
        if not responses:
            return {}
        
        quality_metrics = {
            'high_quality_responses': 0,
            'medium_quality_responses': 0,
            'low_quality_responses': 0,
            'quality_score': 0
        }
        
        total_responses = len(responses)
        quality_scores = []
        
        for response in responses:
            score = 0
            
            # Check completion percentage
            completion = response.get('completion_percentage', 0)
            if completion >= 90:
                score += 40
            elif completion >= 70:
                score += 30
            elif completion >= 50:
                score += 20
            
            # Check answer quality (length, detail)
            for answer_data in response.get('answers', {}).values():
                answer = answer_data.get('value')
                if answer and str(answer).strip():
                    if len(str(answer)) > 20:  # Detailed response
                        score += 10
                    elif len(str(answer)) > 5:  # Moderate response
                        score += 5
                    else:  # Short response
                        score += 2
            
            # Categorize quality
            if score >= 70:
                quality_metrics['high_quality_responses'] += 1
            elif score >= 40:
                quality_metrics['medium_quality_responses'] += 1
            else:
                quality_metrics['low_quality_responses'] += 1
            
            quality_scores.append(score)
        
        quality_metrics['quality_score'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        quality_metrics['quality_distribution'] = {
            'high_quality_rate': quality_metrics['high_quality_responses'] / total_responses * 100,
            'medium_quality_rate': quality_metrics['medium_quality_responses'] / total_responses * 100,
            'low_quality_rate': quality_metrics['low_quality_responses'] / total_responses * 100
        }
        
        return quality_metrics
    
    def _analyze_temporal_patterns(self, responses: List[Dict]) -> Dict:
        """Analyze temporal submission patterns"""
        import pandas as pd
        
        if not responses:
            return {}
        
        # Extract submission times
        submission_times = []
        for response in responses:
            create_time = response.get('create_time')
            if create_time:
                try:
                    dt = pd.to_datetime(create_time)
                    submission_times.append(dt)
                except:
                    continue
        
        if len(submission_times) < 2:
            return {'message': 'Insufficient data for temporal analysis'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame({'time': submission_times})
        df = df.sort_values('time')
        df['date'] = df['time'].dt.date
        
        # Group by date and count
        daily_counts = df.groupby('date').size()
        
        # Calculate trend
        if len(daily_counts) > 1:
            import numpy as np
            x = np.arange(len(daily_counts))
            y = daily_counts.values.astype(float)
            trend_slope = np.polyfit(x, y, 1)[0]
        else:
            trend_slope = 0
        
        return {
            'trend_direction': 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable',
            'trend_strength': abs(trend_slope),
            'peak_submission_date': daily_counts.idxmax() if not daily_counts.empty else None,
            'lowest_submission_date': daily_counts.idxmin() if not daily_counts.empty else None,
            'average_daily_submissions': daily_counts.mean(),
            'submission_consistency': 1 / (daily_counts.std() + 1) if not daily_counts.empty else 0,
            'total_days_with_responses': len(daily_counts)
        }
        """Generate analytics for a Google Form"""
        try:
            form_data = self.get_form_responses(user_id, form_id)
            
            analytics = {
                'form_id': form_id,
                'form_title': form_data['form_title'],
                'total_responses': form_data['total_responses'],
                'questions_analysis': {},
                'response_timeline': [],
                'summary_stats': {}
            }
            
            if not form_data['responses']:
                return analytics
            
            # Analyze each question
            for question_id, question_info in form_data['questions'].items():
                question_analytics = {
                    'question_title': question_info['title'],
                    'question_type': question_info['type'],
                    'response_count': 0,
                    'unique_answers': set(),
                    'answer_distribution': {}
                }
                
                for response in form_data['responses']:
                    if question_id in response['answers']:
                        answer = response['answers'][question_id]['answer']
                        question_analytics['response_count'] += 1
                        
                        # Handle different answer types
                        if isinstance(answer, list):
                            for ans in answer:
                                question_analytics['unique_answers'].add(str(ans))
                                question_analytics['answer_distribution'][str(ans)] = \
                                    question_analytics['answer_distribution'].get(str(ans), 0) + 1
                        else:
                            question_analytics['unique_answers'].add(str(answer))
                            question_analytics['answer_distribution'][str(answer)] = \
                                question_analytics['answer_distribution'].get(str(answer), 0) + 1
                
                # Convert set to list for JSON serialization
                question_analytics['unique_answers'] = list(question_analytics['unique_answers'])
                analytics['questions_analysis'][question_id] = question_analytics
            
            # Generate summary stats
            analytics['summary_stats'] = {
                'total_questions': len(form_data['questions']),
                'avg_completion_rate': sum(
                    len(r['answers']) for r in form_data['responses']
                ) / len(form_data['responses']) / len(form_data['questions']) * 100 if form_data['responses'] else 0
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating form analytics: {e}")
            raise

# Global instance
google_forms_service = GoogleFormsService()
