"""
Google Forms Integration Routes - Production Ready
Provides real Google Forms integration for automated reports
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from ..decorators import get_current_user_id, firebase_auth_required, firebase_token_optional

try:
    from app.services.google_forms_service import google_forms_service, _initialize_google_forms_service
    GOOGLE_FORMS_ENABLED = google_forms_service is not None
    print(f"Google Forms routes status: {'Enabled' if GOOGLE_FORMS_ENABLED else 'Disabled'}")

    # If service is None but we have credentials, try to initialize again
    if google_forms_service is None:
        import os
        if os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'):
            print("🔄 Retrying Google Forms service initialization...")
            google_forms_service = _initialize_google_forms_service()
            GOOGLE_FORMS_ENABLED = google_forms_service is not None
            print(f"🔄 Retry result: {'Enabled' if GOOGLE_FORMS_ENABLED else 'Still Disabled'}")
except (ImportError, ValueError) as e:
    google_forms_service = None
    GOOGLE_FORMS_ENABLED = False
    print(f"⚠️ Google Forms routes disabled - {str(e)}")

# Lazy import to avoid app context issues
automated_report_system = None
def _get_automated_report_system():
    global automated_report_system
    if automated_report_system is None:
        from app.services.automated_report_system import automated_report_system as ars
        automated_report_system = ars
    return automated_report_system

from app import db
from app.models import User
import logging
import os
from datetime import datetime
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
google_forms_bp = Blueprint('google_forms', __name__, url_prefix='/api/google-forms')

@google_forms_bp.route('/status', methods=['GET'])
@firebase_token_optional
def get_service_status():
    """Get the current status of the Google Forms service AND user authorization"""
    try:
        # Check service availability first
        if not google_forms_service:
            return jsonify({
                'success': False,
                'status': 'not_available',
                'message': 'Google Forms service not imported',
                'service_enabled': False,
                'is_authenticated': False,
                'is_authorized': False,
                'has_valid_token': False,
                'requires_config': True
            }), 503

        if not google_forms_service.is_enabled():
            return jsonify({
                'success': False,
                'status': 'disabled',
                'message': 'Google Forms service is not configured - missing OAuth credentials',
                'service_enabled': False,
                'is_authenticated': False,
                'is_authorized': False,
                'has_valid_token': False,
                'requires_config': True
            }), 503

        # Service is enabled - now check user authorization
        user_id = get_current_user_id()

        if not user_id:
            # Not authenticated with app
            return jsonify({
                'success': True,
                'status': 'enabled',
                'message': 'Google Forms service is available',
                'service_enabled': True,
                'is_authenticated': False,
                'is_authorized': False,
                'has_valid_token': False,
                'requires_auth': True
            })

        # User is authenticated - check Google Forms authorization
        is_authorized = False
        forms_count = 0

        try:
            credentials = google_forms_service._get_user_credentials(str(user_id))
            is_authorized = credentials is not None

            if is_authorized:
                # Try to get forms count, but don't fail authorization if this fails
                # The user may have no forms or there may be temporary API issues
                try:
                    forms = google_forms_service.get_user_forms(str(user_id), page_size=1)
                    forms_count = len(forms) if forms else 0
                    logger.info(f"User {user_id} has {forms_count} forms")
                except Exception as e:
                    logger.warning(f"Could not fetch forms for user {user_id}, but credentials are valid: {e}")
                    # Keep is_authorized = True since credentials exist
                    forms_count = 0
        except Exception as e:
            logger.error(f"Error checking user authorization: {e}")

        return jsonify({
            'success': True,
            'status': 'enabled',
            'message': 'Google Forms service is available and configured',
            'service_enabled': True,
            'is_authenticated': True,
            'is_authorized': is_authorized,
            'has_valid_token': is_authorized,
            'forms_count': forms_count
        })

    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': 'Error checking service status',
            'service_enabled': False,
            'is_authenticated': False,
            'is_authorized': False,
            'has_valid_token': False
        }), 500

@google_forms_bp.route('/forms', methods=['GET'])
@firebase_auth_required
def get_user_forms():
    """Get list of Google Forms accessible to the current user"""
    try:
        # Check if service is enabled
        if not google_forms_service or not google_forms_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Google Forms service is not configured',
                'requires_config': True
            }), 503

        user_id = get_current_user_id()

        # Require authentication - no fallback
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please log in first.',
                'requires_auth': True
            }), 401

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

@google_forms_bp.route('/forms/<form_id>/info', methods=['GET', 'OPTIONS'])
@firebase_auth_required
def get_form_info(form_id: str):
    """Get detailed information about a specific Google Form"""
    try:
        # Check if service is enabled
        if not google_forms_service or not google_forms_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Google Forms service is not configured',
                'requires_config': True
            }), 503
        
        user_id = get_current_user_id()
        
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

@google_forms_bp.route('/forms/<form_id>/responses', methods=['GET', 'OPTIONS'])
@firebase_auth_required
def get_form_responses(form_id: str):
    """Get responses for a specific Google Form"""
    try:
        # Check if service is enabled
        if not google_forms_service or not google_forms_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Google Forms service is not configured',
                'requires_config': True
            }), 503
        
        user_id = get_current_user_id()
        
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

@google_forms_bp.route('/forms/<form_id>/generate-report', methods=['POST', 'OPTIONS'])
@firebase_auth_required
def generate_automated_report(form_id: str):
    """Generate automated report from Google Form responses"""
    try:
        user_id = get_current_user_id()
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
        result = _get_automated_report_system().generate_google_forms_automated_report(
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
@firebase_auth_required
def authorize_google():
    """Initiate Google OAuth authorization for Google Forms access"""
    try:
        user_id = get_current_user_id()

        # This should always have a user_id due to decorator, but check anyway
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please log in first.',
                'requires_auth': True
            }), 401

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

@google_forms_bp.route('/oauth/callback', methods=['GET', 'POST'])
def oauth_callback():
    """Handle Google OAuth callback"""
    try:
        logger.info(f"OAuth callback received - Method: {request.method}")

        # Get authorization code from query params (GET) or body (POST)
        if request.method == 'GET':
            authorization_code = request.args.get('code')
            state = request.args.get('state')
            logger.info(f"GET callback - Code present: {bool(authorization_code)}, State: {state}")
        else:
            data = request.get_json() or {}
            authorization_code = data.get('code')
            state = data.get('state')
            logger.info(f"POST callback - Code present: {bool(authorization_code)}, State: {state}")

        if not authorization_code:
            logger.error("OAuth callback missing authorization code")
            return jsonify({
                'success': False,
                'error': 'Authorization code is required'
            }), 400

        # Get user_id from state or current session
        user_id = state if state and state != 'None' else None
        if not user_id:
            try:
                user_id = get_current_user_id()
                logger.info(f"Using current user ID: {user_id}")
            except (AttributeError, RuntimeError) as e:
                logger.error(f"Authentication error: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401

        logger.info(f"Processing OAuth callback for user {user_id}")

        # Exchange code for tokens using existing method (correct parameter order: user_id, code, state)
        result = google_forms_service.handle_oauth_callback(str(user_id), authorization_code, str(user_id))

        if result.get('status') != 'success':
            error_msg = result.get('message', 'Failed to exchange authorization code')
            logger.error(f"OAuth callback failed for user {user_id}: {error_msg}")
            if request.method == 'GET':
                return f'<html><body><p>Error: {error_msg}</p></body></html>', 400
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        logger.info(f"OAuth callback successful for user {user_id}")

        # For GET requests (browser redirects), return HTML that closes the popup
        if request.method == 'GET':
            return '''
                <html>
                    <body>
                        <script>
                            console.log('OAuth successful, posting message to opener');
                            window.opener.postMessage({type: 'google-auth-success'}, '*');
                            setTimeout(function() {
                                window.close();
                            }, 500);
                        </script>
                        <p>Authorization successful! Redirecting...</p>
                    </body>
                </html>
            '''

        # For POST requests, return JSON
        return jsonify({
            'success': True,
            'message': 'Google Forms access authorized successfully'
        })

    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        if request.method == 'GET':
            return f'<html><body><p>Error: {str(e)}</p></body></html>', 500
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/forms/<form_id>/export-excel', methods=['POST', 'OPTIONS'])
@firebase_auth_required
def export_google_form_to_excel(form_id: str):
    """Export Google Form responses to Excel"""
    try:
        # Check if service is enabled
        if not google_forms_service or not google_forms_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Google Forms service is not configured',
                'requires_config': True
            }), 503

        user_id = get_current_user_id()
        data = request.get_json() or {}

        # Get export options
        export_options = {
            'include_analytics': data.get('include_analytics', True),
            'date_range': data.get('date_range', {}),
            'use_ai_enhancement': data.get('use_ai_enhancement', False),
            'excel_options': data.get('excel_options', {
                'include_form_schema': True,
                'include_submission_metadata': True,
                'include_charts': data.get('include_charts', True),
                'include_pivot': data.get('include_pivot', False),
                'formatting': 'professional',
                'compression': True
            }),
            'max_responses': data.get('max_responses', 1000)
        }

        # Import Google Forms Excel service
        try:
            from app.services.google_forms_excel_service import google_forms_excel_service
        except ImportError:
            logger.error("Google Forms Excel service not available")
            return jsonify({
                'success': False,
                'error': 'Google Forms Excel export service not available'
            }), 503

        # Export to Excel
        export_result = google_forms_excel_service.export_google_form_to_excel(
            user_id=str(user_id),
            form_id=form_id,
            options=export_options
        )

        if not export_result['success']:
            return jsonify({
                'success': False,
                'error': export_result.get('error', 'Failed to export Google Form to Excel')
            }), 400

        return jsonify({
            'success': True,
            'message': 'Google Form exported to Excel successfully',
            'download_url': export_result['download_url'],
            'file_size': export_result.get('file_size', 0),
            'responses_count': export_result.get('responses_count', 0),
            'generation_time': export_result.get('generation_time', 0),
            'form_info': export_result.get('form_info', {}),
            'ai_enhanced': export_result.get('ai_enhanced', False)
        })

    except Exception as e:
        logger.exception(f"Error exporting Google Form {form_id} to Excel")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@google_forms_bp.route('/forms/<form_id>/preview-report', methods=['POST', 'OPTIONS'])
@firebase_auth_required
def preview_report_data(form_id: str):
    """Preview report data before generation"""
    try:
        user_id = get_current_user_id()

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

@google_forms_bp.route('/forms/<form_id>/download-excel/<filename>', methods=['GET', 'OPTIONS'])
@firebase_auth_required
def download_google_forms_excel(form_id: str, filename: str):
    """Download Google Forms Excel export file"""
    try:
        user_id = get_current_user_id()

        # Security: Only allow downloads for authenticated users
        # In a production environment, you might want to add more security checks

        # Construct file path
        upload_folder = os.path.join(current_app.root_path, '..', 'backend', 'static', 'exports')
        file_path = os.path.join(upload_folder, filename)

        # Verify file exists and is an Excel file
        if not os.path.exists(file_path) or not filename.endswith('.xlsx'):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        # Generate a user-friendly filename
        clean_filename = f"google_form_{form_id}_export_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=clean_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"Error downloading Google Forms Excel file: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to download file'
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
