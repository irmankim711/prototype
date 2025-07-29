from flask import Blueprint, jsonify, request, send_from_directory, current_app
from docxtpl import DocxTemplate
import os
import uuid
from docx import Document
import base64
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from app.services.ai_service import ai_service
import logging

# Set up logging
logger = logging.getLogger(__name__)

mvp = Blueprint('mvp', __name__)

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

@mvp.route('/ai/analyze', methods=['POST'])
def ai_analyze():
    """
    Enhanced AI analysis endpoint using OpenAI for comprehensive data analysis
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided for analysis',
                'summary': 'Analysis failed - missing data',
                'insights': [],
                'suggestions': ['Please provide data to analyze']
            }), 400
        
        # Extract context and analysis type from request
        context = data.get('context', 'general')
        analysis_data = data.get('data', data)
        
        # Log the analysis request
        logger.info(f"AI analysis requested for context: {context}")
        
        # Call enhanced AI service
        result = ai_service.analyze_data(analysis_data, context)
        
        # Ensure the response includes all expected fields for frontend compatibility
        response = {
            'success': result.get('success', True),
            'summary': result.get('summary', 'Analysis completed'),
            'insights': result.get('insights', []),
            'patterns': result.get('patterns', []),
            'anomalies': result.get('anomalies', []),
            'recommendations': result.get('recommendations', []),
            'risks': result.get('risks', []),
            'opportunities': result.get('opportunities', []),
            'confidence_score': result.get('confidence_score', 0.8),
            'data_quality': result.get('data_quality', 'medium'),
            'analysis_type': context,
            'timestamp': result.get('timestamp'),
            'suggestions': result.get('recommendations', [])  # For backward compatibility
        }
        
        if not result.get('success', True):
            response['error'] = result.get('error', 'Unknown error occurred')
            return jsonify(response), 500
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in AI analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'summary': 'Analysis failed due to technical error',
            'insights': ['Technical error prevented analysis completion'],
            'suggestions': ['Please check your data format and try again'],
            'patterns': [],
            'anomalies': [],
            'recommendations': [],
            'risks': ['Analysis incomplete'],
            'opportunities': [],
            'confidence_score': 0.0
        }), 500

@mvp.route('/ai/report-suggestions', methods=['POST'])
def ai_report_suggestions():
    """
    Generate AI-powered suggestions for report content based on data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided for suggestions'
            }), 400
        
        report_type = data.get('report_type', 'general')
        report_data = data.get('data', data)
        
        logger.info(f"AI report suggestions requested for type: {report_type}")
        
        result = ai_service.generate_report_suggestions(report_data, report_type)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in AI report suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'suggestions': {}
        }), 500

@mvp.route('/ai/optimize-template', methods=['POST'])
def ai_optimize_template():
    """
    Use AI to analyze and optimize document templates
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('template_content'):
            return jsonify({
                'success': False,
                'error': 'Template content is required'
            }), 400
        
        template_content = data.get('template_content', '')
        placeholders = data.get('placeholders', [])
        template_type = data.get('template_type', 'general')
        
        logger.info(f"AI template optimization requested for type: {template_type}")
        
        result = ai_service.optimize_template(template_content, placeholders, template_type)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in AI template optimization: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'optimization': {}
        }), 500

@mvp.route('/ai/validate-data', methods=['POST'])
def ai_validate_data():
    """
    AI-powered data quality validation and suggestions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided for validation'
            }), 400
        
        validation_data = data.get('data', data)
        
        logger.info("AI data validation requested")
        
        result = ai_service.validate_data_quality(validation_data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in AI data validation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'validation': {
                'overall_quality_score': 0.0,
                'data_readiness': 'unknown',
                'issues_found': []
            }
        }), 500

@mvp.route('/ai/smart-placeholders', methods=['POST'])
def ai_smart_placeholders():
    """
    Generate intelligent placeholder suggestions based on context and industry
    """
    try:
        data = request.get_json()
        
        context = data.get('context', 'general') if data else 'general'
        industry = data.get('industry', 'general') if data else 'general'
        
        logger.info(f"AI placeholder suggestions requested for context: {context}, industry: {industry}")
        
        result = ai_service.generate_smart_placeholders(context, industry)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating smart placeholders: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'placeholders': {}
        }), 500

@mvp.route('/ai/health', methods=['GET'])
def ai_health_check():
    """
    Check AI service health and API key status
    """
    try:
        # Check if OpenAI API key is configured
        openai_configured = bool(ai_service.openai_api_key and ai_service.openai_api_key.startswith('sk-'))
        google_ai_configured = bool(ai_service.google_ai_api_key)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': {
                'openai': {
                    'configured': openai_configured,
                    'status': 'ready' if openai_configured else 'not_configured'
                },
                'google_ai': {
                    'configured': google_ai_configured,
                    'status': 'ready' if google_ai_configured else 'not_configured'
                }
            },
            'features_available': [
                'data_analysis',
                'report_suggestions',
                'template_optimization',
                'data_validation',
                'smart_placeholders'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in AI health check: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@mvp.route('/templates/<template_name>/placeholders', methods=['GET'])
def extract_placeholders_from_stored(template_name):
    """
    Returns a JSON list of unique placeholders found in the .docx template stored on the server.
    Example: GET /mvp/templates/04-%20LAPORAN%20FU%20_%20PUNCAK%20ALAM.docx/placeholders
    """
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(template_name)
    template_path = os.path.join(TEMPLATE_DIR, safe_name)

    if not os.path.isfile(template_path):
        return jsonify({'error': 'Template not found'}), 404

    try:
        # First try to open with python-docx to check if it's a valid Word document
        doc = Document(template_path)
        
        # Extract placeholders manually from the document content
        import re
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        all_placeholders = set()
        
        for paragraph in doc.paragraphs:
            if paragraph.text:
                placeholders = re.findall(placeholder_pattern, paragraph.text)
                all_placeholders.update(placeholders)
        
        # Also check table cells
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text:
                            placeholders = re.findall(placeholder_pattern, paragraph.text)
                            all_placeholders.update(placeholders)
        
        return jsonify({'placeholders': list(all_placeholders)})
        
    except Exception as e:
        return jsonify({'error': f'Failed to process template: {str(e)}'}), 500

@mvp.route('/templates/<template_name>/content', methods=['GET'])
def extract_template_content(template_name):
    """
    Extracts the raw content from a Word template for frontend editing.
    Preserves formatting information and structure.
    """
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(template_name)
    template_path = os.path.join(TEMPLATE_DIR, safe_name)

    if not os.path.isfile(template_path):
        return jsonify({'error': 'Template not found'}), 404

    try:
        doc = Document(template_path)
        content = []
        
        import re
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        all_placeholders = set()
        
        # Process paragraphs with formatting information
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                # Extract formatting information
                formatting = {
                    'style': paragraph.style.name if paragraph.style else 'Normal',
                    'alignment': paragraph.alignment,
                    'font_size': None,
                    'font_name': None,
                    'bold': False,
                    'italic': False
                }
                
                # Try to extract font information from runs
                for run in paragraph.runs:
                    if run.font.size:
                        formatting['font_size'] = run.font.size.pt
                    if run.font.name:
                        formatting['font_name'] = run.font.name
                    if run.bold:
                        formatting['bold'] = True
                    if run.italic:
                        formatting['italic'] = True
                
                # Convert paragraph to HTML-like structure with formatting
                text = paragraph.text
                # Replace placeholders with editable spans
                text = re.sub(placeholder_pattern, r'<span class="placeholder" data-placeholder="\1">{{{\1}}}</span>', text)
                
                content.append({
                    'type': 'paragraph',
                    'text': text,
                    'formatting': formatting,
                    'style': paragraph.style.name if paragraph.style else 'Normal'
                })
                
                # Extract placeholders
                placeholders = re.findall(placeholder_pattern, paragraph.text)
                all_placeholders.update(placeholders)
        
        # Process tables with structure preservation
        for table_index, table in enumerate(doc.tables):
            table_content = {
                'type': 'table',
                'index': table_index,
                'rows': [],
                'formatting': {
                    'style': 'Table Grid',
                    'alignment': 'left'
                }
            }
            
            for row_index, row in enumerate(table.rows):
                row_data = []
                for cell_index, cell in enumerate(row.cells):
                    cell_text = ''
                    cell_formatting = {
                        'bold': False,
                        'italic': False,
                        'font_size': None,
                        'font_name': None
                    }
                    
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            text = paragraph.text
                            # Replace placeholders with editable spans
                            text = re.sub(placeholder_pattern, r'<span class="placeholder" data-placeholder="\1">{{{\1}}}</span>', text)
                            cell_text += text + ' '
                            
                            # Extract formatting from runs
                            for run in paragraph.runs:
                                if run.font.size:
                                    cell_formatting['font_size'] = run.font.size.pt
                                if run.font.name:
                                    cell_formatting['font_name'] = run.font.name
                                if run.bold:
                                    cell_formatting['bold'] = True
                                if run.italic:
                                    cell_formatting['italic'] = True
                    
                    row_data.append({
                        'text': cell_text.strip(),
                        'formatting': cell_formatting,
                        'row': row_index,
                        'col': cell_index
                    })
                    
                    # Extract placeholders from cell text
                    placeholders = re.findall(placeholder_pattern, cell_text)
                    all_placeholders.update(placeholders)
                
                table_content['rows'].append(row_data)
            
            content.append(table_content)
        
        # Add template metadata
        template_info = {
            'filename': safe_name,
            'total_paragraphs': len([item for item in content if item['type'] == 'paragraph']),
            'total_tables': len([item for item in content if item['type'] == 'table']),
            'total_placeholders': len(all_placeholders),
            'page_count': len(doc.sections) if hasattr(doc, 'sections') else 1
        }
        
        return jsonify({
            'content': content,
            'placeholders': list(all_placeholders),
            'template_info': template_info
        })
    except Exception as e:
        return jsonify({'error': f'Failed to extract template content: {str(e)}'}), 500

@mvp.route('/templates/<template_name>/preview', methods=['POST'])
def generate_live_preview(template_name):
    """
    Generates a live preview of the filled template as PDF.
    Preserves original template formatting and styles.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(template_name)
    template_path = os.path.join(TEMPLATE_DIR, safe_name)
    
    logger.info(f"Attempting to generate preview for template: {safe_name}")
    logger.info(f"Template path: {template_path}")

    if not os.path.isfile(template_path):
        logger.error(f"Template not found at path: {template_path}")
        return jsonify({'error': 'Template not found'}), 404

    data = request.get_json()
    context = data.get('data', {}) if data else {}
    
    logger.info(f"Received context data: {context}")
    
    if not context:
        logger.warning("No data provided for preview")
        return jsonify({'error': 'No data provided for preview'}), 400

    try:
        # Create a styled PDF that mimics the template using only reportlab
        buffer = io.BytesIO()
        pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Create custom styles to match template
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        
        # Read the original template to understand structure
        from docx import Document
        doc_original = Document(template_path)
        
        # Process paragraphs with preserved formatting
        for paragraph in doc_original.paragraphs:
            if paragraph.text.strip():
                # Replace placeholders with actual values
                text = paragraph.text
                for key, value in context.items():
                    text = text.replace(f'{{{{{key}}}}}', str(value))
                
                if text.strip():
                    # Determine style based on paragraph properties
                    if paragraph.style and hasattr(paragraph.style, 'name') and paragraph.style.name and paragraph.style.name.startswith('Heading'):
                        p = Paragraph(text, title_style)
                    else:
                        p = Paragraph(text, normal_style)
                    story.append(p)
        
        # Process tables with preserved structure
        for table in doc_original.tables:
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = ''
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            text = paragraph.text
                            for key, value in context.items():
                                text = text.replace(f'{{{{{key}}}}}', str(value))
                            cell_text += text + ' '
                    row_data.append(cell_text.strip())
                table_data.append(row_data)
            
            if table_data:
                pdf_table = Table(table_data)
                pdf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(pdf_table)
                story.append(Spacer(1, 20))
        
        pdf_doc.build(story)
        buffer.seek(0)
        
        # Convert to base64 for frontend display
        pdf_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        logger.info("Successfully generated PDF preview using fallback method")
        
        return jsonify({
            'preview': f'data:application/pdf;base64,{pdf_base64}',
            'filename': f'preview_{uuid.uuid4().hex}.pdf'
        })
        
    except Exception as e:
        logger.error(f"Failed to generate preview: {str(e)}")
        return jsonify({'error': f'Failed to generate preview: {str(e)}'}), 500

@mvp.route('/templates/list', methods=['GET'])
def list_templates():
    files = []
    for fname in os.listdir(TEMPLATE_DIR):
        if fname.lower().endswith('.docx'):
            files.append({
                'id': fname,
                'name': os.path.splitext(fname)[0],
                'description': '',
                'filename': fname
            })
    return jsonify(files)

@mvp.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        current_app.logger.debug(f"Received data: {data}")
        
        template_filename = data.get('templateFilename')
        context = data.get('data', {})
        
        current_app.logger.debug(f"Template filename: {template_filename}")
        current_app.logger.debug(f"Context data: {context}")
        
        if not template_filename or not context:
            return jsonify({'error': 'Missing template filename or data'}), 400
        
        template_path = os.path.join(TEMPLATE_DIR, template_filename)
        current_app.logger.debug(f"Template path: {template_path}")
        
        if not os.path.isfile(template_path):
            return jsonify({'error': 'Template not found'}), 404
        
        # Generate unique output filename
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static/generated'))
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"report_{uuid.uuid4().hex}.docx"
        output_path = os.path.join(output_dir, output_filename)
        
        current_app.logger.debug(f"Output path: {output_path}")
        
        # Fill template using docxtpl
        from docxtpl import DocxTemplate
        current_app.logger.debug("Creating DocxTemplate instance")
        doc = DocxTemplate(template_path)
        
        # Transform flat context data to nested structure
        nested_context = {}
        for key, value in context.items():
            if '.' in key:
                parts = key.split('.')
                current = nested_context
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                nested_context[key] = value
        
        current_app.logger.debug(f"Nested context: {nested_context}")
        
        current_app.logger.debug("Rendering template with context")
        doc.render(nested_context)
        
        current_app.logger.debug("Saving rendered document")
        doc.save(output_path)
        
        # Create download URL
        download_url = f"/mvp/static/generated/{output_filename}"
        
        current_app.logger.debug(f"Report generated successfully: {download_url}")
        
        return jsonify({
            'downloadUrl': download_url,
            'message': f'Report generated successfully! File: {output_filename}',
            'filename': output_filename,
            'status': 'success'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating report: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Failed to generate report: {str(e)}',
            'status': 'error'
        }), 500

@mvp.route('/templates/<template_name>/download', methods=['GET'])
def download_template(template_name):
    """
    Download the original template file for verification.
    """
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(template_name)
    template_path = os.path.join(TEMPLATE_DIR, safe_name)

    if not os.path.isfile(template_path):
        return jsonify({'error': 'Template not found'}), 404

    try:
        return send_from_directory(
            TEMPLATE_DIR, 
            safe_name, 
            as_attachment=True,
            download_name=safe_name
        )
    except Exception as e:
        return jsonify({'error': f'Failed to download template: {str(e)}'}), 500 

@mvp.route('/static/generated/<filename>', methods=['GET'])
def serve_generated_file(filename):
    """
    Serve generated report files for download.
    """
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    generated_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static/generated'))
    file_path = os.path.join(generated_dir, safe_filename)
    
    if not os.path.isfile(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        return send_from_directory(
            generated_dir,
            safe_filename,
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        return jsonify({'error': f'Failed to serve file: {str(e)}'}), 500 