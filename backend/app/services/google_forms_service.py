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
        self.mock_mode = not os.path.exists(self.credentials_file)
        
        if self.mock_mode:
            logger.warning("Google credentials file not found. Running in mock mode.")
        
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
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri='http://localhost:5000/api/google-forms/callback'
            )
            
            logger.info(f"OAuth flow created successfully")
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id  # Pass user_id as state parameter
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
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri='http://localhost:5000/api/google-forms/callback'
            )
            
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
    
    def generate_form_analytics(self, user_id: str, form_id: str) -> Dict[str, Any]:
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
