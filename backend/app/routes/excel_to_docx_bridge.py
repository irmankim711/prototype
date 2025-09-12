"""
Excel to DOCX Bridge API
Direct conversion from Excel files to DOCX reports
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
from ..core.auth import jwt_required
from ..services.excel_parser import ExcelTableDetector
from ..services.report_generation_service import ReportGenerationService
from ..services.form_automation import FormAutomationService
from ..services.docx_preview_service import docx_preview_service
from .. import db
from ..models import Report, User

logger = logging.getLogger(__name__)

excel_to_docx_bp = Blueprint('excel_to_docx_bridge', __name__, url_prefix='/api/excel-to-docx')

@excel_to_docx_bp.route('/convert', methods=['POST'])
@jwt_required
def convert_excel_to_docx(current_user):
    """
    Convert uploaded Excel file directly to DOCX report
    
    Expected form data:
    - file: Excel file (.xlsx, .xls)
    - title: Report title (optional)
    - template: Template to use (optional)
    """
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Only Excel files (.xlsx, .xls) are supported'}), 400
        
        # Get optional parameters
        report_title = request.form.get('title', f'Report from {file.filename}')
        template_name = request.form.get('template', 'default')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'excel')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)
        file.save(file_path)
        
        # Initialize services
        form_automation = FormAutomationService()
        report_service = ReportGenerationService()
        
        # Parse Excel file
        logger.info(f"Parsing Excel file: {file_path}")
        excel_result = form_automation.excel_parser.parse_excel_file(file_path)
        
        if not excel_result['success']:
            return jsonify({
                'error': f"Failed to parse Excel file: {excel_result.get('error', 'Unknown error')}"
            }), 400
        
        # Generate DOCX report from parsed data
        logger.info(f"Generating DOCX report with template: {template_name}")
        
        # Extract data for report generation
        excel_data = excel_result.get('data', {})
        sheets = excel_data.get('sheets', {})
        
        # Prepare report data structure
        report_data = {
            'title': report_title,
            'source_file': filename,
            'generated_at': datetime.now().isoformat(),
            'sheets': []
        }
        
        # Process each sheet
        for sheet_name, sheet_data in sheets.items():
            if sheet_data.get('tables'):
                for table in sheet_data['tables']:
                    # Convert table data to report format
                    table_info = {
                        'sheet_name': sheet_name,
                        'table_name': table.get('title', f'Table from {sheet_name}'),
                        'headers': table.get('headers', []),
                        'data': table.get('data', []),
                        'stats': table.get('statistics', {}),
                        'chart_suggestions': table.get('chart_suggestions', [])
                    }
                    report_data['sheets'].append(table_info)
        
        # Generate DOCX using report service
        config = {
            'title': report_title,
            'template': template_name,
            'format': 'docx',
            'include_charts': True,
            'include_statistics': True
        }
        
        docx_path, file_size = report_service.generate_docx_report(report_data, config)
        
        # Create database record
        report = Report(
            title=report_title,
            description=f'Generated from Excel file: {filename}',
            file_path=docx_path,
            file_size=file_size,
            format='docx',
            status='completed',
            user_id=current_user.id,
            metadata_={
                'source_file': filename,
                'source_type': 'excel',
                'sheets_processed': len(report_data['sheets']),
                'template_used': template_name,
                'generation_method': 'excel_to_docx_bridge'
            }
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Clean up uploaded Excel file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up uploaded file: {e}")
        
        return jsonify({
            'success': True,
            'report_id': report.id,
            'title': report.title,
            'file_path': report.file_path,
            'file_size': report.file_size,
            'download_url': f'/api/reports/{report.id}/download',
            'preview_url': f'/api/excel-to-docx/{report.id}/preview',
            'edit_url': f'/reports/{report.id}/edit',
            'metadata': report.metadata_
        }), 201
        
    except Exception as e:
        logger.error(f"Excel to DOCX conversion failed: {str(e)}")
        return jsonify({
            'error': f'Failed to convert Excel to DOCX: {str(e)}'
        }), 500


@excel_to_docx_bp.route('/templates', methods=['GET'])
@jwt_required
def get_available_templates(current_user):
    """Get list of available DOCX templates"""
    try:
        # This would typically load from a templates directory
        templates = [
            {
                'id': 'default',
                'name': 'Default Business Report',
                'description': 'Clean, professional layout with charts and tables'
            },
            {
                'id': 'financial',
                'name': 'Financial Report',
                'description': 'Optimized for financial data with emphasis on numbers'
            },
            {
                'id': 'executive',
                'name': 'Executive Summary',
                'description': 'High-level overview format for executive presentations'
            },
            {
                'id': 'detailed',
                'name': 'Detailed Analysis',
                'description': 'Comprehensive format with extensive data tables'
            }
        ]
        
        return jsonify({
            'templates': templates,
            'default': 'default'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        return jsonify({'error': 'Failed to retrieve templates'}), 500


@excel_to_docx_bp.route('/<int:report_id>/preview', methods=['GET'])
@jwt_required
def preview_docx_report(current_user, report_id):
    """
    Generate HTML preview of a DOCX report
    """
    try:
        # Get the report from database
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check if file exists
        if not os.path.exists(report.file_path):
            return jsonify({'error': 'Report file not found'}), 404
        
        # Generate HTML preview
        if report.format == 'docx':
            preview_url = docx_preview_service.get_preview_url(report.file_path)
            
            return jsonify({
                'success': True,
                'preview_url': preview_url,
                'preview_type': 'html',
                'report_id': report.id,
                'title': report.title
            }), 200
        else:
            return jsonify({
                'error': f'Preview not supported for format: {report.format}'
            }), 400
            
    except Exception as e:
        logger.error(f"Preview generation failed: {str(e)}")
        return jsonify({
            'error': f'Failed to generate preview: {str(e)}'
        }), 500


@excel_to_docx_bp.route('/preview-content/<int:report_id>', methods=['GET'])
@jwt_required 
def get_preview_content(current_user, report_id):
    """
    Get the actual HTML content for preview (embedded mode)
    """
    try:
        # Get the report from database
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check if file exists
        if not os.path.exists(report.file_path):
            return jsonify({'error': 'Report file not found'}), 404
        
        # Convert DOCX to HTML and get content
        if report.format == 'docx':
            _, html_content = docx_preview_service.convert_docx_to_html(report.file_path)
            
            # Return HTML content directly
            from flask import Response
            return Response(html_content, mimetype='text/html')
        else:
            return jsonify({
                'error': f'Preview not supported for format: {report.format}'
            }), 400
            
    except Exception as e:
        logger.error(f"Preview content generation failed: {str(e)}")
        return jsonify({
            'error': f'Failed to get preview content: {str(e)}'
        }), 500