"""
Form Data Processors
Handles normalizing data from different form sources
"""

import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
from flask import current_app

from ..models import db, FormDataSubmission

logger = logging.getLogger(__name__)

class FormProcessor:
    """Base class for processing form data from various sources"""
    
    def __init__(self, data_source):
        self.data_source = data_source
        self.source_type = data_source.source_type
        self.field_mapping = data_source.field_mapping or {}
        
    def process_webhook_data(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process incoming webhook data"""
        try:
            if self.source_type == 'google_forms':
                return self._process_google_forms_webhook(webhook_data, headers)
            elif self.source_type == 'microsoft_forms':
                return self._process_microsoft_forms_webhook(webhook_data, headers)
            elif self.source_type == 'zoho_forms':
                return self._process_zoho_forms_webhook(webhook_data, headers)
            elif self.source_type == 'typeform':
                return self._process_typeform_webhook(webhook_data, headers)
            elif self.source_type == 'custom':
                return self._process_custom_webhook(webhook_data, headers)
            else:
                return self._process_generic_webhook(webhook_data, headers)
                
        except Exception as e:
            logger.error(f"Error processing webhook data: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'processing_error': str(e)}
            }
    
    def manual_sync(self) -> Dict:
        """Manually sync data from the form source API"""
        try:
            if self.source_type == 'google_forms':
                return self._sync_google_forms()
            elif self.source_type == 'microsoft_forms':
                return self._sync_microsoft_forms()
            elif self.source_type == 'zoho_forms':
                return self._sync_zoho_forms()
            elif self.source_type == 'typeform':
                return self._sync_typeform()
            else:
                return {
                    'status': 'error',
                    'message': f'Manual sync not implemented for {self.source_type}',
                    'error_count': 1,
                    'new_submissions': 0,
                    'updated_submissions': 0
                }
                
        except Exception as e:
            logger.error(f"Error during manual sync: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'sync_error': str(e)}
            }
    
    def _process_google_forms_webhook(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process Google Forms webhook data"""
        try:
            # Google Forms sends notifications through Pub/Sub or direct webhooks
            form_id = webhook_data.get('formId') or headers.get('X-Goog-Resource-ID')
            
            if not form_id:
                return {
                    'status': 'error',
                    'message': 'No form ID found in webhook data',
                    'error_count': 1,
                    'new_submissions': 0,
                    'updated_submissions': 0
                }
            
            # For Google Forms, we need to fetch the actual responses via API
            # This webhook usually just notifies us that there's new data
            return self._sync_google_forms()
            
        except Exception as e:
            logger.error(f"Google Forms webhook processing error: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'google_forms_error': str(e)}
            }
    
    def _process_microsoft_forms_webhook(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process Microsoft Forms webhook data"""
        try:
            # Microsoft Forms webhook structure
            if 'value' in webhook_data:
                submissions_data = webhook_data['value']
            elif 'formResponse' in webhook_data:
                submissions_data = [webhook_data]
            else:
                submissions_data = [webhook_data]
            
            new_count = 0
            updated_count = 0
            errors = []
            
            for submission_data in submissions_data:
                try:
                    result = self._save_normalized_submission(
                        submission_data,
                        'microsoft_forms'
                    )
                    
                    if result['created']:
                        new_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    errors.append(str(e))
                    logger.error(f"Error processing Microsoft Forms submission: {str(e)}")
            
            return {
                'status': 'success' if not errors else 'partial',
                'new_submissions': new_count,
                'updated_submissions': updated_count,
                'error_count': len(errors),
                'errors': errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Microsoft Forms webhook processing error: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'microsoft_forms_error': str(e)}
            }
    
    def _process_zoho_forms_webhook(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process Zoho Forms webhook data"""
        try:
            # Zoho Forms webhook structure
            new_count = 0
            updated_count = 0
            errors = []
            
            # Zoho sends form data directly in webhook
            if 'form_data' in webhook_data:
                submission_data = webhook_data
            else:
                submission_data = webhook_data
            
            try:
                result = self._save_normalized_submission(
                    submission_data,
                    'zoho_forms'
                )
                
                if result['created']:
                    new_count = 1
                else:
                    updated_count = 1
                    
            except Exception as e:
                errors.append(str(e))
                logger.error(f"Error processing Zoho Forms submission: {str(e)}")
            
            return {
                'status': 'success' if not errors else 'error',
                'new_submissions': new_count,
                'updated_submissions': updated_count,
                'error_count': len(errors),
                'errors': errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Zoho Forms webhook processing error: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'zoho_forms_error': str(e)}
            }
    
    def _process_typeform_webhook(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process Typeform webhook data"""
        try:
            # Typeform webhook structure
            form_response = webhook_data.get('form_response', {})
            
            if not form_response:
                return {
                    'status': 'error',
                    'message': 'No form_response found in webhook data',
                    'error_count': 1,
                    'new_submissions': 0,
                    'updated_submissions': 0
                }
            
            try:
                result = self._save_normalized_submission(
                    webhook_data,
                    'typeform'
                )
                
                return {
                    'status': 'success',
                    'new_submissions': 1 if result['created'] else 0,
                    'updated_submissions': 0 if result['created'] else 1,
                    'error_count': 0
                }
                
            except Exception as e:
                logger.error(f"Error processing Typeform submission: {str(e)}")
                return {
                    'status': 'error',
                    'error_count': 1,
                    'new_submissions': 0,
                    'updated_submissions': 0,
                    'errors': {'typeform_error': str(e)}
                }
                
        except Exception as e:
            logger.error(f"Typeform webhook processing error: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'typeform_error': str(e)}
            }
    
    def _process_custom_webhook(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process custom form webhook data"""
        try:
            result = self._save_normalized_submission(
                webhook_data,
                'custom'
            )
            
            return {
                'status': 'success',
                'new_submissions': 1 if result['created'] else 0,
                'updated_submissions': 0 if result['created'] else 1,
                'error_count': 0
            }
            
        except Exception as e:
            logger.error(f"Custom webhook processing error: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'custom_error': str(e)}
            }
    
    def _process_generic_webhook(self, webhook_data: Dict, headers: Dict) -> Dict:
        """Process generic webhook data (fallback)"""
        try:
            result = self._save_normalized_submission(
                webhook_data,
                'generic'
            )
            
            return {
                'status': 'success',
                'new_submissions': 1 if result['created'] else 0,
                'updated_submissions': 0 if result['created'] else 1,
                'error_count': 0
            }
            
        except Exception as e:
            logger.error(f"Generic webhook processing error: {str(e)}")
            return {
                'status': 'error',
                'error_count': 1,
                'new_submissions': 0,
                'updated_submissions': 0,
                'errors': {'generic_error': str(e)}
            }
    
    def _save_normalized_submission(self, raw_data: Dict, source_type: str) -> Dict:
        """Save a normalized submission to the database"""
        try:
            # Extract external ID
            external_id = self._extract_external_id(raw_data, source_type)
            
            # Normalize the data
            normalized_data = self._normalize_submission_data(raw_data, source_type)
            
            # Extract metadata
            submitted_at = self._extract_submitted_at(raw_data, source_type)
            submitter_email = self._extract_submitter_email(raw_data, source_type)
            submitter_name = self._extract_submitter_name(raw_data, source_type)
            
            # Check if submission already exists
            existing_submission = None
            if external_id:
                existing_submission = FormDataSubmission.query.filter_by(
                    data_source_id=self.data_source.id,
                    external_id=external_id
                ).first()
            
            if existing_submission:
                # Update existing submission
                existing_submission.raw_data = raw_data
                existing_submission.normalized_data = normalized_data
                existing_submission.processing_status = 'processed'
                existing_submission.updated_at = datetime.utcnow()
                created = False
            else:
                # Create new submission
                submission = FormDataSubmission(
                    data_source_id=self.data_source.id,
                    external_id=external_id,
                    raw_data=raw_data,
                    normalized_data=normalized_data,
                    submitted_at=submitted_at,
                    submitter_email=submitter_email,
                    submitter_name=submitter_name,
                    processing_status='processed'
                )
                db.session.add(submission)
                created = True
            
            db.session.commit()
            
            return {
                'created': created,
                'submission_id': existing_submission.id if existing_submission else submission.id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving normalized submission: {str(e)}")
            raise e
    
    def _extract_external_id(self, raw_data: Dict, source_type: str) -> Optional[str]:
        """Extract external ID from raw submission data"""
        if source_type == 'google_forms':
            return raw_data.get('response_id') or raw_data.get('responseId')
        elif source_type == 'microsoft_forms':
            return raw_data.get('id') or raw_data.get('responseId')
        elif source_type == 'zoho_forms':
            return raw_data.get('submission_id') or raw_data.get('formData', {}).get('submission_id')
        elif source_type == 'typeform':
            form_response = raw_data.get('form_response', {})
            return form_response.get('token') or form_response.get('response_id')
        else:
            return raw_data.get('id') or raw_data.get('submission_id') or raw_data.get('response_id')
    
    def _extract_submitted_at(self, raw_data: Dict, source_type: str) -> datetime:
        """Extract submission timestamp"""
        timestamp_str = None
        
        if source_type == 'google_forms':
            timestamp_str = raw_data.get('timestamp') or raw_data.get('createTime')
        elif source_type == 'microsoft_forms':
            timestamp_str = raw_data.get('submissionDateTime') or raw_data.get('createdDateTime')
        elif source_type == 'zoho_forms':
            timestamp_str = raw_data.get('timestamp') or raw_data.get('formData', {}).get('timestamp')
        elif source_type == 'typeform':
            form_response = raw_data.get('form_response', {})
            timestamp_str = form_response.get('submitted_at')
        else:
            timestamp_str = raw_data.get('timestamp') or raw_data.get('submitted_at') or raw_data.get('createdAt')
        
        if timestamp_str:
            try:
                # Try different timestamp formats
                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
                
                # Try parsing ISO format
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Fallback to current time
        return datetime.utcnow()
    
    def _extract_submitter_email(self, raw_data: Dict, source_type: str) -> Optional[str]:
        """Extract submitter email"""
        if source_type == 'google_forms':
            return raw_data.get('responderEmail') or raw_data.get('email')
        elif source_type == 'microsoft_forms':
            return raw_data.get('responder', {}).get('email')
        elif source_type == 'zoho_forms':
            form_data = raw_data.get('formData', {})
            return form_data.get('email') or form_data.get('Email')
        elif source_type == 'typeform':
            form_response = raw_data.get('form_response', {})
            hidden = form_response.get('hidden', {})
            return hidden.get('email')
        else:
            return raw_data.get('email') or raw_data.get('submitter_email')
    
    def _extract_submitter_name(self, raw_data: Dict, source_type: str) -> Optional[str]:
        """Extract submitter name"""
        if source_type == 'google_forms':
            return raw_data.get('responderName') or raw_data.get('name')
        elif source_type == 'microsoft_forms':
            responder = raw_data.get('responder', {})
            return responder.get('displayName')
        elif source_type == 'zoho_forms':
            form_data = raw_data.get('formData', {})
            return form_data.get('name') or form_data.get('Name')
        elif source_type == 'typeform':
            form_response = raw_data.get('form_response', {})
            hidden = form_response.get('hidden', {})
            return hidden.get('name')
        else:
            return raw_data.get('name') or raw_data.get('submitter_name')
    
    def _normalize_submission_data(self, raw_data: Dict, source_type: str) -> Dict:
        """Normalize submission data using field mapping"""
        normalized = {}
        
        try:
            if source_type == 'google_forms':
                normalized = self._normalize_google_forms_data(raw_data)
            elif source_type == 'microsoft_forms':
                normalized = self._normalize_microsoft_forms_data(raw_data)
            elif source_type == 'zoho_forms':
                normalized = self._normalize_zoho_forms_data(raw_data)
            elif source_type == 'typeform':
                normalized = self._normalize_typeform_data(raw_data)
            else:
                normalized = self._normalize_generic_data(raw_data)
            
            # Apply custom field mapping if configured
            if self.field_mapping:
                mapped_data = {}
                for source_field, target_field in self.field_mapping.items():
                    if source_field in normalized:
                        mapped_data[target_field] = normalized[source_field]
                
                # Keep unmapped fields with original names
                for field, value in normalized.items():
                    if field not in self.field_mapping:
                        mapped_data[field] = value
                
                normalized = mapped_data
                
        except Exception as e:
            logger.error(f"Error normalizing data: {str(e)}")
            normalized = {'raw_data': raw_data, 'normalization_error': str(e)}
        
        return normalized
    
    def _normalize_google_forms_data(self, raw_data: Dict) -> Dict:
        """Normalize Google Forms data"""
        normalized = {}
        
        # Google Forms responses structure
        answers = raw_data.get('answers', {})
        for question_id, answer_data in answers.items():
            question_title = answer_data.get('questionTitle', question_id)
            answer_value = answer_data.get('textAnswers', {}).get('answers', [{}])[0].get('value')
            normalized[question_title] = answer_value
        
        return normalized
    
    def _normalize_microsoft_forms_data(self, raw_data: Dict) -> Dict:
        """Normalize Microsoft Forms data"""
        normalized = {}
        
        # Microsoft Forms responses structure
        questions = raw_data.get('questions', [])
        for question in questions:
            question_id = question.get('id')
            question_title = question.get('title', question_id)
            answer = question.get('answer')
            
            if answer:
                if isinstance(answer, dict):
                    normalized[question_title] = answer.get('value', str(answer))
                else:
                    normalized[question_title] = str(answer)
        
        return normalized
    
    def _normalize_zoho_forms_data(self, raw_data: Dict) -> Dict:
        """Normalize Zoho Forms data"""
        normalized = {}
        
        # Zoho Forms data structure
        form_data = raw_data.get('formData', raw_data)
        
        for field_name, field_value in form_data.items():
            if not field_name.startswith('_'):  # Skip internal fields
                normalized[field_name] = field_value
        
        return normalized
    
    def _normalize_typeform_data(self, raw_data: Dict) -> Dict:
        """Normalize Typeform data"""
        normalized = {}
        
        # Typeform response structure
        form_response = raw_data.get('form_response', {})
        answers = form_response.get('answers', [])
        
        for answer in answers:
            field = answer.get('field', {})
            field_title = field.get('title', field.get('id'))
            
            # Extract answer value based on type
            answer_value = None
            for answer_type in ['text', 'email', 'number', 'boolean', 'choice', 'choices']:
                if answer_type in answer:
                    answer_value = answer[answer_type]
                    break
            
            if answer_value is not None:
                normalized[field_title] = answer_value
        
        return normalized
    
    def _normalize_generic_data(self, raw_data: Dict) -> Dict:
        """Normalize generic form data"""
        normalized = {}
        
        # Simple field extraction for generic forms
        for key, value in raw_data.items():
            if not key.startswith('_') and key not in ['id', 'timestamp', 'metadata']:
                normalized[key] = value
        
        return normalized
    
    # Manual sync methods (for API-based data fetching)
    
    def _sync_google_forms(self) -> Dict:
        """Sync Google Forms via API"""
        # Implementation would require Google Forms API integration
        # This is a placeholder for the actual API calls
        return {
            'status': 'info',
            'message': 'Google Forms API sync not implemented yet',
            'new_submissions': 0,
            'updated_submissions': 0,
            'error_count': 0
        }
    
    def _sync_microsoft_forms(self) -> Dict:
        """Sync Microsoft Forms via API"""
        # Implementation would require Microsoft Graph API integration
        return {
            'status': 'info',
            'message': 'Microsoft Forms API sync not implemented yet',
            'new_submissions': 0,
            'updated_submissions': 0,
            'error_count': 0
        }
    
    def _sync_zoho_forms(self) -> Dict:
        """Sync Zoho Forms via API"""
        # Implementation would require Zoho Forms API integration
        return {
            'status': 'info',
            'message': 'Zoho Forms API sync not implemented yet',
            'new_submissions': 0,
            'updated_submissions': 0,
            'error_count': 0
        }
    
    def _sync_typeform(self) -> Dict:
        """Sync Typeform via API"""
        # Implementation would require Typeform API integration
        return {
            'status': 'info',
            'message': 'Typeform API sync not implemented yet',
            'new_submissions': 0,
            'updated_submissions': 0,
            'error_count': 0
        }
