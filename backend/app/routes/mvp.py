from flask import Blueprint, jsonify, request, send_from_directory
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

mvp = Blueprint('mvp', __name__)

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

@mvp.route('/ai/analyze', methods=['POST'])
def ai_analyze():
    """
    Mock AI analysis endpoint to prevent frontend errors while testing.
    """
    try:
        data = request.get_json()
        return jsonify({
            'summary': 'Data analysis completed successfully.',
            'insights': ['Analysis placeholder'],
            'suggestions': 'Consider reviewing your data.'
        })
    except Exception as e:
        return jsonify({
            'summary': 'Analysis completed with warnings.',
            'insights': ['Mock analysis result'],
            'suggestions': 'Data appears to be valid.'
        })

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
    Returns HTML-like structure that can be edited in the browser.
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
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                # Convert paragraph to HTML-like structure
                text = paragraph.text
                # Replace placeholders with editable spans
                text = re.sub(placeholder_pattern, r'<span class="placeholder" data-placeholder="\1">{{{\1}}}</span>', text)
                content.append({
                    'type': 'paragraph',
                    'text': text,
                    'style': paragraph.style.name if paragraph.style else 'Normal'
                })
                # Extract placeholders
                placeholders = re.findall(placeholder_pattern, paragraph.text)
                all_placeholders.update(placeholders)
        
        # Also process table content
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            text = paragraph.text
                            text = re.sub(placeholder_pattern, r'<span class="placeholder" data-placeholder="\1">{{{\1}}}</span>', text)
                            content.append({
                                'type': 'table_cell',
                                'text': text,
                                'style': paragraph.style.name if paragraph.style else 'Normal'
                            })
                            placeholders = re.findall(placeholder_pattern, paragraph.text)
                            all_placeholders.update(placeholders)
        
        return jsonify({
            'content': content,
            'placeholders': list(all_placeholders)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to extract template content: {str(e)}'}), 500

@mvp.route('/templates/<template_name>/preview', methods=['POST'])
def generate_live_preview(template_name):
    """
    Generates a live preview of the filled template as PDF.
    Accepts template data and returns a base64-encoded PDF preview.
    """
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(template_name)
    template_path = os.path.join(TEMPLATE_DIR, safe_name)

    if not os.path.isfile(template_path):
        return jsonify({'error': 'Template not found'}), 404

    data = request.get_json()
    context = data.get('data', {})
    
    if not context:
        return jsonify({'error': 'No data provided for preview'}), 400

    try:
        # Create a simple PDF preview without using docxtpl
        buffer = io.BytesIO()
        
        # Create a simple PDF preview
        pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Read the Word document and extract text
        doc = Document(template_path)
        
        # Extract text from document
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                # Replace placeholders with actual values
                text = paragraph.text
                for key, value in context.items():
                    text = text.replace(f'{{{{{key}}}}}', str(value))
                
                if text.strip():
                    p = Paragraph(text, styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 12))
        
        # Also process table content
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            text = paragraph.text
                            for key, value in context.items():
                                text = text.replace(f'{{{{{key}}}}}', str(value))
                            
                            if text.strip():
                                p = Paragraph(text, styles['Normal'])
                                story.append(p)
                                story.append(Spacer(1, 6))
        
        pdf_doc.build(story)
        buffer.seek(0)
        
        # Convert to base64 for frontend display
        pdf_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'preview': f'data:application/pdf;base64,{pdf_base64}',
            'filename': f'preview_{uuid.uuid4().hex}.pdf'
        })
        
    except Exception as e:
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
    data = request.get_json()
    template_filename = data.get('templateFilename')
    context = data.get('data', {})
    if not template_filename or not context:
        return jsonify({'error': 'Missing template filename or data'}), 400
    template_path = os.path.join(TEMPLATE_DIR, template_filename)
    if not os.path.isfile(template_path):
        return jsonify({'error': 'Template not found'}), 404
    # Generate unique output filename
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static/generated'))
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"report_{uuid.uuid4().hex}.docx"
    output_path = os.path.join(output_dir, output_filename)
    # Fill template
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(output_path)
    download_url = f"/static/generated/{output_filename}"
    return jsonify({'downloadUrl': download_url}) 