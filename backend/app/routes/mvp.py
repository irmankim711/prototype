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
        # For problematic templates, use manual replacement instead of docxtpl
        from docx import Document
        import tempfile
        import shutil
        
        # Copy the original template to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            shutil.copy2(template_path, tmp_file.name)
            tmp_path = tmp_file.name
        
        # Load the document and manually replace placeholders
        doc = Document(tmp_path)
        
        # Debug: print context data
        print(f"Preview context data: {context}")
        
        # Replace placeholders in paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text:
                original_text = paragraph.text
                for key, value in context.items():
                    original_text = original_text.replace(f'{{{{{key}}}}}', str(value))
                
                # If text changed, update the paragraph
                if original_text != paragraph.text:
                    # Clear the paragraph and add the new text
                    for run in paragraph.runs:
                        run.clear()
                    if paragraph.runs:
                        paragraph.runs[0].text = original_text
                    else:
                        paragraph.add_run(original_text)
        
        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text:
                            original_text = paragraph.text
                            for key, value in context.items():
                                original_text = original_text.replace(f'{{{{{key}}}}}', str(value))
                            
                            # If text changed, update the paragraph
                            if original_text != paragraph.text:
                                # Clear the paragraph and add the new text
                                for run in paragraph.runs:
                                    run.clear()
                                if paragraph.runs:
                                    paragraph.runs[0].text = original_text
                                else:
                                    paragraph.add_run(original_text)
        
        # Save the modified document
        doc.save(tmp_path)
        
        # Convert to PDF using python-docx2pdf or similar
        try:
            from docx2pdf import convert
            pdf_path = tmp_path.replace('.docx', '.pdf')
            convert(tmp_path, pdf_path)
            
            # Read PDF and convert to base64
            with open(pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Clean up temporary files
            os.unlink(tmp_path)
            os.unlink(pdf_path)
            
            return jsonify({
                'preview': f'data:application/pdf;base64,{pdf_base64}',
                'filename': f'preview_{uuid.uuid4().hex}.pdf'
            })
            
        except Exception as e:
            # Clean up temp file in case of error
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            # Log the conversion error and fall back to reportlab
            print(f"docx2pdf conversion failed: {e}")
            
            # Fallback: Create a styled PDF that mimics the template
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
            doc_original = Document(template_path)
            
            # Process paragraphs with preserved formatting
            for paragraph in doc_original.paragraphs:
                if paragraph.text.strip():
                    try:
                        # Replace placeholders with actual values
                        text = paragraph.text
                        for key, value in context.items():
                            text = text.replace(f'{{{{{key}}}}}', str(value))
                        
                        if text.strip():
                            # Escape special characters for reportlab
                            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            
                            # Determine style based on paragraph properties
                            if paragraph.style.name.startswith('Heading'):
                                p = Paragraph(text, title_style)
                            else:
                                p = Paragraph(text, normal_style)
                            story.append(p)
                    except Exception as e:
                        # Skip problematic paragraphs but continue processing
                        print(f"Error processing paragraph: {e}")
                        continue
            
            # Process tables with preserved structure
            for table in doc_original.tables:
                try:
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
                                    # Escape special characters
                                    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
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
                except Exception as e:
                    # Skip problematic tables but continue processing
                    print(f"Error processing table: {e}")
                    continue
            
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
    
    try:
        # Generate unique output filename
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static/generated'))
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"report_{uuid.uuid4().hex}.docx"
        output_path = os.path.join(output_dir, output_filename)
        
        # Fill template using docxtpl
        from docxtpl import DocxTemplate
        doc = DocxTemplate(template_path)
        doc.render(context)
        doc.save(output_path)
        
        # Create download URL
        download_url = f"/mvp/static/generated/{output_filename}"
        
        return jsonify({
            'downloadUrl': download_url,
            'message': f'Report generated successfully! File: {output_filename}',
            'filename': output_filename,
            'status': 'success'
        })
        
    except Exception as e:
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