"""
Production Reports API Endpoints - ZERO MOCK DATA
Real report generation with template processing and AI insights
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import BadRequest, NotFound
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import tempfile
from io import BytesIO

from .production_endpoints import handle_errors, validate_json_data

logger = logging.getLogger(__name__)

# Create blueprint
production_reports_bp = Blueprint('production_reports', __name__, url_prefix='/api/production/reports')

# ============================================================================
# AUTOMATED REPORT GENERATION - REAL DATA
# ============================================================================

@production_reports_bp.route('/generate', methods=['POST'])
@jwt_required()
@validate_json_data(['form_analysis_id', 'report_type'])
@handle_errors
def generate_automated_report():
    """Generate automated report from real form analysis data"""
    from ..services.production_automated_report_system import ProductionAutomatedReportSystem
    from ..models.production_models import FormAnalysis, Report
    from .. import db
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        form_analysis_id = data['form_analysis_id']
        report_type = data['report_type']
        program_id = data.get('program_id')
        custom_title = data.get('title', 'Automated Analysis Report')
        
        # Get real form analysis data
        form_analysis = FormAnalysis.query.filter_by(
            id=form_analysis_id,
            user_id=user_id
        ).first()
        
        if not form_analysis:
            return jsonify({
                'status': 'error',
                'message': 'Form analysis not found'
            }), 404
        
        # Initialize automated report system
        report_system = ProductionAutomatedReportSystem()
        
        # Generate real report with actual data
        report_result = report_system.generate_comprehensive_report({
            'form_analysis': {
                'id': form_analysis.id,
                'form_id': form_analysis.form_id,
                'form_provider': form_analysis.form_provider,
                'analysis_data': form_analysis.analysis_data,
                'response_count': form_analysis.response_count,
                'created_at': form_analysis.created_at.isoformat()
            },
            'report_type': report_type,
            'user_id': user_id,
            'program_id': program_id
        })
        
        # Save report to database
        report_record = Report(
            user_id=user_id,
            program_id=program_id,
            form_analysis_id=form_analysis_id,
            title=custom_title,
            description=f"Automated report generated from {form_analysis.form_provider} form analysis",
            report_type=report_type,
            content_data=report_result['content'],
            charts_data=report_result.get('charts', {}),
            statistics_data=report_result.get('statistics', {}),
            template_used='production_template',
            generation_method='automated',
            ai_generated=True,
            status='completed'
        )
        
        db.session.add(report_record)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': {
                'report_id': report_record.id,
                'report_uuid': report_record.uuid,
                'title': report_record.title,
                'report_type': report_type,
                'content': report_result['content'],
                'charts': report_result.get('charts', {}),
                'statistics': report_result.get('statistics', {}),
                'metadata': {
                    'generated_at': report_record.created_at.isoformat(),
                    'source_analysis_id': form_analysis_id,
                    'response_count': form_analysis.response_count,
                    'form_provider': form_analysis.form_provider,
                    'mock_data': False,
                    'production_generated': True
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating automated report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate report',
            'details': str(e) if current_app.debug else 'Report generation service unavailable'
        }), 500

@production_reports_bp.route('/template/process', methods=['POST'])
@jwt_required()
@validate_json_data(['template_data', 'program_id'])
@handle_errors
def process_template_with_real_data():
    """Process template with real program data - NO MOCK VALUES"""
    from ..services.production_template_converter import ProductionTemplateConverter
    from ..models.production_models import Program
    from .. import db
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        program_id = data['program_id']
        template_data = data['template_data']
        output_format = data.get('output_format', 'docx')
        
        # Get real program data
        program = Program.query.filter_by(
            id=program_id,
            user_id=user_id
        ).first()
        
        if not program:
            return jsonify({
                'status': 'error',
                'message': 'Program not found'
            }), 404
        
        # Initialize template converter with real data
        template_converter = ProductionTemplateConverter()
        
        # Process template with actual program data
        processed_result = template_converter.convert_template_with_real_data({
            'template_content': template_data,
            'program': {
                'id': program.id,
                'name': program.name,
                'description': program.description,
                'start_date': program.start_date.isoformat() if program.start_date else None,
                'end_date': program.end_date.isoformat() if program.end_date else None,
                'budget': program.budget,
                'funding_source': program.funding_source,
                'program_type': program.program_type,
                'target_population': program.target_population,
                'geographic_scope': program.geographic_scope,
                'participants_enrolled': program.participants_enrolled,
                'participants_completed': program.participants_completed,
                'completion_rate': program.completion_rate,
                'satisfaction_score': program.satisfaction_score,
                'program_manager': program.program_manager,
                'contact_email': program.contact_email,
                'contact_phone': program.contact_phone,
                'status': program.status
            },
            'output_format': output_format
        })
        
        return jsonify({
            'status': 'success',
            'data': {
                'processed_content': processed_result['content'],
                'placeholders_replaced': processed_result['placeholders_replaced'],
                'replacement_count': processed_result['replacement_count'],
                'program_data_source': 'real_database',
                'mock_data': False,
                'metadata': {
                    'program_id': program_id,
                    'program_name': program.name,
                    'processed_at': datetime.utcnow().isoformat(),
                    'template_format': output_format
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing template: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process template',
            'details': str(e)
        }), 500

@production_reports_bp.route('/download/<report_uuid>', methods=['GET'])
@jwt_required()
@handle_errors
def download_report(report_uuid: str):
    """Download generated report as file"""
    from ..models.production_models import Report
    from ..services.production_template_converter import ProductionTemplateConverter
    
    try:
        user_id = get_jwt_identity()
        
        # Get real report from database
        report = Report.query.filter_by(
            uuid=report_uuid,
            user_id=user_id
        ).first()
        
        if not report:
            return jsonify({
                'status': 'error',
                'message': 'Report not found'
            }), 404
        
        # Generate file from report data
        template_converter = ProductionTemplateConverter()
        
        # Create downloadable file
        if report.file_format == 'pdf':
            file_result = template_converter.generate_pdf_from_content(report.content_data)
            mimetype = 'application/pdf'
            filename = f"report_{report.id}.pdf"
        elif report.file_format == 'docx':
            file_result = template_converter.generate_docx_from_content(report.content_data)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f"report_{report.id}.docx"
        else:
            return jsonify({
                'status': 'error',
                'message': 'Unsupported file format'
            }), 400
        
        # Update download count
        report.download_count += 1
        from .. import db
        db.session.commit()
        
        # Return file for download
        return send_file(
            BytesIO(file_result['file_content']),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to download report',
            'details': str(e)
        }), 500

# ============================================================================
# REPORT MANAGEMENT ENDPOINTS
# ============================================================================

@production_reports_bp.route('/list', methods=['GET'])
@jwt_required()
@handle_errors
def list_user_reports():
    """List all reports for authenticated user - REAL DATA"""
    from ..models.production_models import Report, Program, FormAnalysis
    from sqlalchemy.orm import joinedload
    
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        report_type = request.args.get('type')
        status = request.args.get('status')
        
        # Build query for real reports
        query = Report.query.filter_by(user_id=user_id)
        
        if report_type:
            query = query.filter_by(report_type=report_type)
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(Report.created_at.desc())
        
        # Paginate
        reports_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        reports_data = []
        for report in reports_paginated.items:
            report_data = {
                'id': report.id,
                'uuid': report.uuid,
                'title': report.title,
                'description': report.description,
                'report_type': report.report_type,
                'status': report.status,
                'file_format': report.file_format,
                'download_count': report.download_count,
                'created_at': report.created_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
                'mock_data': False
            }
            
            # Add program info if available
            if report.program_id:
                program = Program.query.get(report.program_id)
                if program:
                    report_data['program'] = {
                        'id': program.id,
                        'name': program.name,
                        'status': program.status
                    }
            
            # Add form analysis info if available
            if report.form_analysis_id:
                form_analysis = FormAnalysis.query.get(report.form_analysis_id)
                if form_analysis:
                    report_data['form_analysis'] = {
                        'id': form_analysis.id,
                        'form_provider': form_analysis.form_provider,
                        'response_count': form_analysis.response_count
                    }
            
            reports_data.append(report_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'reports': reports_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': reports_paginated.total,
                    'pages': reports_paginated.pages,
                    'has_next': reports_paginated.has_next,
                    'has_prev': reports_paginated.has_prev
                },
                'metadata': {
                    'total_reports': reports_paginated.total,
                    'data_source': 'real_database',
                    'mock_data': False,
                    'last_updated': datetime.utcnow().isoformat()
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch reports',
            'details': str(e)
        }), 500

@production_reports_bp.route('/<report_uuid>', methods=['GET'])
@jwt_required()
@handle_errors
def get_report_details(report_uuid: str):
    """Get detailed information about a specific report"""
    from ..models.production_models import Report, Program, FormAnalysis
    
    try:
        user_id = get_jwt_identity()
        
        # Get real report data
        report = Report.query.filter_by(
            uuid=report_uuid,
            user_id=user_id
        ).first()
        
        if not report:
            return jsonify({
                'status': 'error',
                'message': 'Report not found'
            }), 404
        
        report_data = {
            'id': report.id,
            'uuid': report.uuid,
            'title': report.title,
            'description': report.description,
            'report_type': report.report_type,
            'status': report.status,
            'content_data': report.content_data,
            'charts_data': report.charts_data,
            'statistics_data': report.statistics_data,
            'file_format': report.file_format,
            'template_used': report.template_used,
            'generation_method': report.generation_method,
            'ai_generated': report.ai_generated,
            'download_count': report.download_count,
            'is_public': report.is_public,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat(),
            'mock_data': False
        }
        
        # Add related data
        if report.program_id:
            program = Program.query.get(report.program_id)
            if program:
                report_data['program'] = {
                    'id': program.id,
                    'name': program.name,
                    'description': program.description,
                    'status': program.status,
                    'participants_enrolled': program.participants_enrolled,
                    'completion_rate': program.completion_rate
                }
        
        if report.form_analysis_id:
            form_analysis = FormAnalysis.query.get(report.form_analysis_id)
            if form_analysis:
                report_data['form_analysis'] = {
                    'id': form_analysis.id,
                    'form_id': form_analysis.form_id,
                    'form_provider': form_analysis.form_provider,
                    'form_title': form_analysis.form_title,
                    'response_count': form_analysis.response_count,
                    'created_at': form_analysis.created_at.isoformat()
                }
        
        return jsonify({
            'status': 'success',
            'data': report_data
        })
        
    except Exception as e:
        logger.error(f"Error getting report details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch report details',
            'details': str(e)
        }), 500

@production_reports_bp.route('/statistics', methods=['GET'])
@jwt_required()
@handle_errors
def get_reports_statistics():
    """Get real statistics about user's reports"""
    from ..models.production_models import Report, FormAnalysis
    from sqlalchemy import func
    from .. import db
    
    try:
        user_id = get_jwt_identity()
        
        # Get real statistics from database
        total_reports = Report.query.filter_by(user_id=user_id).count()
        
        # Reports by type
        reports_by_type = db.session.query(
            Report.report_type,
            func.count(Report.id)
        ).filter_by(user_id=user_id).group_by(Report.report_type).all()
        
        # Reports by status
        reports_by_status = db.session.query(
            Report.status,
            func.count(Report.id)
        ).filter_by(user_id=user_id).group_by(Report.status).all()
        
        # Total downloads
        total_downloads = db.session.query(
            func.sum(Report.download_count)
        ).filter_by(user_id=user_id).scalar() or 0
        
        # Recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_reports = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= thirty_days_ago
        ).count()
        
        statistics = {
            'total_reports': total_reports,
            'total_downloads': int(total_downloads),
            'recent_reports_30_days': recent_reports,
            'reports_by_type': {report_type: count for report_type, count in reports_by_type},
            'reports_by_status': {status: count for status, count in reports_by_status},
            'statistics_source': 'real_database',
            'mock_data': False,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting report statistics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch statistics',
            'details': str(e)
        }), 500
