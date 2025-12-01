"""
DOCX Preview Service
Converts DOCX files to HTML for in-browser preview
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from docx import Document
from docx.shared import Inches
import base64
from io import BytesIO
import zipfile
import xml.etree.ElementTree as ET
import convertapi

logger = logging.getLogger(__name__)

class DocxPreviewService:
    """Service for converting DOCX files to HTML for browser preview"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'static', 'previews')
        self.ensure_directories()
        
        # Configure ConvertAPI
        # Try to get from env, otherwise use provided key
        self.convert_api_secret = os.environ.get('CONVERT_API_SECRET', 'rd78ghGq31u8k5zm2hY22ACRtnkqje8g')
        convertapi.api_secret = self.convert_api_secret
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def convert_docx_to_html_convertapi(self, docx_path: str, output_filename: str = None) -> Tuple[str, str]:
        """
        Convert DOCX to HTML using ConvertAPI for high fidelity
        
        Args:
            docx_path: Path to DOCX file
            output_filename: Optional output filename
            
        Returns:
            Tuple of (html_file_path, html_content)
        """
        try:
            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"DOCX file not found: {docx_path}")
                
            logger.info(f"Converting DOCX to HTML using ConvertAPI: {docx_path}")
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = Path(docx_path).stem
                output_filename = f"{base_name}_preview_hq.html"
            
            html_file_path = os.path.join(self.output_dir, output_filename)
            
            # Use ConvertAPI to convert
            result = convertapi.convert('html', {
                'File': docx_path,
                'Responsive': 'true',
                'EmbedImages': 'true',
                'EmbedFonts': 'true'
            }, from_format='docx')
            
            # Save the result
            result.save_files(self.output_dir)
            
            # ConvertAPI might save with a different name, so we need to find it
            # Or we can read the content directly from the result
            # The save_files method saves to the directory. Let's try to save to specific file if possible
            # But simpler is to just read the content and write it ourselves to control the filename
            
            # Get the content from the first file in result
            # ConvertAPI returns a list of files (usually just one for HTML unless split)
            # For HTML conversion, it might produce multiple files if images aren't embedded, 
            # but we requested EmbedImages=true
            
            # Let's save it to our target path
            result.file.save(html_file_path)
            
            # Read the content
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            logger.info(f"Successfully converted DOCX to HTML via ConvertAPI: {html_file_path}")
            return html_file_path, html_content
            
        except Exception as e:
            logger.error(f"ConvertAPI conversion failed: {str(e)}")
            logger.info("Falling back to local conversion...")
            return self.convert_docx_to_html(docx_path, output_filename)

    def convert_html_to_docx_convertapi(self, html_content: str, output_docx_path: str) -> str:
        """
        Convert HTML content back to DOCX using ConvertAPI
        
        Args:
            html_content: HTML string to convert
            output_docx_path: Path to save the resulting DOCX
            
        Returns:
            Path to the saved DOCX file
        """
        try:
            logger.info(f"Converting HTML to DOCX using ConvertAPI")
            
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
                
            try:
                # Use ConvertAPI to convert
                result = convertapi.convert('docx', {
                    'File': temp_html_path,
                    'PageSize': 'a4',
                    'MarginTop': '20',
                    'MarginBottom': '20',
                    'MarginLeft': '20',
                    'MarginRight': '20'
                }, from_format='html')
                
                # Save the result
                result.file.save(output_docx_path)
                
                logger.info(f"Successfully converted HTML to DOCX: {output_docx_path}")
                return output_docx_path
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
                    
        except Exception as e:
            logger.error(f"ConvertAPI HTML->DOCX conversion failed: {str(e)}")
            raise

    def convert_docx_to_html(self, docx_path: str, output_filename: str = None) -> Tuple[str, str]:
        """
        Convert DOCX to HTML for browser preview
        
        Args:
            docx_path: Path to DOCX file
            output_filename: Optional output filename
            
        Returns:
            Tuple of (html_file_path, html_content)
        """
        try:
            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"DOCX file not found: {docx_path}")
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = Path(docx_path).stem
                output_filename = f"{base_name}_preview.html"
            
            html_file_path = os.path.join(self.output_dir, output_filename)
            
            # Open and parse the DOCX document
            doc = Document(docx_path)
            
            # Extract images from the DOCX file
            images = self._extract_images_from_docx(docx_path)
            
            # Convert to HTML
            html_content = self._convert_document_to_html(doc, images)
            
            # Save HTML file
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Successfully converted DOCX to HTML: {html_file_path}")
            return html_file_path, html_content
            
        except Exception as e:
            logger.error(f"DOCX to HTML conversion failed: {str(e)}")
            raise
    
    def _extract_images_from_docx(self, docx_path: str) -> Dict[str, str]:
        """Extract images from DOCX file and convert to base64"""
        images = {}
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # Find all image files in the DOCX
                image_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]
                
                for image_file in image_files:
                    # Read image data
                    image_data = docx_zip.read(image_file)
                    
                    # Determine image format
                    image_ext = Path(image_file).suffix.lower()
                    if image_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                        # Convert to base64
                        image_b64 = base64.b64encode(image_data).decode('utf-8')
                        mime_type = f"image/{image_ext[1:].replace('jpg', 'jpeg')}"
                        
                        # Store with filename as key
                        image_name = Path(image_file).name
                        images[image_name] = f"data:{mime_type};base64,{image_b64}"
        
        except Exception as e:
            logger.warning(f"Failed to extract images from DOCX: {e}")
        
        return images
    
    def _convert_document_to_html(self, doc: Document, images: Dict[str, str]) -> str:
        """Convert python-docx Document to HTML"""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>Document Preview</title>',
            '<style>',
            self._get_preview_styles(),
            '</style>',
            '</head>',
            '<body>',
            '<div class="docx-preview-container">',
        ]
        
        # Process document elements in order
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        
        # Process document elements recursively to handle nested structures (sdt, text boxes, etc.)
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        
        try:
            # 1. Extract Headers
            for section in doc.sections:
                if section.header:
                    html_parts.append('<div class="docx-header">')
                    html_parts.extend(self._process_element_recursive(section.header._element, doc, images))
                    html_parts.append('</div><hr class="header-separator">')
                    # Only process first section's header for now to avoid duplicates in a single-page preview
                    break 

            # 2. Extract Body Content
            html_parts.extend(self._process_element_recursive(doc.element.body, doc, images))
            
            # 3. Extract Footers
            for section in doc.sections:
                if section.footer:
                    html_parts.append('<hr class="footer-separator"><div class="docx-footer">')
                    html_parts.extend(self._process_element_recursive(section.footer._element, doc, images))
                    html_parts.append('</div>')
                    break

        except Exception as e:
            logger.warning(f"Recursive parsing failed: {e}. Falling back to legacy method.")
            # Fallback to legacy method
            for paragraph in doc.paragraphs:
                html_parts.append(self._convert_paragraph_to_html(paragraph, images))
            for table in doc.tables:
                html_parts.append(self._convert_table_to_html(table, images))
        
        # FINAL SAFETY NET: If content is still very short (likely just headers/footers or empty),
        # try to extract raw text from the entire XML tree.
        current_content_length = len(''.join(html_parts))
        if current_content_length < 500: # Arbitrary threshold
            logger.warning("Content seems empty after structured parsing. Attempting raw text extraction.")
            html_parts.append('<div class="raw-text-fallback" style="color: red; margin-top: 20px; border-top: 1px solid red; padding-top: 10px;">')
            html_parts.append('<p><em><strong>Note:</strong> Structured formatting could not be fully preserved. Showing raw text content below:</em></p>')
            
            try:
                # Iterate over all 't' (text) elements in the document body
                body_xml = doc.element.body
                raw_paragraphs = []
                current_para = []
                
                # Simple iteration over all text nodes
                for t in body_xml.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    if t.text:
                        current_para.append(self._escape_html(t.text))
                        # If text ends with newline or is long, break (heuristic)
                        if len(current_para) > 20: 
                            raw_paragraphs.append('<p>' + ''.join(current_para) + '</p>')
                            current_para = []
                
                if current_para:
                    raw_paragraphs.append('<p>' + ''.join(current_para) + '</p>')
                    
                html_parts.extend(raw_paragraphs)
            except Exception as raw_e:
                logger.error(f"Raw text extraction failed: {raw_e}")
            
            html_parts.append('</div>')

        html_parts.extend([
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)

    def _process_element_recursive(self, element, doc, images, depth=0):
        """Recursively process XML elements to extract content"""
        html_parts = []
        
        # Safety limit for recursion
        if depth > 50:
            return html_parts
            
        # Import wrappers here to avoid circular imports or scope issues
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        
        try:
            # Check if the current element is a paragraph or table
            tag = element.tag
            
            if tag.endswith('}p'): # Paragraph
                paragraph = Paragraph(element, doc)
                html_parts.append(self._convert_paragraph_to_html(paragraph, images))
                return html_parts
                
            if tag.endswith('}tbl'): # Table
                table = Table(element, doc)
                html_parts.append(self._convert_table_to_html(table, images))
                return html_parts
            
            # If not a leaf node (p or tbl), recurse into children
            # This handles body, sdt, sdtContent, txbxContent, smartTag, ins, etc. automatically
            for child in element.iterchildren():
                html_parts.extend(self._process_element_recursive(child, doc, images, depth + 1))
                    
        except Exception as e:
            logger.warning(f"Error processing element {element.tag}: {e}")
            
        return html_parts
    
    def _convert_paragraph_to_html(self, paragraph, images: Dict[str, str] = None) -> str:
        """Convert a paragraph to HTML, handling runs and hyperlinks manually"""
        if images is None:
            images = {}
            
        # Determine paragraph style
        style_class = 'paragraph'
        if paragraph.style.name.startswith('Heading'):
            level = paragraph.style.name.replace('Heading ', '')
            if level.isdigit() and 1 <= int(level) <= 6:
                # For headings, we can usually trust paragraph.text, but let's be safe
                return f'<h{level} class="heading-{level}">{self._escape_html(paragraph.text)}</h{level}>'
        
        # Handle different paragraph styles
        if 'Title' in paragraph.style.name:
            style_class = 'title'
        elif 'Subtitle' in paragraph.style.name:
            style_class = 'subtitle'
            
        # Determine alignment
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        align_style = ''
        if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            align_style = 'text-align: center;'
        elif paragraph.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
            align_style = 'text-align: right;'
        elif paragraph.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
            align_style = 'text-align: justify;'
        
        # Process content by iterating over XML children to catch hyperlinks and fields
        html_content = ''
        
        # Helper to process a run element
        def process_run_element(run_element):
            text_content = ''
            # Extract text from t tags
            for t in run_element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if t.text:
                    text_content += self._escape_html(t.text)
            
            # Apply formatting based on rPr
            rPr = run_element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
            if rPr is not None:
                if rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}b') is not None:
                    text_content = f'<strong>{text_content}</strong>'
                if rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}i') is not None:
                    text_content = f'<em>{text_content}</em>'
                if rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}u') is not None:
                    text_content = f'<u>{text_content}</u>'
            
            # Handle images
            img_html = ''
            try:
                drawings = run_element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
                for drawing in drawings:
                    blips = drawing.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                    for blip in blips:
                        embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        if embed_id and embed_id in paragraph.part.rels:
                            image_part = paragraph.part.rels[embed_id].target_part
                            image_name = os.path.basename(image_part.partname)
                            if image_name in images:
                                img_src = images[image_name]
                                img_html += f'<br><img src="{img_src}" style="max-width: 100%; height: auto; margin: 10px 0;" /><br>'
            except Exception as e:
                pass
                
            return text_content + img_html

        # Iterate over children
        for child in paragraph._element.iterchildren():
            tag = child.tag
            if tag.endswith('}r'): # Run
                html_content += process_run_element(child)
            elif tag.endswith('}hyperlink'): # Hyperlink
                # Hyperlinks contain runs
                for sub_child in child.iterchildren():
                    if sub_child.tag.endswith('}r'):
                        html_content += process_run_element(sub_child)
            elif tag.endswith('}fldSimple'): # Simple Field
                # Fields might contain runs
                for sub_child in child.iterchildren():
                    if sub_child.tag.endswith('}r'):
                        html_content += process_run_element(sub_child)
        
        # Fallback: if manual parsing yielded nothing but paragraph.text exists, use that
        if not html_content and paragraph.text.strip():
            html_content = self._escape_html(paragraph.text)
            
        if not html_content:
            return '<br>'
        
        return f'<p class="{style_class}" style="{align_style}">{html_content}</p>'
    
    def _convert_table_to_html(self, table, images: Dict[str, str] = None) -> str:
        """Convert a table to HTML"""
        html_parts = ['<table class="docx-table">']
        
        for i, row in enumerate(table.rows):
            html_parts.append('<tr>')
            
            for cell in row.cells:
                tag = 'td' # Default to td, let styles handle headers if needed
                
                # Convert cell content (paragraphs)
                cell_content = []
                for paragraph in cell.paragraphs:
                    # Skip empty paragraphs in cells to avoid excessive whitespace, 
                    # unless it's the only thing in the cell
                    if paragraph.text.strip() or len(cell.paragraphs) == 1:
                        cell_content.append(self._convert_paragraph_to_html(paragraph, images))
                
                cell_html = ''.join(cell_content) if cell_content else '&nbsp;'
                html_parts.append(f'<{tag} class="table-cell">{cell_html}</{tag}>')
            
            html_parts.append('</tr>')
        
        html_parts.append('</table>')
        return '\n'.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _get_preview_styles(self) -> str:
        """Get CSS styles for the preview"""
        return """
            body {
                font-family: 'Times New Roman', Times, serif;
                line-height: 1.5;
                color: #000;
                background-color: #525659;
                margin: 0;
                padding: 20px;
            }
            
            .docx-preview-container {
                width: 210mm;
                min-height: 297mm;
                margin: 0 auto;
                background: white;
                padding: 25mm 25mm;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
                box-sizing: border-box;
            }
            
            .title {
                font-size: 24pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 12pt;
                color: #000;
            }
            
            .subtitle {
                font-size: 18pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 12pt;
                color: #444;
            }
            
            .heading-1 {
                font-size: 16pt;
                font-weight: bold;
                color: #2c3e50;
                margin-top: 18pt;
                margin-bottom: 12pt;
            }
            
            .heading-2 {
                font-size: 14pt;
                font-weight: bold;
                color: #34495e;
                margin-top: 14pt;
                margin-bottom: 10pt;
            }
            
            .heading-3 {
                font-size: 12pt;
                font-weight: bold;
                color: #34495e;
                margin-top: 12pt;
                margin-bottom: 6pt;
            }
            
            .paragraph {
                margin-bottom: 10pt;
                font-size: 11pt;
            }
            
            .docx-table {
                width: 100%;
                border-collapse: collapse;
                margin: 12pt 0;
                border: 1px solid black;
            }
            
            .table-cell {
                border: 1px solid black;
                padding: 5pt;
                vertical-align: top;
            }
            
            strong { font-weight: bold; }
            em { font-style: italic; }
            
            @media print {
                body {
                    background: white;
                    padding: 0;
                }
                
                .docx-preview-container {
                    box-shadow: none;
                    padding: 0;
                    margin: 0;
                    width: 100%;
                }
            }
            
            @media (max-width: 800px) {
                .docx-preview-container {
                    width: 100%;
                    padding: 15px;
                }
            }

            
            @media print {
                body {
                    background: white;
                    padding: 0;
                }
                
                .docx-preview-container {
                    box-shadow: none;
                    padding: 20px;
                }
            }
            
            @media (max-width: 768px) {
                .docx-preview-container {
                    padding: 20px;
                    margin: 10px;
                }
                
                .title {
                    font-size: 1.5em;
                }
                
                .docx-table {
                    font-size: 0.9em;
                }
                
                .table-cell {
                    padding: 8px;
                }
            }
        """
    
    def get_preview_url(self, docx_path: str) -> str:
        """
        Get URL for previewing a DOCX file
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            URL for preview
        """
        try:
            # Convert to HTML using ConvertAPI for high fidelity
            html_file_path, _ = self.convert_docx_to_html_convertapi(docx_path)
            
            # Return relative URL
            filename = Path(html_file_path).name
            return f'/static/previews/{filename}'
            
        except Exception as e:
            logger.error(f"Failed to get preview URL: {str(e)}")
            raise
    
    def cleanup_old_previews(self, max_age_hours: int = 24):
        """Clean up old preview files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in Path(self.output_dir).glob('*.html'):
                if current_time - file_path.stat().st_mtime > max_age_seconds:
                    file_path.unlink()
                    logger.info(f"Cleaned up old preview: {file_path}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup previews: {str(e)}")

# Global service instance
docx_preview_service = DocxPreviewService()