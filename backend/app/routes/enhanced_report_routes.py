"""
Enhanced Report Builder API Routes
Provides endpoints for the new AI-powered report builder with live preview
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import tempfile
import json
import logging
from werkzeug.utils import secure_filename
from datetime import datetime

from ..services.gemini_content_service import gemini_content_service
from ..services.enhanced_excel_parser import enhanced_excel_parser
from ..services.live_preview_generator import live_preview_generator

logger = logging.getLogger(__name__)

enhanced_report_bp = Blueprint('enhanced_report', __name__, url_prefix='/api/enhanced-report')

@enhanced_report_bp.route('/upload-excel', methods=['POST'])
@jwt_required()
def upload_excel():
    """
    Upload and analyze Excel file for report generation
    """
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file type
        filename = secure_filename(file.filename or 'upload.xlsx')
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in ['.xlsx', '.xls', '.csv']:
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files.'
            }), 400
        
        # Save file temporarily
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Parse Excel file
        parse_result = enhanced_excel_parser.parse_excel_file(file_path)
        
        # Clean up temporary file
        try:
            os.remove(file_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        if not parse_result['success']:
            return jsonify({
                'success': False,
                'error': f"Failed to parse Excel file: {parse_result['error']}"
            }), 400
        
        # Generate AI insights if available
        ai_insights = {}
        if gemini_content_service.is_available():
            try:
                ai_insights = gemini_content_service.generate_report_insights(parse_result)
            except Exception as e:
                logger.warning(f"Failed to generate AI insights: {str(e)}")
        
        return jsonify({
            'success': True,
            'data': parse_result,
            'ai_insights': ai_insights,
            'filename': filename,
            'user_id': user_id,
            'upload_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error uploading Excel file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/generate-content-variations', methods=['POST'])
@jwt_required()
def generate_content_variations():
    """
    Generate AI content variations for report sections
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        excel_data = data.get('excel_data')
        section_type = data.get('section_type', 'executive_summary')
        
        if not excel_data:
            return jsonify({
                'success': False,
                'error': 'Excel data is required'
            }), 400
        
        # Extract data summary for AI
        primary_sheet = excel_data.get('primary_sheet', {})
        data_summary = {
            'total_records': primary_sheet.get('clean_rows', 0),
            'key_metrics': primary_sheet.get('statistics', {}),
            'categories': list(primary_sheet.get('field_categories', {}).values()),
            'time_period': 'Current analysis'
        }
        
        # Generate content variations
        if gemini_content_service.is_available():
            content_variations = gemini_content_service.generate_content_variations(
                data_summary, section_type
            )
        else:
            # Fallback content
            content_variations = {
                'variations': [
                    {
                        'style': 'professional',
                        'title': 'Executive Summary',
                        'content': 'This report provides a comprehensive analysis of the uploaded data with key insights and recommendations.',
                        'tone': 'formal'
                    },
                    {
                        'style': 'casual',
                        'title': 'Quick Overview',
                        'content': 'Here\'s what we found in your data! The analysis shows some interesting patterns worth exploring.',
                        'tone': 'friendly'
                    },
                    {
                        'style': 'technical',
                        'title': 'Data Analysis Summary', 
                        'content': 'Statistical analysis reveals significant patterns across multiple variables with measurable performance indicators.',
                        'tone': 'analytical'
                    },
                    {
                        'style': 'results',
                        'title': 'Key Results',
                        'content': 'Bottom line: Your data shows clear opportunities for improvement and areas of excellence.',
                        'tone': 'action-oriented'
                    }
                ]
            }
        
        return jsonify({
            'success': True,
            'content_variations': content_variations,
            'section_type': section_type,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating content variations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/generate-live-preview', methods=['POST'])
@jwt_required()
def generate_live_preview():
    """
    Generate live HTML preview of the report
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        excel_data = data.get('excel_data')
        template_type = data.get('template_type', 'professional')
        selected_content = data.get('selected_content')
        
        if not excel_data:
            return jsonify({
                'success': False,
                'error': 'Excel data is required'
            }), 400
        
        # Generate live preview
        preview_result = live_preview_generator.generate_live_preview(
            excel_data=excel_data,
            template_type=template_type,
            ai_content=selected_content
        )
        
        if not preview_result['success']:
            return jsonify({
                'success': False,
                'error': f"Preview generation failed: {preview_result.get('error', 'Unknown error')}"
            }), 500
        
        return jsonify({
            'success': True,
            'preview_html': preview_result['html_content'],
            'template_type': template_type,
            'charts_count': preview_result.get('charts_count', 0),
            'generated_at': preview_result['generated_at']
        })
        
    except Exception as e:
        logger.error(f"Error generating live preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/generate-multiple-previews', methods=['POST'])
@jwt_required()
def generate_multiple_previews():
    """
    Generate multiple preview variations for comparison
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        excel_data = data.get('excel_data')
        content_variations = data.get('content_variations')
        
        if not excel_data:
            return jsonify({
                'success': False,
                'error': 'Excel data is required'
            }), 400
        
        # Generate multiple previews
        previews_result = live_preview_generator.generate_content_variations_preview(
            excel_data=excel_data,
            content_variations=content_variations or {}
        )
        
        if not previews_result['success']:
            return jsonify({
                'success': False,
                'error': f"Multiple previews generation failed: {previews_result.get('error', 'Unknown error')}"
            }), 500
        
        return jsonify({
            'success': True,
            'preview_variations': previews_result['variations'],
            'variation_count': previews_result['variation_count'],
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating multiple previews: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/export-report', methods=['POST'])
@jwt_required()
def export_report():
    """
    Export report in various formats (PDF, Word, Excel)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        excel_data = data.get('excel_data')
        selected_content = data.get('selected_content')
        export_format = data.get('format', 'pdf').lower()
        template_type = data.get('template_type', 'professional')
        
        if not excel_data:
            return jsonify({
                'success': False,
                'error': 'Excel data is required'
            }), 400
        
        if export_format not in ['pdf', 'word', 'excel', 'html']:
            return jsonify({
                'success': False,
                'error': 'Invalid export format. Supported: pdf, word, excel, html'
            }), 400
        
        # Generate final report
        preview_result = live_preview_generator.generate_live_preview(
            excel_data=excel_data,
            template_type=template_type,
            ai_content=selected_content
        )
        
        if not preview_result['success']:
            return jsonify({
                'success': False,
                'error': f"Report generation failed: {preview_result.get('error', 'Unknown error')}"
            }), 500
        
        # For now, return HTML content - PDF/Word conversion would require additional libraries
        if export_format == 'html':
            # Save HTML to temporary file
            temp_dir = tempfile.mkdtemp()
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(preview_result['html_content'])
            
            return jsonify({
                'success': True,
                'message': 'Report generated successfully',
                'format': export_format,
                'filename': filename,
                'download_url': f'/api/enhanced-report/download/{filename}',
                'file_path': file_path
            })
        else:
            # For PDF/Word export, we would need additional libraries like weasyprint or python-docx
            return jsonify({
                'success': False,
                'error': f'{export_format.upper()} export not yet implemented. Please use HTML format.',
                'available_formats': ['html']
            }), 501
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_available_templates():
    """
    Get list of available report templates
    """
    try:
        templates = [
            {
                'id': 'professional',
                'name': 'Professional Report',
                'description': 'Clean, formal business report with comprehensive analysis',
                'style': 'formal',
                'color_scheme': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'],
                'preview_image': '/static/templates/professional_preview.png'
            },
            {
                'id': 'training',
                'name': 'Training Analysis',
                'description': 'Focused on training programs and educational metrics',
                'style': 'educational',
                'color_scheme': ['#27AE60', '#2980B9', '#E74C3C', '#F39C12'],
                'preview_image': '/static/templates/training_preview.png'
            },
            {
                'id': 'analytics',
                'name': 'Data Analytics',
                'description': 'Technical analysis with detailed visualizations',
                'style': 'technical',
                'color_scheme': ['#8E44AD', '#3498DB', '#E67E22', '#E74C3C'],
                'preview_image': '/static/templates/analytics_preview.png'
            },
            {
                'id': 'executive',
                'name': 'Executive Summary',
                'description': 'High-level overview for executive decision making',
                'style': 'executive',
                'color_scheme': ['#34495E', '#2C3E50', '#95A5A6', '#BDC3C7'],
                'preview_image': '/static/templates/executive_preview.png'
            }
        ]
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/chart-suggestions', methods=['POST'])
@jwt_required()
def get_chart_suggestions():
    """
    Get AI-powered chart suggestions based on Excel data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        excel_data = data.get('excel_data')
        
        if not excel_data:
            return jsonify({
                'success': False,
                'error': 'Excel data is required'
            }), 400
        
        # Generate chart suggestions
        if gemini_content_service.is_available():
            chart_suggestions = gemini_content_service.generate_chart_suggestions(excel_data)
        else:
            # Fallback suggestions
            chart_suggestions = [
                {
                    'type': 'bar',
                    'title': 'Data Overview',
                    'x_axis': 'categories',
                    'y_axis': 'values',
                    'description': 'Bar chart showing data distribution',
                    'priority': 1
                },
                {
                    'type': 'line',
                    'title': 'Trends Over Time',
                    'x_axis': 'date',
                    'y_axis': 'values',
                    'description': 'Line chart showing trends',
                    'priority': 2
                }
            ]
        
        return jsonify({
            'success': True,
            'chart_suggestions': chart_suggestions,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting chart suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_report_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the enhanced report builder
    """
    try:
        status = {
            'service': 'Enhanced Report Builder',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'gemini_ai': gemini_content_service.is_available(),
                'excel_parser': True,
                'preview_generator': True
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'service': 'Enhanced Report Builder',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Error handlers
@enhanced_report_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@enhanced_report_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@enhanced_report_bp.errorhandler(413)
def file_too_large(error):
    return jsonify({
        'success': False,
        'error': 'File too large',
        'message': 'The uploaded file exceeds the maximum size limit'
    }), 413
