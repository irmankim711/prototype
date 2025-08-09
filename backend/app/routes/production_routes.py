"""
Production-Ready API Routes
Eliminates all mock data and implements real API endpoints
"""
import os
import logging
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from typing import Dict, Any

from app.services.production_google_forms_service import production_google_forms_service
from app.services.production_ai_service import production_ai_service
from app.services.production_template_service import production_template_service
from app.models import User, Report
from app import db

logger = logging.getLogger(__name__)

# Create blueprint for production API routes
production_bp = Blueprint('production', __name__, url_prefix='/api/production')

@production_bp.route('/health', methods=['GET'])
def health_check():
    """Production health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'production'),
        'features': {
            'google_forms': os.getenv('ENABLE_REAL_GOOGLE_FORMS', 'false').lower() == 'true',
            'ai_analysis': os.getenv('ENABLE_REAL_AI', 'false').lower() == 'true',
            'mock_disabled': os.getenv('MOCK_MODE_DISABLED', 'false').lower() == 'true'
        }
    })

# Google Forms Integration Routes
@production_bp.route('/google-forms/auth-url', methods=['POST'])
@jwt_required()
def get_google_auth_url():
    """Get real Google OAuth authorization URL"""
    try:
        user_id = get_jwt_identity()
        auth_url = production_google_forms_service.get_authorization_url(user_id)
        
        logger.info(f"Real Google OAuth URL generated for user {user_id}")
        return jsonify({
            'success': True,
            'authorization_url': auth_url,
            'user_id': user_id
        })
    except Exception as e:
        logger.error(f"Error generating Google auth URL: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@production_bp.route('/google-forms/callback', methods=['POST'])
@jwt_required()
def handle_google_callback():
    """Handle real Google OAuth callback"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        code = data.get('code')
        state = data.get('state')
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Authorization code is required'
            }), 400
        
        result = production_google_forms_service.handle_oauth_callback(user_id, code, state)
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': 'Google Forms authentication successful',
                'user_id': user_id
            })
        else:
            return jsonify({
                'success': False,
                'error': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"Error handling Google callback: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@production_bp.route('/google-forms/forms', methods=['GET'])
@jwt_required()
def get_user_google_forms():
    """Get real Google Forms for authenticated user"""
    try:
        user_id = get_jwt_identity()
        page_size = request.args.get('page_size', 50, type=int)
        
        forms = production_google_forms_service.get_user_forms(user_id, page_size)
        
        logger.info(f"Retrieved {len(forms)} real Google Forms for user {user_id}")
        return jsonify({
            'success': True,
            'forms': forms,
            'total_count': len(forms),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error fetching Google Forms: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@production_bp.route('/google-forms/<form_id>/responses', methods=['GET'])
@jwt_required()
def get_form_responses(form_id):
    """Get real responses for a Google Form"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 100, type=int)
        include_analysis = request.args.get('include_analysis', 'false').lower() == 'true'
        
        responses = production_google_forms_service.get_form_responses(
            user_id, form_id, limit, include_analysis
        )
        
        logger.info(f"Retrieved responses for form {form_id} (user {user_id})")
        return jsonify(responses)
        
    except Exception as e:
        logger.error(f"Error fetching form responses: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# AI Analysis Routes
@production_bp.route('/ai/analyze', methods=['POST'])
@jwt_required()
def analyze_data_with_ai():
    """Analyze data with real AI or intelligent fallback"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Data is required for analysis'
            }), 400
        
        form_title = data.get('form_title', 'Form Analysis')
        form_data = data.get('form_data', {})
        
        analysis_result = production_ai_service.analyze_form_data(form_data, form_title)
        
        logger.info(f"AI analysis completed for user {user_id} ({'AI-powered' if analysis_result.get('ai_powered') else 'Fallback analysis'})")
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Report Generation Routes
@production_bp.route('/reports/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """Generate report with real data (no mock data)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        form_id = data.get('form_id')
        template_name = data.get('template', 'Temp1.docx')
        report_config = data.get('config', {})
        
        if not form_id:
            return jsonify({
                'success': False,
                'error': 'form_id is required'
            }), 400
        
        # Generate automated report with real data
        report_result = production_google_forms_service.generate_automated_report(
            user_id, form_id, report_config
        )
        
        if report_result['status'] != 'success':
            return jsonify({
                'success': False,
                'error': report_result.get('message', 'Failed to generate report')
            }), 500
        
        # Process template with real data
        template_result = production_template_service.process_template_with_real_data(
            template_name, report_result
        )
        
        if template_result['status'] != 'success':
            return jsonify({
                'success': False,
                'error': template_result.get('message', 'Failed to process template')
            }), 500
        
        # Create report record in database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        report = Report(
            title=f"Report for {report_result['form_info']['title']}",
            description=f"Generated from Google Form responses",
            status='completed',
            user_id=user_id,
            template_id=template_name,
            data=template_result['mapped_data']
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info(f"Report generated successfully for user {user_id}, form {form_id}")
        return jsonify({
            'success': True,
            'report_id': report.id,
            'form_info': report_result['form_info'],
            'response_count': report_result['response_count'],
            'template_validation': template_result['validation'],
            'analysis': report_result.get('analysis', {}),
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@production_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_user_reports():
    """Get user reports (no mock data)"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        
        # Build query
        query = Report.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        reports_pagination = query.order_by(Report.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        reports_data = []
        for report in reports_pagination.items:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'status': report.status,
                'template_id': report.template_id,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'updated_at': report.updated_at.isoformat() if report.updated_at else None,
                'data_preview': {
                    'participant_count': len(report.data.get('participants', [])) if report.data else 0,
                    'program_title': report.data.get('program', {}).get('title', '') if report.data else ''
                }
            })
        
        logger.info(f"Retrieved {len(reports_data)} reports for user {user_id}")
        return jsonify({
            'success': True,
            'reports': reports_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reports_pagination.total,
                'pages': reports_pagination.pages,
                'has_prev': reports_pagination.has_prev,
                'has_next': reports_pagination.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@production_bp.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_details(report_id):
    """Get detailed report information"""
    try:
        user_id = get_jwt_identity()
        
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404
        
        report_data = {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'template_id': report.template_id,
            'data': report.data,
            'output_url': report.output_url,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None
        }
        
        logger.info(f"Retrieved report details for report {report_id} (user {user_id})")
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching report details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Template Management Routes
@production_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_available_templates():
    """Get available templates (no mock data)"""
    try:
        templates = [
            {
                'id': 'Temp1.docx',
                'name': 'Training Report Template',
                'description': 'Comprehensive training program report with participant tracking',
                'placeholders': list(production_template_service.template_mappings['Temp1.docx']['placeholders'].keys()),
                'required_sections': production_template_service.template_mappings['Temp1.docx']['required_sections'],
                'optional_sections': production_template_service.template_mappings['Temp1.docx']['optional_sections']
            }
        ]
        
        logger.info("Retrieved available templates")
        return jsonify({
            'success': True,
            'templates': templates,
            'total_count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@production_bp.route('/templates/<template_id>/validate', methods=['POST'])
@jwt_required()
def validate_template_data(template_id):
    """Validate data against template requirements"""
    try:
        data = request.get_json()
        form_data = data.get('form_data', {})
        
        template_result = production_template_service.process_template_with_real_data(
            template_id, form_data
        )
        
        if template_result['status'] == 'success':
            return jsonify({
                'success': True,
                'validation': template_result['validation'],
                'completeness': template_result['validation']['completeness']
            })
        else:
            return jsonify({
                'success': False,
                'error': template_result.get('message', 'Validation failed')
            }), 400
            
    except Exception as e:
        logger.error(f"Error validating template data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Statistics and Analytics Routes
@production_bp.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_analytics():
    """Get dashboard analytics with real data"""
    try:
        user_id = get_jwt_identity()
        
        # Get real statistics from database
        total_reports = Report.query.filter_by(user_id=user_id).count()
        completed_reports = Report.query.filter_by(user_id=user_id, status='completed').count()
        processing_reports = Report.query.filter_by(user_id=user_id, status='processing').count()
        failed_reports = Report.query.filter_by(user_id=user_id, status='failed').count()
        
        # Get recent activity
        recent_reports = Report.query.filter_by(user_id=user_id)\
            .order_by(Report.created_at.desc())\
            .limit(5).all()
        
        recent_activity = []
        for report in recent_reports:
            recent_activity.append({
                'id': report.id,
                'title': report.title,
                'status': report.status,
                'created_at': report.created_at.isoformat() if report.created_at else None
            })
        
        analytics_data = {
            'total_reports': total_reports,
            'completed_reports': completed_reports,
            'processing_reports': processing_reports,
            'failed_reports': failed_reports,
            'success_rate': (completed_reports / total_reports * 100) if total_reports > 0 else 0,
            'recent_activity': recent_activity,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Dashboard analytics generated for user {user_id}")
        return jsonify({
            'success': True,
            'analytics': analytics_data
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@production_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist'
    }), 404

@production_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
