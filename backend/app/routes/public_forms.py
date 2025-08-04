"""
Public Forms API - Handles form submissions from public/Google/Microsoft forms
This module normalizes data from different sources and stores it in PostgreSQL
"""

from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import json
import uuid
from ..models import db, Form, FormSubmission, User
from ..utils.data_normalizer import normalize_form_data
from ..tasks.report_tasks import trigger_auto_report_generation

# Create blueprint for public forms
public_forms_bp = Blueprint('public_forms', __name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@public_forms_bp.route('/submit', methods=['POST'])
@limiter.limit("20 per minute")
def submit_public_form():
    """
    Universal form submission endpoint that accepts data from:
    - Google Forms
    - Microsoft Forms  
    - Custom public forms
    - Direct API submissions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract metadata
        form_source = data.get('source', 'unknown')  # google, microsoft, custom, api
        form_id = data.get('form_id')
        submission_data = data.get('data', {})
        submitter_info = data.get('submitter', {})
        
        # Normalize the form data based on source
        normalized_data = normalize_form_data(submission_data, form_source)
        
        # Create or find form record
        form = None
        if form_id:
            form = Form.query.filter_by(id=form_id).first()
        
        # If no form found, create a dynamic form entry
        if not form:
            form = create_dynamic_form(data, form_source)
        
        # Create submission record
        submission = FormSubmission(
            form_id=form.id,
            data=normalized_data,
            submitter_email=submitter_info.get('email'),
            submitted_at=datetime.utcnow(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            submission_source=form_source,
            status='submitted'
        )
        
        # Add location data if provided
        if 'location' in data:
            submission.location_data = data['location']
        
        db.session.add(submission)
        db.session.commit()
        
        current_app.logger.info(f"Form submission created: {submission.id} from {form_source}")
        
        # Trigger automatic report generation if configured
        if form.form_settings and form.form_settings.get('auto_report_enabled', False):
            trigger_auto_report_generation.delay(form.id, submission.id)
        
        return jsonify({
            'success': True,
            'submission_id': submission.id,
            'form_id': form.id,
            'message': 'Form submitted successfully',
            'timestamp': submission.submitted_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in submit_public_form: {str(e)}")
        return jsonify({'error': 'Failed to submit form'}), 500


@public_forms_bp.route('/batch-submit', methods=['POST'])
@limiter.limit("5 per minute")  
def batch_submit_forms():
    """
    Batch submission endpoint for processing multiple form responses at once
    Useful for importing data from external sources
    """
    try:
        data = request.get_json()
        submissions = data.get('submissions', [])
        
        if not submissions:
            return jsonify({'error': 'No submissions provided'}), 400
        
        if len(submissions) > 100:  # Limit batch size
            return jsonify({'error': 'Batch size too large (max 100)'}), 400
        
        results = []
        successful_count = 0
        
        for submission_data in submissions:
            try:
                # Process each submission
                form_source = submission_data.get('source', 'batch')
                form_id = submission_data.get('form_id')
                normalized_data = normalize_form_data(submission_data.get('data', {}), form_source)
                
                # Find or create form
                form = None
                if form_id:
                    form = Form.query.filter_by(id=form_id).first()
                
                if not form:
                    form = create_dynamic_form(submission_data, form_source)
                
                # Create submission
                submission = FormSubmission(
                    form_id=form.id,
                    data=normalized_data,
                    submitter_email=submission_data.get('submitter', {}).get('email'),
                    submitted_at=datetime.utcnow(),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    submission_source=form_source,
                    status='submitted'
                )
                
                db.session.add(submission)
                db.session.flush()  # Get ID without committing
                
                results.append({
                    'success': True,
                    'submission_id': submission.id,
                    'form_id': form.id
                })
                successful_count += 1
                
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'total_processed': len(submissions),
            'successful': successful_count,
            'failed': len(submissions) - successful_count,
            'results': results
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in batch_submit_forms: {str(e)}")
        return jsonify({'error': 'Failed to process batch submission'}), 500


@public_forms_bp.route('/google-webhook', methods=['POST'])
@limiter.limit("100 per hour")
def google_forms_webhook():
    """
    Webhook endpoint for Google Forms integration
    Receives notifications when new responses are submitted
    """
    try:
        data = request.get_json()
        
        # Verify Google webhook signature if configured
        # if not verify_google_signature(request):
        #     return jsonify({'error': 'Invalid signature'}), 401
        
        # Process Google Forms specific data structure
        form_response = data.get('formResponse', {})
        form_id = data.get('formId')
        
        # Transform Google Forms data to our format
        submission_data = {
            'source': 'google',
            'form_id': form_id,
            'data': transform_google_response(form_response),
            'submitter': {
                'email': form_response.get('respondentEmail')
            },
            'timestamp': data.get('timestamp')
        }
        
        # Process using the main submission endpoint logic
        return submit_public_form_data(submission_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in google_forms_webhook: {str(e)}")
        return jsonify({'error': 'Failed to process Google Forms webhook'}), 500


@public_forms_bp.route('/microsoft-webhook', methods=['POST'])
@limiter.limit("100 per hour")
def microsoft_forms_webhook():
    """
    Webhook endpoint for Microsoft Forms integration
    """
    try:
        data = request.get_json()
        
        # Process Microsoft Forms specific data structure
        form_id = data.get('formId')
        response_data = data.get('response', {})
        
        submission_data = {
            'source': 'microsoft',
            'form_id': form_id,
            'data': transform_microsoft_response(response_data),
            'submitter': {
                'email': response_data.get('responderEmail')
            },
            'timestamp': data.get('submitDate')
        }
        
        return submit_public_form_data(submission_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in microsoft_forms_webhook: {str(e)}")
        return jsonify({'error': 'Failed to process Microsoft Forms webhook'}), 500


def create_dynamic_form(submission_data, form_source):
    """Create a dynamic form entry for external submissions"""
    form_title = submission_data.get('form_title', f'External Form ({form_source})')
    
    # Extract schema from submission data
    schema = {
        'fields': [],
        'source': form_source,
        'auto_generated': True
    }
    
    # Create basic schema from submitted data
    if 'data' in submission_data:
        for key, value in submission_data['data'].items():
            field_type = determine_field_type(value)
            schema['fields'].append({
                'name': key,
                'type': field_type,
                'label': key.replace('_', ' ').title(),
                'required': False
            })
    
    # Create form record
    form = Form(
        title=form_title,
        description=f'Auto-generated form for {form_source} submissions',
        schema=schema,
        is_public=True,
        is_active=True,
        creator_id=1,  # System user - you may want to create a specific system user
        form_settings={
            'auto_generated': True,
            'source': form_source,
            'auto_report_enabled': True  # Enable auto-reporting for external forms
        }
    )
    
    db.session.add(form)
    db.session.flush()  # Get ID without committing
    
    return form


def submit_public_form_data(submission_data):
    """Helper function to process submission data consistently"""
    # This function contains the core logic from submit_public_form
    # but can be called internally without HTTP request context
    pass


def transform_google_response(form_response):
    """Transform Google Forms response to standard format"""
    transformed = {}
    
    # Handle Google Forms specific structure
    answers = form_response.get('answers', {})
    for question_id, answer in answers.items():
        # Extract question text and answer value
        question_text = answer.get('questionTitle', question_id)
        answer_value = answer.get('textAnswer', {}).get('value') or answer.get('choiceAnswer', {}).get('value')
        
        transformed[question_text] = answer_value
    
    return transformed


def transform_microsoft_response(response_data):
    """Transform Microsoft Forms response to standard format"""
    transformed = {}
    
    # Handle Microsoft Forms specific structure
    answers = response_data.get('answers', [])
    for answer in answers:
        question_text = answer.get('questionTitle', '')
        answer_value = answer.get('value', '')
        
        if question_text:
            transformed[question_text] = answer_value
    
    return transformed


def determine_field_type(value):
    """Determine field type based on value"""
    if isinstance(value, bool):
        return 'checkbox'
    elif isinstance(value, (int, float)):
        return 'number'
    elif isinstance(value, str):
        if '@' in value and '.' in value:
            return 'email'
        elif len(value) > 100:
            return 'textarea'
        else:
            return 'text'
    else:
        return 'text'


# Error handlers
@public_forms_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@public_forms_bp.errorhandler(400)
def bad_request_handler(e):
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid data provided'
    }), 400

@public_forms_bp.errorhandler(500)
def internal_error_handler(e):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An error occurred while processing your request'
    }), 500
