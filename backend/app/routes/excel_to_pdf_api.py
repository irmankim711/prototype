"""
Excel to PDF API Routes
Unified endpoint for Excel upload and PDF report generation
"""

from flask import Blueprint, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
import os
import logging
import tempfile
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Import services with error handling
try:
    from ..services.docx_preview_service import docx_preview_service
except ImportError:
    logger.warning("docx_preview_service not available")
    docx_preview_service = None

try:
    from ..services.convertapi_service import convertapi_service
except ImportError:
    logger.warning("convertapi_service not available")
    convertapi_service = None

excel_to_pdf_bp = Blueprint('excel_to_pdf', __name__, url_prefix='/api/excel-to-pdf')

@excel_to_pdf_bp.route('/upload-and-generate', methods=['POST'])
def upload_excel_and_generate_report():
    """
    Upload Excel file and generate PDF report

    Form data:
    - file: Excel file (.xlsx, .xls)
    - title: Optional report title
    - formats: Comma-separated formats (e.g., "docx,pdf")
    - template: Template type (default: excel_analysis)
    """
    return jsonify({'error': 'This endpoint is under development'}), 501

@excel_to_pdf_bp.route('/preview/<int:report_id>', methods=['GET'])
def preview_generated_report(report_id):
    """
    Preview generated report (if supported by format)
    """
    try:
        from ..models import Report

        # Get the report (temporarily without user filtering for testing)
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Handle missing file path - try to find TeX file by report title/date
        if not report.file_path:
            # Try to find a matching TeX file for this report
            static_dir = os.path.join(os.getcwd(), 'static', 'generated')
            potential_files = []

            if os.path.exists(static_dir):
                # Look for TeX files that might match this report
                for file in os.listdir(static_dir):
                    if file.endswith('.tex') and ('Temp1' in file or 'SENARAI' in file.upper()):
                        potential_files.append(file)

            if potential_files:
                # Use the most recent matching file
                potential_files.sort(reverse=True)  # Sort by name (includes date)
                report.file_path = os.path.join(static_dir, potential_files[0])
                logger.info(f"Found matching TeX file for report {report.id}: {potential_files[0]}")
            else:
                return jsonify({
                    'error': 'Report file path is empty and no matching TeX files found',
                    'report_id': report.id,
                    'title': report.title,
                    'file_format': report.file_format
                }), 404

        # Check if file exists
        if not os.path.exists(report.file_path):
            return jsonify({'error': 'Report file not found'}), 404

        # Generate preview based on format and actual file extension
        preview_url = None
        preview_type = 'data'
        preview_data = None

        # Check actual file extension to determine real format
        file_extension = os.path.splitext(report.file_path)[1].lower() if report.file_path else ''

        if file_extension == '.tex':
            # Handle TeX files - convert to HTML
            try:
                # Read the TeX content
                with open(report.file_path, 'r', encoding='utf-8') as f:
                    tex_content = f.read()

                # Convert TeX to simple HTML
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .content {{ line-height: 1.6; }}
        .section {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <div class="content">
        <pre style="white-space: pre-wrap; font-family: inherit;">{tex_content}</pre>
    </div>
</body>
</html>"""

                # Save HTML preview
                preview_filename = f"tex_preview_{report.id}.html"
                preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
                os.makedirs(preview_dir, exist_ok=True)
                preview_path = os.path.join(preview_dir, preview_filename)

                with open(preview_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                preview_url = f"/static/previews/{preview_filename}"
                preview_type = 'html'

                logger.info(f"Generated TeX preview for report {report.id}: {preview_path}")

            except Exception as e:
                logger.error(f"Failed to generate TeX preview: {str(e)}")
                preview_data = {
                    'title': report.title,
                    'file_format': report.file_format,
                    'actual_format': 'tex',
                    'file_size': report.file_size,
                    'created_at': report.created_at.isoformat(),
                    'download_url': f"/api/reports/download/{os.path.basename(report.file_path)}",
                    'error': f"TeX preview generation failed: {str(e)}"
                }
                preview_type = 'data'

        elif report.file_format == 'docx' or file_extension == '.docx':
            # Generate HTML preview for DOCX files
            if docx_preview_service:
                try:
                    html_file_path, html_content = docx_preview_service.convert_docx_to_html(report.file_path)
                    preview_url = f"/static/previews/{os.path.basename(html_file_path)}"
                    preview_type = 'html'
                except Exception as e:
                    logger.warning(f"Failed to generate DOCX preview with docx_preview_service: {str(e)}")
                    # Fallback to ConvertAPI for preview
                    if convertapi_service:
                        try:
                            success, message, html_path = convertapi_service.convert_docx_to_html_preview(report.file_path)
                            if success and html_path:
                                preview_url = f"/static/previews/{os.path.basename(html_path)}"
                                preview_type = 'html'
                                logger.info(f"ConvertAPI preview generated successfully: {html_path}")
                            else:
                                logger.warning(f"ConvertAPI preview failed: {message}")
                                preview_type = 'data'
                        except Exception as convert_e:
                            logger.error(f"ConvertAPI preview fallback failed: {str(convert_e)}")
                            preview_type = 'data'
                    else:
                        logger.warning("convertapi_service not available")
                        preview_type = 'data'
            else:
                logger.warning("docx_preview_service not available, falling back to data preview")
                preview_type = 'data'

            # Set preview_data if we're falling back to data type
            if preview_type == 'data':
                preview_data = {
                    'title': report.title,
                    'format': report.file_format,
                    'file_size': report.file_size,
                    'created_at': report.created_at.isoformat() if report.created_at else None,
                    'download_url': f"/api/reports/download/{os.path.basename(report.file_path)}",
                    'message': 'Preview service not available'
                }

        else:
            # Unknown format
            preview_data = {
                'title': report.title,
                'format': report.file_format,
                'file_size': report.file_size,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'error': 'Unsupported format for preview'
            }
            preview_type = 'data'

        return jsonify({
            'success': True,
            'preview_type': preview_type,
            'preview_url': preview_url,
            'preview_data': preview_data
        }), 200

    except Exception as e:
        logger.error(f"Error generating preview for report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to generate preview'}), 500


@excel_to_pdf_bp.route('/preview-content/<int:report_id>', methods=['GET'])
def get_preview_content(report_id):
    """
    Get preview content (HTML) for direct display
    """
    try:
        from ..models import Report

        # Get the report (temporarily without user filtering for testing)
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Ensure file exists
        if not report.file_path or not os.path.exists(report.file_path):
            return Response('<html><body><h1>File not found</h1></body></html>', mimetype='text/html'), 404

        file_extension = os.path.splitext(report.file_path)[1].lower()

        # For TeX files - convert to HTML
        if report.file_format == 'tex' or file_extension == '.tex':
            try:
                from ..services.latex_conversion_service import latex_conversion_service
                html_content = latex_conversion_service.generate_html_preview(report.file_path)
                return Response(html_content, mimetype='text/html')
            except Exception as e:
                logger.error(f"Failed to generate TeX preview content: {str(e)}")
                return jsonify({'error': f'Failed to generate TeX preview: {str(e)}'}), 500

        elif report.file_format == 'docx' or file_extension == '.docx':
            if docx_preview_service:
                try:
                    _, html_content = docx_preview_service.convert_docx_to_html(report.file_path)
                    return Response(html_content, mimetype='text/html')
                except Exception as e:
                    logger.warning(f"Failed to generate DOCX preview with docx_preview_service: {str(e)}")
                    if convertapi_service:
                        try:
                            success, message, html_path = convertapi_service.convert_docx_to_html_preview(report.file_path)
                            if success and html_path and os.path.exists(html_path):
                                with open(html_path, 'r', encoding='utf-8') as f:
                                    html_content = f.read()
                                return Response(html_content, mimetype='text/html')
                            else:
                                return Response(f'<html><body><h1>Preview Failed</h1><p>{message}</p></body></html>', mimetype='text/html'), 500
                        except Exception as fallback_error:
                            logger.error(f"ConvertAPI preview fallback failed: {str(fallback_error)}")
                            return Response(f'<html><body><h1>Preview Error</h1><p>{str(fallback_error)}</p></body></html>', mimetype='text/html'), 500
                    else:
                        return Response('<html><body><h1>Preview Not Available</h1><p>Preview service not configured</p></body></html>', mimetype='text/html'), 503
            else:
                return Response('<html><body><h1>Preview Not Available</h1><p>DOCX preview service not configured</p></body></html>', mimetype='text/html'), 503

        else:
            return Response('<html><body><h1>Unsupported Format</h1><p>Preview not available for this format</p></body></html>', mimetype='text/html'), 400

    except Exception as e:
        logger.error(f"Error getting preview content for report {report_id}: {str(e)}")
        return Response(f'<html><body><h1>Error</h1><p>{str(e)}</p></body></html>', mimetype='text/html'), 500


@excel_to_pdf_bp.route('/status', methods=['GET'])
def get_conversion_status():
    """
    Get status of recent conversions for the user
    """
    try:
        from ..models import Report

        # Get recent reports (temporarily without user filtering)
        reports = Report.query.order_by(Report.created_at.desc())\
                             .limit(10).all()

        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'format': report.file_format,
                'status': report.status,
                'file_size': report.file_size,
                'created_at': report.created_at.isoformat(),
                'download_url': f"/api/reports/download/{os.path.basename(report.file_path)}",
                'metadata': report.metadata_
            })

        return jsonify({
            'success': True,
            'reports': reports_data,
            'total_count': len(reports_data)
        }), 200

    except Exception as e:
        logger.error(f"Status retrieval failed: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve status',
            'message': str(e)
        }), 500

@excel_to_pdf_bp.route('/preview-content/<int:report_id>', methods=['GET'])
def get_preview_content(report_id):
    """
    Get the HTML content for preview (embedded mode)
    """
    try:
        from ..models import Report
        from flask import Response

        # Get the report (temporarily without user filtering for testing)
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Handle missing file path - try to find TeX file by report title/date
        if not report.file_path:
            # Try to find a matching TeX file for this report
            static_dir = os.path.join(os.getcwd(), 'static', 'generated')
            potential_files = []

            if os.path.exists(static_dir):
                # Look for TeX files that might match this report
                for file in os.listdir(static_dir):
                    if file.endswith('.tex') and ('Temp1' in file or 'SENARAI' in file.upper()):
                        potential_files.append(file)

            if potential_files:
                # Use the most recent matching file
                potential_files.sort(reverse=True)  # Sort by name (includes date)
                report.file_path = os.path.join(static_dir, potential_files[0])
                logger.info(f"Found matching TeX file for report {report.id}: {potential_files[0]}")
            else:
                return jsonify({
                    'error': 'Report file path is empty and no matching TeX files found',
                    'report_id': report.id,
                    'title': report.title,
                    'file_format': report.file_format
                }), 404

        # Check if file exists
        if not os.path.exists(report.file_path):
            return jsonify({'error': 'Report file not found'}), 404

        # Check actual file extension to determine real format
        file_extension = os.path.splitext(report.file_path)[1].lower() if report.file_path else ''

        # Generate HTML preview for different file types
        if file_extension == '.tex':
            # Handle TeX files - convert to HTML
            try:
                # Read the TeX content
                with open(report.file_path, 'r', encoding='utf-8') as f:
                    tex_content = f.read()

                # Convert TeX to formatted HTML (same as preview endpoint)
                lines = tex_content.split('\n')
                formatted_content = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Enhanced formatting for this specific report
                    if 'LAPORAN PROGRAM' in line.upper():
                        formatted_content.append(f'<h1 style="text-align: center; color: #2c3e50;">{line}</h1>')
                    elif any(keyword in line.upper() for keyword in ['MAKLUMAT PROGRAM', 'OBJEKTIF KURSUS', 'TENTATIF PROGRAM']):
                        formatted_content.append(f'<h2 style="background: #3498db; color: white; padding: 10px; margin-top: 25px;">{line}</h2>')
                    elif any(keyword in line.upper() for keyword in ['LOKASI', 'LOCATION', 'ANJURAN', 'ORGANIZER', 'TARIKH']):
                        formatted_content.append(f'<h3 style="color: #34495e; border-bottom: 1px solid #bdc3c7;">{line}</h3>')
                    elif line.isupper() and len(line) > 3 and not line.startswith('9:00'):
                        formatted_content.append(f'<div style="background: #ecf0f1; padding: 8px; margin: 5px 0; font-weight: bold;">{line}</div>')
                    elif 'PERUNDING MUBARAK RESOURCES' in line:
                        formatted_content.append(f'<div style="text-align: center; font-size: 18px; color: #27ae60; font-weight: bold; margin: 15px 0;">{line}</div>')
                    elif '9:00 AM - 5:00 PM' in line:
                        formatted_content.append(f'<div style="text-align: center; background: #f39c12; color: white; padding: 5px; border-radius: 3px;">{line}</div>')
                    else:
                        formatted_content.append(f'<p style="margin: 8px 0; line-height: 1.5;">{line}</p>')

                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-top: 5px solid #3498db;
        }}
    </style>
</head>
<body>
    <div class="container">
        {''.join(formatted_content)}
    </div>
</body>
</html>"""

                return Response(html_content, mimetype='text/html')

            except Exception as e:
                logger.error(f"Failed to generate TeX preview content: {str(e)}")
                return jsonify({'error': f'Failed to generate TeX preview: {str(e)}'}), 500

        elif report.file_format == 'docx' or file_extension == '.docx':
            try:
                _, html_content = docx_preview_service.convert_docx_to_html(report.file_path)
                return Response(html_content, mimetype='text/html')
            except Exception as e:
                logger.warning(f"Failed to generate DOCX preview with docx_preview_service: {str(e)}")
                # Fallback to ConvertAPI for preview
                try:
                    success, message, html_path = convertapi_service.convert_docx_to_html_preview(report.file_path)
                    if success and html_path and os.path.exists(html_path):
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        return Response(html_content, mimetype='text/html')
                    else:
                        logger.error(f"ConvertAPI preview failed: {message}")
                        return jsonify({'error': f'ConvertAPI preview failed: {message}'}), 500
                except Exception as convert_e:
                    logger.error(f"ConvertAPI preview fallback failed: {str(convert_e)}")
                    return jsonify({'error': 'Failed to generate preview with both services'}), 500
        else:
            return jsonify({
                'error': f'Preview not available for {report.file_format} format'
            }), 400

    except Exception as e:
        logger.error(f"Preview content generation failed: {str(e)}")
        return jsonify({
            'error': 'Failed to get preview content',
            'message': str(e)
        }), 500

@excel_to_pdf_bp.route('/convert-test', methods=['POST'])
def test_convertapi_connection():
    """
    Test ConvertAPI connection and credentials
    """
    try:
        test_result = convertapi_service.test_connection()

        return jsonify({
            'success': test_result['success'],
            'message': test_result.get('message', test_result.get('error')),
            'service_info': convertapi_service.get_conversion_info(),
            'user_info': test_result.get('user_info', {})
        }), 200

    except Exception as e:
        logger.error(f"ConvertAPI test failed: {str(e)}")
        return jsonify({
            'error': 'ConvertAPI test failed',
            'message': str(e)
        }), 500

@excel_to_pdf_bp.route('/generate-senarai-preview', methods=['GET'])
def generate_senarai_preview():
    """Generate preview specifically for SENARAI SEMAK PUNCAK ALAM report"""
    try:
        # Look for the specific TeX file
        tex_file = "report_Temp1_20250829_001423.tex"
        static_dir = os.path.join(os.getcwd(), 'static', 'generated')
        tex_path = os.path.join(static_dir, tex_file)

        if not os.path.exists(tex_path):
            return jsonify({'error': f'TeX file not found: {tex_file}'}), 404

        # Read the TeX content
        with open(tex_path, 'r', encoding='utf-8') as f:
            tex_content = f.read()

        # Convert TeX to HTML with better formatting for this specific report
        lines = tex_content.split('\n')
        formatted_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Enhanced formatting for this specific report
            if 'LAPORAN PROGRAM' in line.upper():
                formatted_content.append(f'<h1 style="text-align: center; color: #2c3e50;">{line}</h1>')
            elif any(keyword in line.upper() for keyword in ['MAKLUMAT PROGRAM', 'OBJEKTIF KURSUS', 'TENTATIF PROGRAM']):
                formatted_content.append(f'<h2 style="background: #3498db; color: white; padding: 10px; margin-top: 25px;">{line}</h2>')
            elif any(keyword in line.upper() for keyword in ['LOKASI', 'LOCATION', 'ANJURAN', 'ORGANIZER', 'TARIKH']):
                formatted_content.append(f'<h3 style="color: #34495e; border-bottom: 1px solid #bdc3c7;">{line}</h3>')
            elif line.isupper() and len(line) > 3 and not line.startswith('9:00'):
                formatted_content.append(f'<div style="background: #ecf0f1; padding: 8px; margin: 5px 0; font-weight: bold;">{line}</div>')
            elif 'PERUNDING MUBARAK RESOURCES' in line:
                formatted_content.append(f'<div style="text-align: center; font-size: 18px; color: #27ae60; font-weight: bold; margin: 15px 0;">{line}</div>')
            elif '9:00 AM - 5:00 PM' in line:
                formatted_content.append(f'<div style="text-align: center; background: #f39c12; color: white; padding: 5px; border-radius: 3px;">{line}</div>')
            else:
                formatted_content.append(f'<p style="margin: 8px 0; line-height: 1.5;">{line}</p>')

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LAPORAN KURSUS FIQH USRAH DAERAH KUALA SELANGOR</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-top: 5px solid #3498db;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #3498db;
        }}
        .content {{
            margin-top: 20px;
        }}
        .file-info {{
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="color: #2c3e50; margin: 0;">📊 Report Preview</h1>
            <p style="color: #7f8c8d; margin: 5px 0;">Generated from TeX source file</p>
        </div>

        <div class="file-info">
            <strong>📁 Source File:</strong> {tex_file}<br>
            <strong>📊 Content:</strong> {len(tex_content)} characters<br>
            <strong>🔄 Format:</strong> TeX to HTML conversion<br>
            <strong>📅 Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>

        <div class="content">
            {''.join(formatted_content)}
        </div>

        <div class="footer">
            Generated by Automated Report System • ConvertAPI Integration Active
        </div>
    </div>
</body>
</html>"""

        # Save HTML preview
        preview_filename = "senarai_report_preview.html"
        preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
        os.makedirs(preview_dir, exist_ok=True)
        preview_path = os.path.join(preview_dir, preview_filename)

        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return jsonify({
            'success': True,
            'message': 'SENARAI SEMAK PUNCAK ALAM preview generated successfully',
            'tex_file': tex_file,
            'preview_url': f"/static/previews/{preview_filename}",
            'content_length': len(tex_content),
            'preview_path': preview_path,
            'report_title': 'LAPORAN KURSUS FIQH USRAH DAERAH KUALA SELANGOR'
        })

    except Exception as e:
        return jsonify({
            'error': 'Failed to generate SENARAI preview',
            'message': str(e)
        }), 500

@excel_to_pdf_bp.route('/generate-preview-from-tex', methods=['GET'])
def generate_preview_from_tex():
    """Generate preview from available TeX files"""
    try:
        # Look for TeX files in static/generated
        static_dir = os.path.join(os.getcwd(), 'static', 'generated')
        tex_files = []

        if os.path.exists(static_dir):
            for file in os.listdir(static_dir):
                if file.endswith('.tex'):
                    tex_files.append(file)

        if not tex_files:
            return jsonify({'error': 'No TeX files found'}), 404

        # Use the first TeX file
        tex_file = tex_files[0]
        tex_path = os.path.join(static_dir, tex_file)

        # Read the TeX content
        with open(tex_path, 'r', encoding='utf-8') as f:
            tex_content = f.read()

        # Convert TeX to HTML with better formatting
        lines = tex_content.split('\n')
        formatted_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Format headers and sections
            if any(keyword in line.upper() for keyword in ['LAPORAN', 'MAKLUMAT', 'OBJEKTIF', 'TENTATIF']):
                formatted_content.append(f'<h2>{line}</h2>')
            elif line.isupper() and len(line) > 3:
                formatted_content.append(f'<h3>{line}</h3>')
            else:
                formatted_content.append(f'<p>{line}</p>')

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Report Preview - {tex_file}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            line-height: 1.6;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        p {{
            margin: 10px 0;
            color: #555;
        }}
        .file-info {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            font-size: 14px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Report Preview</h1>
        <div class="file-info">
            <strong>Source:</strong> {tex_file}<br>
            <strong>Generated:</strong> TeX to HTML conversion<br>
            <strong>Content Length:</strong> {len(tex_content)} characters
        </div>
        <div class="content">
            {''.join(formatted_content)}
        </div>
    </div>
</body>
</html>"""

        # Save HTML preview
        preview_filename = f"tex_formatted_preview.html"
        preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
        os.makedirs(preview_dir, exist_ok=True)
        preview_path = os.path.join(preview_dir, preview_filename)

        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return jsonify({
            'success': True,
            'message': 'Preview generated from TeX file',
            'tex_file': tex_file,
            'tex_path': tex_path,
            'preview_url': f"/static/previews/{preview_filename}",
            'preview_path': preview_path,
            'content_length': len(tex_content),
            'available_tex_files': tex_files
        })

    except Exception as e:
        return jsonify({
            'error': 'Failed to generate preview from TeX',
            'message': str(e)
        }), 500

@excel_to_pdf_bp.route('/debug-report/<int:report_id>', methods=['GET'])
def debug_report(report_id):
    """Debug report details"""
    try:
        from ..models import Report

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        return jsonify({
            'report_id': report.id,
            'title': report.title,
            'file_format': report.file_format,
            'file_path': report.file_path,
            'file_exists': os.path.exists(report.file_path) if report.file_path else False,
            'file_extension': os.path.splitext(report.file_path)[1].lower() if report.file_path else None,
            'generation_status': report.generation_status,
            'created_at': report.created_at.isoformat(),
            'file_size': report.file_size
        })

    except Exception as e:
        return jsonify({
            'error': 'Debug failed',
            'message': str(e)
        }), 500

@excel_to_pdf_bp.route('/test-convertapi', methods=['GET'])
def test_convertapi():
    """Test ConvertAPI DOCX to HTML conversion"""
    try:
        from ..services.convertapi_service import convertapi_service

        # Find test DOCX file
        test_file = os.path.join(os.getcwd(), 'templates', 'Temp1.docx')

        if not os.path.exists(test_file):
            return jsonify({'error': 'Test DOCX file not found'}), 404

        # Generate HTML preview
        success, message, html_path = convertapi_service.convert_docx_to_html_preview(test_file)

        if success and html_path:
            # Copy to static directory for serving
            import shutil
            static_preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
            os.makedirs(static_preview_dir, exist_ok=True)

            preview_filename = os.path.basename(html_path)
            static_preview_path = os.path.join(static_preview_dir, preview_filename)
            shutil.copy2(html_path, static_preview_path)

            # Read a snippet of the HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            return jsonify({
                'success': True,
                'message': 'ConvertAPI preview generated successfully',
                'original_path': html_path,
                'static_path': static_preview_path,
                'preview_url': f"/static/previews/{preview_filename}",
                'html_size': len(html_content),
                'html_snippet': html_content[:500] + '...' if len(html_content) > 500 else html_content,
                'convertapi_working': True
            })
        else:
            return jsonify({
                'success': False,
                'error': message,
                'convertapi_working': False
            }), 500

    except Exception as e:
        return jsonify({
            'error': 'Test failed',
            'message': str(e),
            'convertapi_working': False
        }), 500

@excel_to_pdf_bp.route('/supported-formats', methods=['GET'])
def get_supported_formats():
    """
    Get list of supported input and output formats
    """
    return jsonify({
        'input_formats': [
            {
                'extension': '.xlsx',
                'description': 'Excel 2007+ Workbook',
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            {
                'extension': '.xls',
                'description': 'Excel 97-2003 Workbook',
                'mime_type': 'application/vnd.ms-excel'
            },
            {
                'extension': '.xlsm',
                'description': 'Excel Macro-Enabled Workbook',
                'mime_type': 'application/vnd.ms-excel.sheet.macroEnabled.12'
            }
        ],
        'output_formats': [
            {
                'format': 'docx',
                'description': 'Microsoft Word Document',
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            },
            {
                'format': 'pdf',
                'description': 'Portable Document Format',
                'mime_type': 'application/pdf'
            }
        ],
        'templates': [
            {
                'id': 'excel_analysis',
                'name': 'Excel Data Analysis',
                'description': 'Comprehensive analysis of Excel data with statistics and insights'
            },
            {
                'id': 'financial',
                'name': 'Financial Report',
                'description': 'Financial data analysis with charts and summaries'
            },
            {
                'id': 'executive',
                'name': 'Executive Summary',
                'description': 'High-level overview for executive presentation'
            }
        ]
    }), 200

@excel_to_pdf_bp.route('/examples', methods=['GET'])
def get_examples():
    """
    Get example requests and responses
    """
    return jsonify({
        'examples': {
            'upload_and_generate': {
                'description': 'Upload Excel file and generate report',
                'method': 'POST',
                'endpoint': '/api/excel-to-pdf/upload-and-generate',
                'headers': {
                    'Authorization': 'Bearer <firebase_token>'
                },
                'form_data': {
                    'file': '<excel_file>',
                    'title': 'Optional report title',
                    'formats': 'docx,pdf',
                    'template': 'excel_analysis'
                },
                'response': {
                    'success': True,
                    'report_id': 123,
                    'title': 'Analysis Report - data.xlsx',
                    'formats': {
                        'docx': {
                            'url': '/api/reports/download/report_20250101_120000.docx',
                            'filename': 'report_20250101_120000.docx',
                            'size': 1024000
                        },
                        'pdf': {
                            'url': '/api/reports/download/report_20250101_120000.pdf',
                            'filename': 'report_20250101_120000.pdf',
                            'size': 2048000,
                            'method': 'convertapi'
                        }
                    }
                }
            }
        }
    }), 200