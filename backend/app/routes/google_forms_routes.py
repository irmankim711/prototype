"""
Google Forms Integration Routes - Production Ready
Provides real Google Forms integration for automated reports
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.google_forms_service import google_forms_service
from app.services.automated_report_system import automated_report_system
from app.models import User, db
import logging
import os
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
google_forms_bp = Blueprint('google_forms', __name__, url_prefix='/api/google-forms')

@google_forms_bp.route('/forms', methods=['GET'])
@jwt_required()
def get_user_forms():
    """Get list of Google Forms accessible to the current user"""
    try:
        user_id = get_jwt_identity()
        page_size = request.args.get('page_size', 10, type=int)
        
        # Get user's Google Forms
        forms = google_forms_service.get_user_forms(str(user_id), page_size)
        
        return jsonify({
            'success': True,
            'forms': forms,
            'total_count': len(forms)
        })
        
    except Exception as e:
        logger.error(f"Error fetching user forms: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'requires_auth': True
        }), 500

@google_forms_bp.route('/forms/<form_id>/info', methods=['GET'])
@jwt_required()
def get_form_info(form_id: str):
    """Get detailed information about a specific Google Form"""
    try:
        user_id = get_jwt_identity()
        
        # Get form information via responses endpoint (includes form info)
        form_data = google_forms_service.get_form_responses(str(user_id), form_id, limit=1)
        
        if not form_data.get('success', False):
            return jsonify({
                'success': False,
                'error': form_data.get('error', 'Failed to fetch form info')
            }), 400
        
        return jsonify({
            'success': True,
            'form_info': form_data.get('form_info', {})
        })
        
    except Exception as e:
        logger.error(f"Error fetching form info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/forms/<form_id>/responses', methods=['GET'])
@jwt_required()
def get_form_responses(form_id: str):
    """Get responses for a specific Google Form"""
    try:
        user_id = get_jwt_identity()
        
        # Optional query parameters
        limit = request.args.get('limit', 100, type=int)
        include_analysis = request.args.get('include_analysis', 'false').lower() == 'true'
        
        # Get form responses
        if include_analysis:
            responses = google_forms_service.get_form_responses_for_automated_report(
                str(user_id), form_id
            )
        else:
            responses = google_forms_service.get_form_responses(
                str(user_id), form_id, limit=limit
            )
        
        if not responses.get('success', False):
            return jsonify({
                'success': False,
                'error': responses.get('error', 'Failed to fetch responses')
            }), 400
        
        return jsonify({
            'success': True,
            'responses': responses.get('responses', []),
            'form_info': responses.get('form_info', {}),
            'analysis': responses.get('analysis', {}) if include_analysis else None,
            'total_count': len(responses.get('responses', []))
        })
        
    except Exception as e:
        logger.error(f"Error fetching form responses: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/forms/<form_id>/generate-report', methods=['POST'])
@jwt_required()
def generate_automated_report(form_id: str):
    """Generate automated report from Google Form responses"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Report configuration
        report_config = {
            'format': data.get('format', 'pdf'),  # pdf, docx
            'include_charts': data.get('include_charts', True),
            'include_ai_analysis': data.get('include_ai_analysis', True),
            'chart_types': data.get('chart_types', ['response_patterns', 'completion', 'questions']),
            'title': data.get('title', ''),
            'description': data.get('description', '')
        }
        
        # Validate format
        if report_config['format'] not in ['pdf', 'docx']:
            return jsonify({
                'success': False,
                'error': 'Invalid format. Must be pdf or docx'
            }), 400
        
        # Generate the automated report
        result = automated_report_system.generate_google_forms_automated_report(
            form_id, report_config, user_id
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate report')
            }), 400
        
        return jsonify({
            'success': True,
            'report_id': result['report_id'],
            'download_url': result['download_url'],
            'summary': result['summary']
        })
        
    except Exception as e:
        logger.error(f"Error generating automated report: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/oauth/authorize', methods=['POST'])
@jwt_required()
def authorize_google():
    """Initiate Google OAuth authorization for Google Forms access"""
    try:
        user_id = get_jwt_identity()
        
        # Get authorization URL
        auth_url = google_forms_service.get_authorization_url(str(user_id))
        
        return jsonify({
            'success': True,
            'authorization_url': auth_url,
            'state': str(user_id)
        })
        
    except Exception as e:
        logger.error(f"Error getting Google authorization: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/oauth/callback', methods=['POST'])
@jwt_required()
def oauth_callback():
    """Handle Google OAuth callback"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        authorization_code = data.get('code')
        
        if not authorization_code:
            return jsonify({
                'success': False,
                'error': 'Authorization code is required'
            }), 400
        
        # Exchange code for tokens using existing method
        success = google_forms_service.handle_oauth_callback(authorization_code, str(user_id), state=str(user_id))
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to exchange authorization code'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Google Forms access authorized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/status', methods=['GET'])
def get_integration_status():
    """Get Google Forms integration status for current user"""
    try:
        # Check if user is authenticated
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            user_id = None
        
        # If not authenticated, return basic status
        if not user_id:
            return jsonify({
                'success': True,
                'is_authenticated': False,
                'is_authorized': False,
                'has_valid_token': False,
                'requires_auth': True,
                'message': 'Authentication required to check Google Forms integration status'
            })
        
        # Check if user has Google Forms access by trying to get credentials
        credentials = google_forms_service._get_user_credentials(str(user_id))
        is_authorized = credentials is not None
        
        # Try to get forms to check token validity
        forms_count = 0
        if is_authorized:
            try:
                forms = google_forms_service.get_user_forms(str(user_id), page_size=1)
                forms_count = len(forms) if forms else 0
            except:
                is_authorized = False
        
        return jsonify({
            'success': True,
            'is_authenticated': True,
            'is_authorized': is_authorized,
            'has_valid_token': is_authorized,
            'last_sync': None,  # Could be implemented later
            'forms_count': forms_count
        })
        
    except Exception as e:
        logger.error(f"Error checking integration status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/forms/<form_id>/preview-report', methods=['POST'])
@jwt_required()
def preview_report_data(form_id: str):
    """Preview report data before generation"""
    try:
        user_id = get_jwt_identity()
        
        # Get comprehensive analysis for preview
        forms_data = google_forms_service.get_form_responses_for_automated_report(
            str(user_id), form_id
        )
        
        if not forms_data['success']:
            return jsonify({
                'success': False,
                'error': forms_data.get('error', 'Failed to fetch form data')
            }), 400
        
        # Generate preview data
        preview = {
            'form_info': forms_data['form_info'],
            'response_count': len(forms_data.get('responses', [])),
            'analysis_summary': forms_data.get('analysis', {}),
            'insights_preview': forms_data.get('analysis', {}).get('question_insights', [])[:3],
            'completion_stats': forms_data.get('analysis', {}).get('completion_stats', {}),
            'temporal_analysis': forms_data.get('analysis', {}).get('temporal_analysis', {}),
            'available_charts': ['response_patterns', 'completion_rate', 'question_types']
        }
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        logger.error(f"Error generating report preview: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Error handlers
@google_forms_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@google_forms_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

@google_forms_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
