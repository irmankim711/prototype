"""
Production Google Forms Service - ZERO MOCK DATA
Real Google Forms API integration for production deployment
"""

import os
import json
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

from app.models.production import FormIntegration, FormResponse, Participant
from app import db

logger = logging.getLogger(__name__)

class GoogleFormsService:
    """Production Google Forms Service - ZERO MOCK DATA"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.tokens_dir = os.getenv('GOOGLE_TOKEN_FILE', './tokens/google/')
        
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing required Google OAuth configuration. Check environment variables.")
        
        # Ensure directories exist
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        self.scopes = [
            'https://www.googleapis.com/auth/forms.body.readonly',
            'https://www.googleapis.com/auth/forms.responses.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]

        # NO MOCK MODE - This is production only
        self.mock_mode = False  # ALWAYS FALSE for production
        
        logger.info(f"Google Forms Service initialized for production with client ID: {self.client_id[:20]}...")

    def get_authorization_url(self, user_id: str) -> Dict[str, str]:
        """Get real Google OAuth authorization URL - NO MOCK DATA"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,
                prompt='consent'  # Force consent to get refresh token
            )
            
            logger.info(f"Generated real Google OAuth URL for user {user_id}")
            
            return {
                'authorization_url': authorization_url,
                'state': state,
                'status': 'success',
                'platform': 'google_forms'
            }
            
        except Exception as e:
            logger.error(f"Error generating Google authorization URL: {str(e)}")
            raise Exception(f"Failed to generate authorization URL: {str(e)}")

    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle real OAuth callback and store credentials - NO MOCK DATA"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            flow.fetch_token(code=code)
            
            # Store credentials for user
            credentials = flow.credentials
            token_path = os.path.join(self.tokens_dir, f"user_{state}_token.pickle")
            
            with open(token_path, 'wb') as token_file:
                pickle.dump(credentials, token_file)
            
            # Store token in database for tracking
            from app.models.production import UserToken, User
            
            user = User.query.filter_by(id=state).first()
            if user:
                # Remove existing Google tokens for this user
                existing_tokens = UserToken.query.filter_by(
                    user_id=user.id,
                    platform='google'
                ).all()
                
                for token in existing_tokens:
                    db.session.delete(token)
                
                # Create new token record
                user_token = UserToken(
                    user_id=user.id,
                    platform='google',
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    expires_at=credentials.expiry,
                    scopes=self.scopes,
                    platform_user_id=state
                )
                db.session.add(user_token)
                db.session.commit()
            
            logger.info(f"Successfully stored real Google OAuth credentials for user {state}")
            
            return {
                'status': 'success',
                'user_id': state,
                'message': 'Google Forms authentication successful',
                'platform': 'google_forms'
            }
            
        except Exception as e:
            logger.error(f"Google OAuth callback error: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")

    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get stored credentials for user - NO MOCK DATA"""
        token_path = os.path.join(self.tokens_dir, f"user_{user_id}_token.pickle")
        
        if not os.path.exists(token_path):
            return None
            
        try:
            with open(token_path, 'rb') as token_file:
                credentials = pickle.load(token_file)
            
            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Save refreshed credentials
                with open(token_path, 'wb') as token_file:
                    pickle.dump(credentials, token_file)
                
                # Update database token
                from app.models.production import UserToken
                user_token = UserToken.query.filter_by(
                    platform_user_id=user_id,
                    platform='google'
                ).first()
                
                if user_token:
                    user_token.access_token = credentials.token
                    user_token.expires_at = credentials.expiry
                    user_token.update_usage()
                    db.session.commit()
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error loading Google credentials: {str(e)}")
            return None

    def get_user_forms(self, user_id: str, page_size: int = 50) -> Dict[str, Any]:
        """Get real Google Forms for authenticated user - NO MOCK DATA"""
        credentials = self.get_credentials(user_id)
        if not credentials:
            raise Exception("User not authenticated. Please authorize access to Google Forms.")
        
        try:
            # Build services
            drive_service = build('drive', 'v3', credentials=credentials)
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Get forms from Google Drive
            query = "mimeType='application/vnd.google-apps.form'"
            results = drive_service.files().list(
                q=query, 
                pageSize=page_size,
                fields="files(id,name,createdTime,modifiedTime,webViewLink)"
            ).execute()
            
            forms = results.get('files', [])
            processed_forms = []
            
            logger.info(f"Found {len(forms)} real Google Forms for user {user_id}")
            
            for form_file in forms:
                try:
                    # Get form details from Forms API
                    form = forms_service.forms().get(formId=form_file['id']).execute()
                    
                    # Get response count
                    responses_result = forms_service.forms().responses().list(
                        formId=form_file['id']
                    ).execute()
                    response_count = len(responses_result.get('responses', []))
                    
                    processed_form = {
                        'id': form_file['id'],
                        'title': form_file['name'],
                        'description': form.get('info', {}).get('description', ''),
                        'created_time': form_file.get('createdTime'),
                        'modified_time': form_file.get('modifiedTime'),
                        'web_view_link': form_file.get('webViewLink'),
                        'responder_uri': form.get('responderUri'),
                        'question_count': len(form.get('items', [])),
                        'response_count': response_count,
                        'accepts_responses': form.get('settings', {}).get('quizSettings', {}).get('isQuiz', True),
                        'platform': 'google_forms'
                    }
                    processed_forms.append(processed_form)
                    
                except HttpError as e:
                    logger.warning(f"Could not access form {form_file['id']}: {str(e)}")
                    continue
            
            return {
                'forms': processed_forms,
                'total_count': len(processed_forms),
                'status': 'success',
                'platform': 'google_forms'
            }
            
        except Exception as e:
            logger.error(f"Error fetching user forms: {str(e)}")
            raise Exception(f"Failed to fetch forms: {str(e)}")

    def get_form_responses(self, user_id: str, form_id: str) -> Dict[str, Any]:
        """Get real form responses from Google Forms - NO MOCK DATA"""
        credentials = self.get_credentials(user_id)
        if not credentials:
            raise Exception("User not authenticated")
        
        try:
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Get form structure
            form = forms_service.forms().get(formId=form_id).execute()
            
            # Get responses
            responses = forms_service.forms().responses().list(formId=form_id).execute()
            
            # Process responses
            processed_responses = []
            form_items = {item['itemId']: item for item in form.get('items', [])}
            
            logger.info(f"Processing {len(responses.get('responses', []))} real responses for form {form_id}")
            
            for response in responses.get('responses', []):
                processed_response = {
                    'response_id': response['responseId'],
                    'create_time': response['createTime'],
                    'last_submitted_time': response['lastSubmittedTime'],
                    'answers': {}
                }
                
                for answer_id, answer in response.get('answers', {}).items():
                    if answer_id in form_items:
                        question_item = form_items[answer_id]
                        question_title = question_item.get('title', f'Question {answer_id}')
                        
                        # Extract answer based on type
                        answer_value = self._extract_answer_value(answer)
                        processed_response['answers'][question_title] = answer_value
                
                processed_responses.append(processed_response)
            
            return {
                'form_title': form.get('info', {}).get('title', 'Untitled Form'),
                'form_description': form.get('info', {}).get('description', ''),
                'response_count': len(processed_responses),
                'responses': processed_responses,
                'status': 'success',
                'platform': 'google_forms'
            }
            
        except Exception as e:
            logger.error(f"Error fetching form responses: {str(e)}")
            raise Exception(f"Failed to fetch responses: {str(e)}")

    def _extract_answer_value(self, answer: Dict) -> Any:
        """Extract answer value based on answer type - NO MOCK DATA"""
        if 'textAnswers' in answer:
            return answer['textAnswers']['answers'][0]['value']
        elif 'choiceAnswers' in answer:
            return [choice['value'] for choice in answer['choiceAnswers']['answers']]
        elif 'scaleAnswer' in answer:
            return answer['scaleAnswer']['value']
        elif 'dateAnswer' in answer:
            date_obj = answer['dateAnswer']
            return f"{date_obj['year']}-{date_obj['month']:02d}-{date_obj['day']:02d}"
        elif 'timeAnswer' in answer:
            time_obj = answer['timeAnswer']
            return f"{time_obj.get('hours', 0):02d}:{time_obj.get('minutes', 0):02d}"
        elif 'fileUploadAnswers' in answer:
            return [file_answer['fileId'] for file_answer in answer['fileUploadAnswers']['answers']]
        else:
            return str(answer)

    def sync_form_to_database(self, user_id: str, form_id: str, program_id: int) -> Dict[str, Any]:
        """Sync real Google Form responses to database - NO MOCK DATA"""
        try:
            # Get form responses
            form_data = self.get_form_responses(user_id, form_id)
            
            # Check if integration exists
            integration = FormIntegration.query.filter_by(
                program_id=program_id,
                form_id=form_id,
                platform='google_forms'
            ).first()
            
            if not integration:
                # Create new integration
                integration = FormIntegration(
                    program_id=program_id,
                    platform='google_forms',
                    form_id=form_id,
                    form_title=form_data.get('form_title'),
                    form_url=f"https://docs.google.com/forms/d/{form_id}/edit",
                    oauth_user_id=user_id,
                    created_by=user_id
                )
                db.session.add(integration)
                db.session.flush()  # Get the ID
            
            # Update integration metadata
            integration.last_sync = datetime.utcnow()
            integration.sync_count = (integration.sync_count or 0) + 1
            integration.integration_status = 'active'
            
            # Process responses and create/update participants
            participants_created = 0
            participants_updated = 0
            responses_processed = 0
            
            for response in form_data.get('responses', []):
                # Store the raw response
                form_response = FormResponse(
                    integration_id=integration.id,
                    external_response_id=response['response_id'],
                    response_data=response,
                    submitted_at=datetime.fromisoformat(response['create_time'].replace('Z', '+00:00'))
                )
                
                # Normalize the data
                form_response.normalize_response_data()
                db.session.add(form_response)
                
                # Create/update participant if we have enough data
                normalized_data = form_response.normalized_data
                if normalized_data and normalized_data.get('email'):
                    participant_data = self._map_response_to_participant(normalized_data)
                    
                    # Check if participant exists
                    existing = Participant.query.filter_by(
                        program_id=program_id,
                        email=participant_data['email']
                    ).first()
                    
                    if existing:
                        # Update existing participant
                        for key, value in participant_data.items():
                            if value:  # Only update non-empty values
                                setattr(existing, key, value)
                        participants_updated += 1
                    else:
                        # Create new participant
                        new_participant = Participant(
                            program_id=program_id,
                            form_response_id=response['response_id'],
                            registration_source='google_forms',
                            **participant_data
                        )
                        db.session.add(new_participant)
                        participants_created += 1
                
                responses_processed += 1
            
            db.session.commit()
            
            logger.info(f"Successfully synced {responses_processed} responses from Google Form {form_id}")
            
            return {
                'status': 'success',
                'participants_created': participants_created,
                'participants_updated': participants_updated,
                'responses_processed': responses_processed,
                'total_responses': len(form_data.get('responses', [])),
                'integration_id': integration.id,
                'platform': 'google_forms'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing Google form to database: {str(e)}")
            raise Exception(f"Sync failed: {str(e)}")

    def _map_response_to_participant(self, normalized_data: Dict) -> Dict[str, Any]:
        """Map normalized form data to participant fields - NO MOCK DATA"""
        participant_data = {}
        
        # Direct mapping for standard fields
        field_mapping = {
            'full_name': normalized_data.get('name'),
            'email': normalized_data.get('email'),
            'phone': normalized_data.get('phone'),
            'identification_number': normalized_data.get('ic'),
            'gender': normalized_data.get('gender'),
            'organization': normalized_data.get('organization'),
            'position': normalized_data.get('position'),
            'department': normalized_data.get('department')
        }
        
        # Only include fields with values
        for field, value in field_mapping.items():
            if value and str(value).strip():
                participant_data[field] = str(value).strip()
        
        return participant_data

    def get_form_analytics(self, user_id: str, form_id: str) -> Dict[str, Any]:
        """Get real form analytics from Google Forms - NO MOCK DATA"""
        try:
            form_data = self.get_form_responses(user_id, form_id)
            responses = form_data.get('responses', [])
            
            if not responses:
                return {
                    'status': 'success',
                    'analytics': {
                        'total_responses': 0,
                        'message': 'No responses available for analysis'
                    }
                }
            
            # Calculate real analytics
            analytics = {
                'total_responses': len(responses),
                'response_rate_analysis': self._calculate_response_patterns(responses),
                'completion_analysis': self._analyze_completion_quality(responses),
                'question_analytics': self._analyze_question_responses(responses),
                'temporal_analysis': self._analyze_submission_timing(responses),
                'data_quality_metrics': self._calculate_data_quality(responses)
            }
            
            return {
                'status': 'success',
                'analytics': analytics,
                'form_title': form_data.get('form_title'),
                'platform': 'google_forms'
            }
            
        except Exception as e:
            logger.error(f"Error calculating form analytics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _calculate_response_patterns(self, responses: List[Dict]) -> Dict[str, Any]:
        """Calculate real response patterns - NO MOCK DATA"""
        submission_hours = []
        submission_days = []
        
        for response in responses:
            try:
                create_time = datetime.fromisoformat(response['create_time'].replace('Z', '+00:00'))
                submission_hours.append(create_time.hour)
                submission_days.append(create_time.strftime('%A'))
            except:
                continue
        
        from collections import Counter
        
        return {
            'peak_hours': dict(Counter(submission_hours).most_common(5)),
            'peak_days': dict(Counter(submission_days).most_common(7)),
            'total_analyzed': len(submission_hours)
        }

    def _analyze_completion_quality(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze real completion quality - NO MOCK DATA"""
        completion_scores = []
        
        for response in responses:
            answers = response.get('answers', {})
            if answers:
                filled_fields = len([v for v in answers.values() if v and str(v).strip()])
                total_fields = len(answers)
                completion_score = (filled_fields / total_fields * 100) if total_fields > 0 else 0
                completion_scores.append(completion_score)
        
        if completion_scores:
            return {
                'average_completion': sum(completion_scores) / len(completion_scores),
                'completion_distribution': {
                    'high_completion_80_plus': len([s for s in completion_scores if s >= 80]),
                    'medium_completion_50_79': len([s for s in completion_scores if 50 <= s < 80]),
                    'low_completion_below_50': len([s for s in completion_scores if s < 50])
                },
                'total_responses_analyzed': len(completion_scores)
            }
        
        return {'message': 'No completion data available'}

    def _analyze_question_responses(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze real question response patterns - NO MOCK DATA"""
        question_stats = {}
        
        for response in responses:
            for question, answer in response.get('answers', {}).items():
                if question not in question_stats:
                    question_stats[question] = {
                        'response_count': 0,
                        'unique_answers': set(),
                        'empty_responses': 0
                    }
                
                question_stats[question]['response_count'] += 1
                
                if answer and str(answer).strip():
                    question_stats[question]['unique_answers'].add(str(answer))
                else:
                    question_stats[question]['empty_responses'] += 1
        
        # Convert sets to counts for JSON serialization
        processed_stats = {}
        for question, stats in question_stats.items():
            processed_stats[question] = {
                'total_responses': stats['response_count'],
                'unique_answer_count': len(stats['unique_answers']),
                'empty_response_count': stats['empty_responses'],
                'response_rate': ((stats['response_count'] - stats['empty_responses']) / stats['response_count'] * 100) if stats['response_count'] > 0 else 0
            }
        
        return processed_stats

    def _analyze_submission_timing(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze real submission timing patterns - NO MOCK DATA"""
        if not responses:
            return {'message': 'No timing data available'}
        
        submission_times = []
        for response in responses:
            try:
                create_time = datetime.fromisoformat(response['create_time'].replace('Z', '+00:00'))
                submission_times.append(create_time)
            except:
                continue
        
        if len(submission_times) < 2:
            return {'message': 'Insufficient data for timing analysis'}
        
        submission_times.sort()
        
        return {
            'first_response': submission_times[0].isoformat(),
            'latest_response': submission_times[-1].isoformat(),
            'collection_period_days': (submission_times[-1] - submission_times[0]).days,
            'responses_per_day': len(submission_times) / max((submission_times[-1] - submission_times[0]).days, 1)
        }

    def _calculate_data_quality(self, responses: List[Dict]) -> Dict[str, Any]:
        """Calculate real data quality metrics - NO MOCK DATA"""
        quality_scores = []
        email_valid_count = 0
        phone_valid_count = 0
        name_valid_count = 0
        
        for response in responses:
            response_quality = 0
            checks_performed = 0
            
            answers = response.get('answers', {})
            
            # Check email format
            for question, answer in answers.items():
                if 'email' in question.lower() and answer:
                    checks_performed += 1
                    if '@' in str(answer) and '.' in str(answer):
                        response_quality += 1
                        email_valid_count += 1
                
                # Check name completeness
                if 'name' in question.lower() and answer:
                    checks_performed += 1
                    if len(str(answer).strip()) > 2:
                        response_quality += 1
                        name_valid_count += 1
                
                # Check phone format
                if 'phone' in question.lower() and answer:
                    checks_performed += 1
                    phone_clean = str(answer).replace('-', '').replace(' ', '').replace('+', '')
                    if len(phone_clean) >= 10 and phone_clean.isdigit():
                        response_quality += 1
                        phone_valid_count += 1
            
            if checks_performed > 0:
                quality_scores.append((response_quality / checks_performed) * 100)
        
        return {
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'email_validity_rate': (email_valid_count / len(responses) * 100) if responses else 0,
            'phone_validity_rate': (phone_valid_count / len(responses) * 100) if responses else 0,
            'name_completeness_rate': (name_valid_count / len(responses) * 100) if responses else 0,
            'total_responses_analyzed': len(responses)
        }
