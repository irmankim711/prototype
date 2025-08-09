"""
Production Forms API Endpoints - ZERO MOCK DATA
Real form management with Google Forms and Microsoft Forms integration
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import BadRequest, NotFound
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import json

from .production_endpoints import handle_errors, validate_json_data

logger = logging.getLogger(__name__)

# Create blueprint
production_forms_bp = Blueprint('production_forms', __name__, url_prefix='/api/production/forms')

# ============================================================================
# GOOGLE FORMS ENDPOINTS - REAL API INTEGRATION
# ============================================================================

@production_forms_bp.route('/google/list', methods=['GET'])
@jwt_required()
@handle_errors
def list_google_forms():
    """List all accessible Google Forms for authenticated user - REAL DATA"""
    from ..services.production_google_forms_service import ProductionGoogleFormsService
    
    try:
        user_id = get_jwt_identity()
        service = ProductionGoogleFormsService()
        
        # Get user's OAuth token from database
        from ..models import UserOAuthToken
        oauth_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='google'
        ).first()
        
        if not oauth_token:
            return jsonify({
                'status': 'error',
                'message': 'Google OAuth token not found',
                'action_required': 'authenticate_with_google'
            }), 401
        
        # Fetch real forms from Google API
        forms = service.list_forms(oauth_token.access_token)
        
        return jsonify({
            'status': 'success',
            'data': {
                'forms': forms,
                'count': len(forms),
                'source': 'google_forms_api',
                'mock_data': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching Google Forms: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch Google Forms',
            'details': str(e) if current_app.debug else 'Please check your Google OAuth configuration'
        }), 500

@production_forms_bp.route('/google/<form_id>/responses', methods=['GET'])
@jwt_required()
@handle_errors
def get_google_form_responses(form_id: str):
    """Get real responses from specific Google Form"""
    from ..services.production_google_forms_service import ProductionGoogleFormsService
    
    try:
        user_id = get_jwt_identity()
        service = ProductionGoogleFormsService()
        
        # Get user's OAuth token
        from ..models import UserOAuthToken
        oauth_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='google'
        ).first()
        
        if not oauth_token:
            return jsonify({
                'status': 'error',
                'message': 'Google OAuth token not found'
            }), 401
        
        # Fetch real responses from Google API
        responses = service.get_form_responses(form_id, oauth_token.access_token)
        
        # Get form metadata
        form_info = service.get_form_info(form_id, oauth_token.access_token)
        
        return jsonify({
            'status': 'success',
            'data': {
                'form_id': form_id,
                'form_title': form_info.get('title', 'Unknown Form'),
                'responses': responses,
                'response_count': len(responses),
                'source': 'google_forms_api',
                'mock_data': False,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching Google Form responses: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch form responses',
            'details': str(e) if current_app.debug else 'Please verify form access permissions'
        }), 500

@production_forms_bp.route('/google/<form_id>/analyze', methods=['POST'])
@jwt_required()
@handle_errors
def analyze_google_form_responses(form_id: str):
    """Analyze Google Form responses with AI - REAL DATA"""
    from ..services.production_google_forms_service import ProductionGoogleFormsService
    from ..services.production_ai_service import ProductionAIService
    
    try:
        user_id = get_jwt_identity()
        google_service = ProductionGoogleFormsService()
        ai_service = ProductionAIService()
        
        # Get OAuth token
        from ..models import UserOAuthToken
        oauth_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='google'
        ).first()
        
        if not oauth_token:
            return jsonify({
                'status': 'error',
                'message': 'Google OAuth token not found'
            }), 401
        
        # Get real form data
        responses = google_service.get_form_responses(form_id, oauth_token.access_token)
        form_info = google_service.get_form_info(form_id, oauth_token.access_token)
        
        if not responses:
            return jsonify({
                'status': 'error',
                'message': 'No responses found for analysis'
            }), 404
        
        # Perform real AI analysis
        analysis_result = ai_service.analyze_form_responses({
            'form_id': form_id,
            'form_title': form_info.get('title', 'Unknown Form'),
            'responses': responses,
            'response_count': len(responses)
        })
        
        # Store analysis in database
        from ..models import FormAnalysis
        from .. import db
        
        analysis_record = FormAnalysis(
            form_id=form_id,
            user_id=user_id,
            form_provider='google',
            analysis_data=analysis_result,
            response_count=len(responses),
            created_at=datetime.utcnow()
        )
        
        db.session.add(analysis_record)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': {
                'form_id': form_id,
                'analysis_id': analysis_record.id,
                'analysis': analysis_result,
                'metadata': {
                    'form_title': form_info.get('title'),
                    'response_count': len(responses),
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'source': 'real_ai_analysis',
                    'mock_data': False
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing Google Form: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to analyze form responses',
            'details': str(e) if current_app.debug else 'Analysis service temporarily unavailable'
        }), 500

# ============================================================================
# MICROSOFT FORMS ENDPOINTS - REAL API INTEGRATION
# ============================================================================

@production_forms_bp.route('/microsoft/list', methods=['GET'])
@jwt_required()
@handle_errors
def list_microsoft_forms():
    """List all accessible Microsoft Forms for authenticated user - REAL DATA"""
    from ..services.production_microsoft_graph_service import ProductionMicrosoftGraphService
    
    try:
        user_id = get_jwt_identity()
        service = ProductionMicrosoftGraphService()
        
        # Get user's Microsoft OAuth token
        from ..models import UserOAuthToken
        oauth_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='microsoft'
        ).first()
        
        if not oauth_token:
            return jsonify({
                'status': 'error',
                'message': 'Microsoft OAuth token not found',
                'action_required': 'authenticate_with_microsoft'
            }), 401
        
        # Fetch real forms from Microsoft Graph API
        forms = service.list_forms(oauth_token.access_token)
        
        return jsonify({
            'status': 'success',
            'data': {
                'forms': forms,
                'count': len(forms),
                'source': 'microsoft_graph_api',
                'mock_data': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching Microsoft Forms: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch Microsoft Forms',
            'details': str(e) if current_app.debug else 'Please check your Microsoft OAuth configuration'
        }), 500

@production_forms_bp.route('/microsoft/<form_id>/responses', methods=['GET'])
@jwt_required()
@handle_errors
def get_microsoft_form_responses(form_id: str):
    """Get real responses from specific Microsoft Form"""
    from ..services.production_microsoft_graph_service import ProductionMicrosoftGraphService
    
    try:
        user_id = get_jwt_identity()
        service = ProductionMicrosoftGraphService()
        
        # Get OAuth token
        from ..models import UserOAuthToken
        oauth_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='microsoft'
        ).first()
        
        if not oauth_token:
            return jsonify({
                'status': 'error',
                'message': 'Microsoft OAuth token not found'
            }), 401
        
        # Fetch real responses from Microsoft Graph API
        responses = service.get_form_responses(form_id, oauth_token.access_token)
        form_info = service.get_form_info(form_id, oauth_token.access_token)
        
        return jsonify({
            'status': 'success',
            'data': {
                'form_id': form_id,
                'form_title': form_info.get('title', 'Unknown Form'),
                'responses': responses,
                'response_count': len(responses),
                'source': 'microsoft_graph_api',
                'mock_data': False,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching Microsoft Form responses: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch form responses',
            'details': str(e)
        }), 500

# ============================================================================
# UNIFIED FORM MANAGEMENT ENDPOINTS
# ============================================================================

@production_forms_bp.route('/all', methods=['GET'])
@jwt_required()
@handle_errors
def get_all_forms():
    """Get all forms from both Google and Microsoft - REAL DATA"""
    try:
        user_id = get_jwt_identity()
        all_forms = {
            'google_forms': [],
            'microsoft_forms': [],
            'total_count': 0,
            'sources_available': [],
            'mock_data': False
        }
        
        # Check for Google Forms
        from ..models import UserOAuthToken
        google_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='google'
        ).first()
        
        if google_token:
            try:
                from ..services.production_google_forms_service import ProductionGoogleFormsService
                google_service = ProductionGoogleFormsService()
                google_forms = google_service.list_forms(google_token.access_token)
                all_forms['google_forms'] = google_forms
                all_forms['sources_available'].append('google')
            except Exception as e:
                logger.warning(f"Failed to fetch Google Forms: {str(e)}")
        
        # Check for Microsoft Forms
        microsoft_token = UserOAuthToken.query.filter_by(
            user_id=user_id,
            provider='microsoft'
        ).first()
        
        if microsoft_token:
            try:
                from ..services.production_microsoft_graph_service import ProductionMicrosoftGraphService
                microsoft_service = ProductionMicrosoftGraphService()
                microsoft_forms = microsoft_service.list_forms(microsoft_token.access_token)
                all_forms['microsoft_forms'] = microsoft_forms
                all_forms['sources_available'].append('microsoft')
            except Exception as e:
                logger.warning(f"Failed to fetch Microsoft Forms: {str(e)}")
        
        all_forms['total_count'] = len(all_forms['google_forms']) + len(all_forms['microsoft_forms'])
        
        return jsonify({
            'status': 'success',
            'data': all_forms
        })
        
    except Exception as e:
        logger.error(f"Error fetching all forms: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch forms',
            'details': str(e)
        }), 500

@production_forms_bp.route('/stats', methods=['GET'])
@jwt_required()
@handle_errors
def get_forms_statistics():
    """Get real statistics about user's forms and responses"""
    try:
        user_id = get_jwt_identity()
        
        from ..models import FormAnalysis, UserOAuthToken
        from sqlalchemy import func
        from .. import db
        
        # Get form analysis history
        analysis_count = FormAnalysis.query.filter_by(user_id=user_id).count()
        
        # Get recent analyses
        recent_analyses = FormAnalysis.query.filter_by(
            user_id=user_id
        ).order_by(FormAnalysis.created_at.desc()).limit(5).all()
        
        # Get OAuth token status
        oauth_tokens = UserOAuthToken.query.filter_by(user_id=user_id).all()
        connected_providers = [token.provider for token in oauth_tokens]
        
        # Calculate response statistics from recent analyses
        total_responses = sum([analysis.response_count for analysis in recent_analyses])
        
        stats = {
            'total_analyses': analysis_count,
            'total_responses_analyzed': total_responses,
            'connected_providers': connected_providers,
            'recent_analyses': [
                {
                    'id': analysis.id,
                    'form_id': analysis.form_id,
                    'provider': analysis.form_provider,
                    'response_count': analysis.response_count,
                    'created_at': analysis.created_at.isoformat()
                } for analysis in recent_analyses
            ],
            'statistics_source': 'real_database_data',
            'mock_data': False,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching form statistics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch statistics',
            'details': str(e)
        }), 500
