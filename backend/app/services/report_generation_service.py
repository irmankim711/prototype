"""
Enhanced Report Generation Service
Handles generation of PDF, DOCX, and Excel reports with production-ready features
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Report generation libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd

from .. import db
from ..models import Report, Form, FormSubmission, User
from ..core.exceptions import ReportGenerationError
from .latex_conversion_service import latex_conversion_service
from .data_fetcher import data_fetcher
from .template_data_mapper import template_data_mapper

try:
    from .chart_generator_service import chart_generator_service
    CHARTS_AVAILABLE = True
except ImportError:
    chart_generator_service = None
    CHARTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ReportGenerationService:
    """Service for generating various types of reports"""
    
    def __init__(self, upload_folder: str = None):
        self.upload_folder = upload_folder or os.path.join(os.getcwd(), 'uploads', 'reports')
        self.static_dir = os.path.join(os.getcwd(), 'static', 'generated')
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """Ensure the upload directory exists"""
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)
        Path(self.static_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_timestamp_filename(self, prefix: str, extension: str) -> str:
        """Generate a unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"
    
    def generate_pdf_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, int]:
        """
        Generate a PDF report using reportlab
        
        Args:
            data: Data to include in the report
            config: Report configuration (title, style, etc.)
            
        Returns:
            Tuple of (file_path, file_size)
        """
        try:
            filename = self.generate_timestamp_filename("report", "pdf")
            file_path = os.path.join(self.upload_folder, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            story = []
            
            # Get styles - use default without custom colors
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Add title
            title = Paragraph(config.get('title', 'Generated Report'), title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Add generation info
            info_style = styles['Normal']
            generation_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(generation_info, info_style))
            story.append(Spacer(1, 20))
            
            # Add data content
            if isinstance(data, dict):
                story.extend(self._add_dict_to_pdf(data, styles))
            elif isinstance(data, list):
                story.extend(self._add_list_to_pdf(data, styles))
            else:
                story.append(Paragraph(str(data), info_style))
            
            # Build PDF
            doc.build(story)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            logger.info(f"PDF report generated successfully: {file_path} ({file_size} bytes)")
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate PDF report: {str(e)}")
    
    def _add_dict_to_pdf(self, data: Dict[str, Any], styles) -> List:
        """Add dictionary data to PDF story"""
        story = []
        normal_style = styles['Normal']
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                # Add key as subheading
                subheading = Paragraph(f"<b>{key}:</b>", normal_style)
                story.append(subheading)
                story.append(Spacer(1, 10))
                
                if isinstance(value, dict):
                    story.extend(self._add_dict_to_pdf(value, styles))
                else:
                    story.extend(self._add_list_to_pdf(value, styles))
            else:
                # Simple key-value pair
                content = f"<b>{key}:</b> {str(value)}"
                story.append(Paragraph(content, normal_style))
                story.append(Spacer(1, 5))
        
        return story
    
    def _add_list_to_pdf(self, data: List[Any], styles) -> List:
        """Add list data to PDF story"""
        story = []
        normal_style = styles['Normal']
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                story.append(Paragraph(f"<b>Item {i+1}:</b>", normal_style))
                story.append(Spacer(1, 5))
                story.extend(self._add_dict_to_pdf(item, styles))
            else:
                story.append(Paragraph(f"• {str(item)}", normal_style))
                story.append(Spacer(1, 3))
        
        return story
    
    def generate_docx_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, int]:
        """
        Generate a DOCX report using python-docx
        
        Args:
            data: Data to include in the report
            config: Report configuration (title, style, etc.)
            
        Returns:
            Tuple of (file_path, file_size)
        """
        try:
            filename = self.generate_timestamp_filename("report", "docx")
            file_path = os.path.join(self.upload_folder, filename)
            
            # Create document
            doc = Document()
            
            # Add title
            title = doc.add_heading(config.get('title', 'Generated Report'), 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add generation info
            doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            doc.add_paragraph()
            
            # Add data content
            if isinstance(data, dict):
                self._add_dict_to_docx(doc, data)
            elif isinstance(data, list):
                self._add_list_to_docx(doc, data)
            else:
                doc.add_paragraph(str(data))
            
            # Save document
            doc.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            logger.info(f"DOCX report generated successfully: {file_path} ({file_size} bytes)")
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error generating DOCX report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate DOCX report: {str(e)}")
    
    def _add_dict_to_docx(self, doc: Document, data: Dict[str, Any]):
        """Add dictionary data to DOCX document"""
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                # Add key as subheading
                doc.add_heading(key, level=2)
                
                if isinstance(value, dict):
                    self._add_dict_to_docx(doc, value)
                else:
                    self._add_list_to_docx(doc, value)
            else:
                # Simple key-value pair
                p = doc.add_paragraph()
                p.add_run(f"{key}: ").bold = True
                p.add_run(str(value))
    
    def _add_list_to_docx(self, doc: Document, data: List[Any]):
        """Add list data to DOCX document"""
        for i, item in enumerate(data):
            if isinstance(item, dict):
                doc.add_heading(f"Item {i+1}", level=3)
                self._add_dict_to_docx(doc, item)
            else:
                doc.add_paragraph(f"• {str(item)}", style='List Bullet')
    
    def generate_excel_report(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[str, int]:
        """
        Generate an Excel report using openpyxl
        
        Args:
            data: List of dictionaries representing rows
            config: Report configuration (sheet name, headers, etc.)
            
        Returns:
            Tuple of (file_path, file_size)
        """
        try:
            filename = self.generate_timestamp_filename("report", "xlsx")
            file_path = os.path.join(self.upload_folder, filename)
            
            # Create workbook and worksheet
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = config.get('sheet_name', 'Report Data')
            
            if not data:
                # Empty report
                ws['A1'] = "No data available"
                wb.save(file_path)
                file_size = os.path.getsize(file_path)
                return file_path, file_size
            
            # Get headers from first row
            headers = list(data[0].keys())
            
            # Style for headers - minimal styling without colors
            header_font = Font(bold=True)
            header_alignment = Alignment(horizontal="center", vertical="center")

            # Add headers
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.alignment = header_alignment
            
            # Add data rows
            for row_idx, row_data in enumerate(data, 2):
                for col_idx, header in enumerate(headers, 1):
                    value = row_data.get(header, '')
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Add borders
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            for row in ws.iter_rows(min_row=1, max_row=len(data)+1, min_col=1, max_col=len(headers)):
                for cell in row:
                    cell.border = thin_border
            
            # Save workbook
            wb.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            logger.info(f"Excel report generated successfully: {file_path} ({file_size} bytes)")
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate Excel report: {str(e)}")
    
    def generate_latex_based_report(self, report_id: int, latex_file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a report from LaTeX template with automatic conversion to PDF and DOCX

        Args:
            report_id: ID of the report record
            latex_file_path: Path to the LaTeX file
            config: Report configuration

        Returns:
            Dictionary with file paths and metadata
        """
        try:
            # Update report status to generating
            report = Report.query.get(report_id)
            if not report:
                raise ReportGenerationError(f"Report {report_id} not found")

            report.update_status('generating', progress=10)
            db.session.commit()

            # Generate base filename
            base_filename = Path(latex_file_path).stem

            # Fetch real data if data sources are configured
            real_data_result = self.fetch_real_data(config)
            if real_data_result.get('success'):
                raw_data = {
                    'records': real_data_result.get('data', []),
                    'metadata': real_data_result.get('metadata', {}),
                    'summary': real_data_result.get('metadata', {}).get('summary', {}),
                    'submissions': real_data_result.get('data', [])  # For backward compatibility
                }
                logger.info(f"Using real data: {len(raw_data['records'])} records")
            else:
                # Fallback to provided data
                raw_data = config.get('data', {})
                logger.warning(f"Using fallback data due to fetch error: {real_data_result.get('error')}")

            # Map data to template format
            template_name = os.path.basename(latex_file_path)
            mapped_data = template_data_mapper.map_data_for_template(raw_data, template_name)
            logger.info(f"Data mapped for template {template_name}")

            # Read template content and populate with data
            populated_latex_path = self._populate_latex_template(latex_file_path, mapped_data)
            report.update_status('generating', progress=30)
            db.session.commit()
            
            # Convert LaTeX to PDF
            logger.info(f"Converting LaTeX to PDF for report {report_id}")
            pdf_filename = f"{base_filename}.pdf"
            pdf_path, pdf_size = latex_conversion_service.convert_latex_to_pdf(
                populated_latex_path, pdf_filename
            )
            report.update_status('generating', progress=50)
            db.session.commit()
            
            # Convert LaTeX to DOCX
            logger.info(f"Converting LaTeX to DOCX for report {report_id}")
            docx_filename = f"{base_filename}.docx"
            docx_path, docx_size = latex_conversion_service.convert_latex_to_docx(
                populated_latex_path, docx_filename
            )
            report.update_status('generating', progress=80)
            db.session.commit()
            
            # Generate Excel report from data if available
            excel_path = None
            excel_size = None
            if config.get('include_excel', True) and raw_data:
                try:
                    excel_filename = f"{base_filename}.xlsx"
                    excel_path, excel_size = self.generate_excel_report(
                        raw_data.get('records', raw_data.get('submissions', [])),
                        config.get('excel_config', {})
                    )
                    # Rename to match base filename
                    if excel_path:
                        new_excel_path = os.path.join(self.static_dir, excel_filename)
                        if os.path.exists(excel_path):
                            os.rename(excel_path, new_excel_path)
                            excel_path = new_excel_path
                except Exception as e:
                    logger.warning(f"Excel generation failed for report {report_id}: {str(e)}")
            
            report.update_status('generating')
            db.session.commit()

            # Update report with file information (using actual database fields)
            report.file_path = pdf_path
            report.file_size = pdf_size
            report.file_format = 'pdf'

            # Generate download URLs
            base_url = config.get('base_url', 'http://localhost:5000')
            report.download_url = f"{base_url}/api/reports/{report_id}/download/pdf"

            # Mark as completed
            report.update_status('completed')
            report.data_source = config.get('data', {})
            report.generation_config = config
            db.session.commit()

            logger.info(f"✅ LaTeX report files saved: PDF={pdf_path}, DOCX={docx_path}, Excel={excel_path}")
            
            logger.info(f"LaTeX-based report {report_id} generated successfully")
            
            return {
                'report_id': report_id,
                'status': 'completed',
                'latex_source': latex_file_path,
                'pdf_file_path': pdf_path,
                'docx_file_path': docx_path,
                'excel_file_path': excel_path,
                'pdf_download_url': report.pdf_download_url,
                'docx_download_url': report.docx_download_url,
                'excel_download_url': report.excel_download_url,
                'file_sizes': {
                    'pdf': pdf_size,
                    'docx': docx_size,
                    'excel': excel_size
                }
            }
            
        except Exception as e:
            # Update report status to failed
            report = Report.query.get(report_id)
            if report:
                report.update_status('failed', error_message=str(e))
                db.session.commit()
            
            logger.error(f"Error generating LaTeX-based report {report_id}: {str(e)}")
            raise ReportGenerationError(f"Failed to generate LaTeX-based report: {str(e)}")

    def fetch_real_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch real data based on configuration

        Args:
            config: Report configuration with data source specifications

        Returns:
            Dictionary with fetched data and metadata
        """
        try:
            # Check for data source configuration
            data_sources = config.get('data_sources', [])
            if not data_sources:
                # Fallback to legacy data format
                return {
                    'success': True,
                    'data': config.get('data', {}),
                    'metadata': {'source': 'legacy_config'}
                }

            all_data = []
            all_metadata = {}

            # Fetch data from each configured source
            for i, source_config in enumerate(data_sources):
                logger.info(f"Fetching data from source {i + 1}: {source_config.get('type', 'unknown')}")

                result = data_fetcher.fetch_data_by_source_type(source_config)

                if result.get('success'):
                    source_data = result.get('data', [])
                    all_data.extend(source_data)
                    all_metadata[f'source_{i + 1}'] = result.get('metadata', {})
                    logger.info(f"Successfully fetched {len(source_data)} records from source {i + 1}")
                else:
                    logger.error(f"Failed to fetch data from source {i + 1}: {result.get('error')}")
                    all_metadata[f'source_{i + 1}_error'] = result.get('error')

            # Generate data summary
            summary = data_fetcher.get_data_summary(all_data)

            return {
                'success': True,
                'data': all_data,
                'metadata': {
                    'sources': all_metadata,
                    'summary': summary,
                    'total_records': len(all_data),
                    'fetched_at': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error fetching real data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'metadata': {'config': config}
            }

    def generate_comprehensive_report(self, report_id: int, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive report with all formats (PDF, DOCX, Excel)
        Now includes real data fetching and LaTeX conversion

        Args:
            report_id: ID of the report record
            data: Data to include in the report (can be legacy format)
            config: Report configuration

        Returns:
            Dictionary with file paths and metadata
        """
        try:
            logger.info(f"=== Starting comprehensive report generation {report_id} ===")
            logger.info(f"Input data type: {type(data)}, config keys: {list(config.keys())}")

            # Log data structure for debugging
            if isinstance(data, dict):
                logger.info(f"Data keys: {list(data.keys())[:10]}")
                if 'records' in data:
                    logger.info(f"Data contains {len(data.get('records', []))} records")
                if 'submissions' in data:
                    logger.info(f"Data contains {len(data.get('submissions', []))} submissions")

            # Check if this is a LaTeX-based report
            latex_source = config.get('latex_source') or config.get('latex_file_path')

            if latex_source and os.path.exists(latex_source):
                logger.info(f"Generating LaTeX-based comprehensive report {report_id} from {latex_source}")
                return self.generate_latex_based_report(report_id, latex_source, config)

            # Update report status to generating
            report = Report.query.get(report_id)
            if not report:
                raise ReportGenerationError(f"Report {report_id} not found")

            report.update_status('generating', progress=5)
            db.session.commit()

            # Fetch real data if data sources are configured
            real_data_result = self.fetch_real_data(config)
            if real_data_result.get('success'):
                # Use real data
                report_data = {
                    'records': real_data_result.get('data', []),
                    'metadata': real_data_result.get('metadata', {}),
                    'summary': real_data_result.get('metadata', {}).get('summary', {}),
                    'submissions': real_data_result.get('data', [])  # For backward compatibility
                }
                logger.info(f"✓ Using real data: {len(report_data['records'])} records")
            else:
                # Fallback to provided data
                report_data = data
                logger.warning(f"⚠ Using fallback data due to fetch error: {real_data_result.get('error')}")
                # Ensure data has proper structure
                if not isinstance(report_data, dict):
                    report_data = {'records': [], 'submissions': []}
                if 'records' not in report_data and 'submissions' not in report_data:
                    logger.warning("⚠ Data missing 'records' and 'submissions' keys!")
                    report_data['records'] = []

            report.update_status('generating', progress=20)
            db.session.commit()

            # Generate Excel report first (usually fastest)
            logger.info("Generating Excel report...")
            excel_path, excel_size = self.generate_excel_report(
                report_data.get('records', report_data.get('submissions', [])),
                config.get('excel_config', {})
            )
            logger.info(f"✓ Excel generated: {excel_path} ({excel_size} bytes)")
            report.update_status('generating', progress=50)
            db.session.commit()

            # Generate PDF report with enhanced data
            logger.info("Generating PDF report...")
            pdf_path, pdf_size = self.generate_enhanced_pdf_report(report_data, config)
            logger.info(f"✓ PDF generated: {pdf_path} ({pdf_size} bytes)")
            report.update_status('generating', progress=75)
            db.session.commit()

            # Generate DOCX report with enhanced data
            logger.info("Generating DOCX report...")
            docx_path, docx_size = self.generate_enhanced_docx_report(report_data, config)
            logger.info(f"✓ DOCX generated: {docx_path} ({docx_size} bytes)")
            report.update_status('generating', progress=90)
            db.session.commit()

            # Update report with file information (using actual database fields)
            # Store the primary file path (PDF) and file format
            report.file_path = pdf_path
            report.file_size = pdf_size
            report.file_format = 'pdf'

            # Generate download URLs
            base_url = config.get('base_url', 'http://localhost:5000')
            report.download_url = f"{base_url}/api/reports/{report_id}/download/pdf"

            # Mark as completed
            report.update_status('completed')
            report.data_source = data
            report.generation_config = config
            db.session.commit()

            logger.info(f"✅ Report files saved: PDF={pdf_path}, DOCX={docx_path}, Excel={excel_path}")

            logger.info(f"=== ✓ Comprehensive report {report_id} generated successfully ===")
            logger.info(f"Total files: PDF ({pdf_size}), DOCX ({docx_size}), Excel ({excel_size})")

            return {
                'report_id': report_id,
                'status': 'completed',
                'pdf_file_path': pdf_path,
                'docx_file_path': docx_path,
                'excel_file_path': excel_path,
                'pdf_download_url': report.pdf_download_url,
                'docx_download_url': report.docx_download_url,
                'excel_download_url': report.excel_download_url,
                'file_sizes': {
                    'pdf': pdf_size,
                    'docx': docx_size,
                    'excel': excel_size
                }
            }

        except Exception as e:
            # Update report status to failed
            report = Report.query.get(report_id)
            if report:
                report.update_status('failed', error_message=str(e))
                db.session.commit()

            logger.error(f"=== ✗ Error generating comprehensive report {report_id}: {str(e)} ===")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise ReportGenerationError(f"Failed to generate comprehensive report: {str(e)}")

    def generate_enhanced_pdf_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, int]:
        """
        Generate enhanced PDF report with real data, charts, and better formatting

        Args:
            data: Report data with records, metadata, and summary
            config: Report configuration

        Returns:
            Tuple of (file_path, file_size)
        """
        try:
            filename = self.generate_timestamp_filename("enhanced_report", "pdf")
            file_path = os.path.join(self.upload_folder, filename)

            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            story = []

            # Get styles - use default without custom colors
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER
            )

            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=15
            )

            # Add title
            title = config.get('title', 'Data Analysis Report')
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 20))

            # Add generation info
            info_style = styles['Normal']
            generation_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(generation_info, info_style))

            # Add data source info
            metadata = data.get('metadata', {})
            if metadata:
                story.append(Spacer(1, 15))
                story.append(Paragraph("Data Sources:", subtitle_style))
                for key, value in metadata.get('sources', {}).items():
                    if not key.endswith('_error'):
                        source_info = f"• Source {key}: {value.get('source_id', 'Unknown')} ({value.get('row_count', 0)} records)"
                        story.append(Paragraph(source_info, info_style))

            # Add summary statistics
            summary = data.get('summary', {})
            if summary:
                story.append(Spacer(1, 20))
                story.append(Paragraph("Data Summary:", subtitle_style))

                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Records', str(summary.get('record_count', 0))],
                    ['Total Columns', str(summary.get('column_count', 0))],
                    ['Data Sources', str(len(metadata.get('sources', {})))]
                ]

                summary_table = Table(summary_data)
                summary_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(summary_table)

            # Add data preview table
            records = data.get('records', [])
            if records:
                story.append(Spacer(1, 20))
                story.append(Paragraph("Data Preview (First 10 Records):", subtitle_style))

                # Get column names (limit to first 6 for space)
                sample_record = records[0] if records else {}
                columns = list(sample_record.keys())[:6]

                # Create table data
                table_data = [columns]
                for record in records[:10]:
                    row = [str(record.get(col, ''))[:30] for col in columns]  # Truncate long values
                    table_data.append(row)

                # Create table
                data_table = Table(table_data)
                data_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                story.append(data_table)

            # Build PDF
            doc.build(story)

            # Get file size
            file_size = os.path.getsize(file_path)

            logger.info(f"Enhanced PDF report generated successfully: {file_path} ({file_size} bytes)")
            return file_path, file_size

        except Exception as e:
            logger.error(f"Error generating enhanced PDF report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate enhanced PDF report: {str(e)}")

    def generate_enhanced_docx_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, int]:
        """
        Generate DOCX report using template ONLY - no custom formatting added
        Template must be specified in config, otherwise raises error

        Args:
            data: Report data to populate template with
            config: Report configuration (must include docx_template_path)

        Returns:
            Tuple of (file_path, file_size)
        """
        try:
            filename = self.generate_timestamp_filename("enhanced_report", "docx")
            file_path = os.path.join(self.upload_folder, filename)

            # Check if a DOCX template is specified
            template_path = config.get('docx_template_path')

            if not template_path or not os.path.exists(template_path):
                raise ReportGenerationError("DOCX template path must be specified in config and file must exist")

            # Use docxtpl to populate template - NO modifications to template
            logger.info(f"Using DOCX template: {template_path}")

            # Get template data from config, fallback to main data
            template_data = config.get('template_data', data)
            logger.info(f"Template data keys: {list(template_data.keys()) if isinstance(template_data, dict) else 'not a dict'}")

            # Transform data for DOCX template compatibility
            template_data = self._transform_data_for_docx(template_data)
            logger.info(f"Transformed template data keys: {list(template_data.keys()) if isinstance(template_data, dict) else 'not a dict'}")

            file_path = self._populate_docx_template(template_path, template_data, config, file_path)
            file_size = os.path.getsize(file_path)
            logger.info(f"DOCX report from template generated successfully: {file_path} ({file_size} bytes)")
            return file_path, file_size


        except Exception as e:
            logger.error(f"Error generating enhanced DOCX report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate enhanced DOCX report: {str(e)}")

    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old report files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_reports = Report.query.filter(
                Report.created_at < cutoff_date,
                Report.status.in_(['completed', 'failed'])
            ).all()

            for report in old_reports:
                # Remove all file format variants based on base file_path
                if report.file_path:
                    base_path_without_ext = os.path.splitext(report.file_path)[0]
                    report_dir = os.path.dirname(report.file_path)

                    # Try to delete all format variants
                    for ext in ['pdf', 'docx', 'xlsx']:
                        file_path = f"{base_path_without_ext}.{ext}"
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info(f"Deleted old file: {file_path}")
                            except Exception as e:
                                logger.warning(f"Failed to remove file {file_path}: {str(e)}")

                    # Clear file references
                    report.file_path = None
                    report.file_size = None
                    report.file_format = None

                # Update report
                report.status = 'archived'
                db.session.commit()

            logger.info(f"Cleaned up {len(old_reports)} old report files")

        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")

    def _transform_data_for_docx(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform mapped data to match DOCX template placeholders

        Converts structured data (e.g., {'participants': [...]}) to flat format
        that matches template variables like {{NAMA_PESERTA_HADIR}}, {{MARKAH_PRE}}, etc.
        """
        try:
            transformed = {}

            # Check if data has 'participants' key (from template_data_mapper)
            if 'participants' in data and isinstance(data['participants'], list):
                # Transform participants list to peserta_list format
                import math
                peserta_list = []
                for p in data['participants']:
                    # Get mark values and handle NaN properly
                    pre_mark_value = p.get('pre_mark', '')
                    post_mark_value = p.get('post_mark', '')

                    # Convert to string if not empty, but check for NaN
                    if pre_mark_value and not (isinstance(pre_mark_value, float) and math.isnan(pre_mark_value)):
                        pre_mark_str = str(pre_mark_value)
                    else:
                        pre_mark_str = ''

                    if post_mark_value and not (isinstance(post_mark_value, float) and math.isnan(post_mark_value)):
                        post_mark_str = str(post_mark_value)
                    else:
                        post_mark_str = ''

                    peserta = {
                        'bil': p.get('bil', ''),
                        'nama': p.get('name', ''),
                        'kad_pengenalan': p.get('ic', ''),
                        'no_telefon': p.get('tel', ''),
                        'jantina': p.get('gender', ''),
                        'alamat': p.get('address', ''),
                        'kehadiran_sabtu': p.get('attendance_day1', ''),
                        'kehadiran_ahad': p.get('attendance_day2', ''),
                        'nama_pre': p.get('name', ''),
                        'markah_pre': pre_mark_str,
                        'nama_post': p.get('name', ''),
                        'markah_post': post_mark_str
                    }
                    peserta_list.append(peserta)

                transformed['peserta_list'] = peserta_list
                logger.info(f"✅ Transformed {len(peserta_list)} participants to peserta_list format")

            # Check if data has 'records' or 'submissions' (raw Excel data)
            elif 'records' in data and isinstance(data['records'], list):
                peserta_list = []

                # Log available columns from first record for debugging
                if data['records']:
                    logger.info(f"📋 Available Excel columns: {list(data['records'][0].keys())}")

                for idx, record in enumerate(data['records'], 1):
                    # Handle Excel headers with newlines and variations
                    nama = (record.get('NAMA PESERTA HADIR') or
                           record.get('NAMA') or
                           record.get('Nama') or
                           record.get('name') or
                           f'Peserta {idx}')

                    kehadiran_sabtu = (record.get('KEHADIRAH \n(SABTU)') or
                                      record.get('KEHADIRAN \n(SABTU)') or
                                      record.get('KEHADIRAN_SABTU') or
                                      record.get('Attendance_Day1') or
                                      'Hadir')

                    kehadiran_ahad = (record.get('KEHADIRAN\n(AHAD)') or
                                     record.get('KEHADIRAN \n(AHAD)') or
                                     record.get('KEHADIRAN_AHAD') or
                                     record.get('Attendance_Day2') or
                                     'Hadir')

                    # Get mark values and handle NaN properly
                    import math
                    markah_pre_value = record.get('MARKAH_PRE') or record.get('Pre_Test') or record.get('pre_test')
                    markah_post_value = record.get('MARKAH_POST') or record.get('Post_Test') or record.get('post_test')

                    # Convert to string, but check for NaN first
                    if markah_pre_value is not None and not (isinstance(markah_pre_value, float) and math.isnan(markah_pre_value)):
                        markah_pre_str = str(markah_pre_value)
                    else:
                        markah_pre_str = ''

                    if markah_post_value is not None and not (isinstance(markah_post_value, float) and math.isnan(markah_post_value)):
                        markah_post_str = str(markah_post_value)
                    else:
                        markah_post_str = ''

                    # Auto-sync names: Use NAMA PESERTA HADIR as the primary name
                    # If NAMA PRE or NAMA POST are different, still use the main name
                    # This ensures marks stay linked even if user only updates NAMA PESERTA HADIR
                    peserta = {
                        'bil': str(idx),
                        'nama': nama,
                        'kad_pengenalan': record.get('KAD PENGENALAN') or record.get('NO_KP') or record.get('IC') or record.get('ic') or '',
                        'no_telefon': record.get('NO TELEFON') or record.get('NO_TEL') or record.get('Phone') or record.get('phone') or '',
                        'jantina': record.get('JANTINA') or record.get('Gender') or record.get('gender') or '',
                        'alamat': record.get('ALAMAT') or record.get('Address') or record.get('address') or '',
                        'kehadiran_sabtu': kehadiran_sabtu,
                        'kehadiran_ahad': kehadiran_ahad,
                        'nama_pre': nama,  # Always use main name, not NAMA PRE column
                        'markah_pre': markah_pre_str,
                        'nama_post': nama,  # Always use main name, not NAMA POST column
                        'markah_post': markah_post_str,
                        'penilaian': record.get('PENILAIAN') or '',
                        'alasan': record.get('ALASAN') or ''
                    }

                    # Log first participant data for debugging
                    if idx == 1:
                        logger.info(f"📋 Sample transformed participant data: {peserta}")

                    peserta_list.append(peserta)

                transformed['peserta_list'] = peserta_list
                logger.info(f"✅ Transformed {len(peserta_list)} records to peserta_list format")

            # Copy over any program/metadata fields
            if 'program' in data:
                for key, value in data['program'].items():
                    transformed[key] = value

            # Copy over simple fields
            for key in ['title', 'date', 'location', 'organizer', 'total_participants']:
                if key in data:
                    transformed[key] = data[key]

            # If no transformation was done, return original data
            if not transformed:
                logger.warning("⚠️ No data transformation applied, using original data")
                return data

            return transformed

        except Exception as e:
            logger.error(f"❌ Error transforming data for DOCX: {str(e)}")
            logger.error(f"Stack trace:", exc_info=True)
            return data  # Return original data as fallback

    def _populate_docx_template(self, template_path: str, data: Dict[str, Any], config: Dict[str, Any], output_path: str) -> str:
        """
        Populate DOCX template with data and add participant table

        Args:
            template_path: Path to the DOCX template file
            data: Data to populate the template with
            config: Report configuration
            output_path: Path to save the document

        Returns:
            Path to the output DOCX file
        """
        try:
            import shutil
            from docx import Document
            from docx.shared import Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement

            # Check if template has simple placeholders
            has_placeholders = False
            try:
                with open(template_path, 'rb') as f:
                    content = f.read()
                    if b'{{' in content:
                        has_placeholders = True
            except:
                pass

            if has_placeholders:
                # Try to use docxtpl for ALL placeholders including loops
                try:
                    from docxtpl import DocxTemplate
                    doc_tpl = DocxTemplate(template_path)

                    # Render ALL data including lists for loop support
                    logger.info(f"Rendering template with all data keys: {list(data.keys())}")
                    if 'peserta_list' in data:
                        logger.info(f"  - peserta_list contains {len(data['peserta_list'])} items")

                        # Log first 3 participants in detail
                        for idx, peserta in enumerate(data['peserta_list'][:3], 1):
                            logger.info(f"  - Participant {idx}: {peserta}")

                    # Log sample of data for debugging
                    for key, value in data.items():
                        if isinstance(value, list) and value:
                            logger.info(f"  - {key}: list with {len(value)} items")
                            if value:
                                logger.info(f"    First item keys: {list(value[0].keys()) if isinstance(value[0], dict) else 'not a dict'}")
                        elif not isinstance(value, (dict, list)):
                            logger.info(f"  - {key}: {value}")

                    # Render the template with ALL data
                    logger.info(f"📝 Calling doc_tpl.render() with {len(data)} top-level keys")
                    doc_tpl.render(data)
                    logger.info(f"💾 Saving rendered template to: {output_path}")
                    doc_tpl.save(output_path)

                    # Verify the rendered file doesn't still contain loop syntax
                    with open(output_path, 'rb') as f:
                        rendered_content = f.read()
                        if b'{%tr for' in rendered_content:
                            logger.error("❌ WARNING: Rendered file still contains loop syntax! docxtpl may have failed silently")
                        elif b'{{peserta' in rendered_content:
                            logger.error("❌ WARNING: Rendered file still contains {{peserta placeholders! Data not inserted")
                        else:
                            logger.info("✅ Verification: Loop syntax removed, template appears to be rendered correctly")

                    logger.info(f"✅ Template rendered successfully with docxtpl")
                except Exception as e:
                    logger.error(f"❌ docxtpl render failed: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    logger.warning(f"Falling back to copying template without data insertion")
                    shutil.copy2(template_path, output_path)
            else:
                # No placeholders, just copy
                logger.info("No placeholders found in template, copying as-is")
                shutil.copy2(template_path, output_path)

            # Only add participant table as fallback if template rendering failed
            # Check if the template was successfully rendered by looking for filled placeholders
            should_add_fallback_table = False
            if 'peserta_list' in data and isinstance(data['peserta_list'], list) and len(data['peserta_list']) > 0:
                try:
                    # Check if template has loop syntax that should have been rendered
                    with open(output_path, 'rb') as f:
                        content = f.read()
                        # If we still see loop syntax, it means rendering failed
                        if b'{%' in content or b'{{peserta_list}}' in content:
                            should_add_fallback_table = True
                            logger.warning("⚠️ Template loops not rendered, adding fallback participant table")
                        else:
                            logger.info("✅ Template loops appear to be rendered correctly, skipping fallback table")
                except (OSError, IOError) as e:
                    # If we can't check file, add the table to be safe
                    logger.warning(f"Could not check template rendering: {str(e)}")
                    should_add_fallback_table = True
                except Exception as e:
                    # Log unexpected errors but still add fallback
                    logger.error(f"Unexpected error checking template rendering: {str(e)}", exc_info=True)
                    should_add_fallback_table = True

            if should_add_fallback_table:
                logger.info(f"Adding fallback participant table with {len(data['peserta_list'])} rows")

                # Open the output document
                doc = Document(output_path)

                # Add page break and heading
                doc.add_page_break()
                heading = doc.add_heading('SENARAI PESERTA', level=1)
                heading.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                shading = OxmlElement('w:shd')
                shading.set(qn('w:fill'), '4472C4')
                heading._element.get_or_add_pPr().append(shading)

                # Create table
                headers = ['BIL', 'NAMA', 'IC', 'TELEFON', 'JANTINA', 'ALAMAT',
                          'SABTU', 'AHAD', 'PRE', 'MARKAH PRE', 'POST', 'MARKAH POST']

                table = doc.add_table(rows=1, cols=len(headers))

                # Style header row
                for i, h in enumerate(headers):
                    cell = table.rows[0].cells[i]
                    p = cell.paragraphs[0]
                    p.text = h
                    p.runs[0].font.bold = True
                    p.runs[0].font.size = Pt(9)
                    p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    shd = OxmlElement('w:shd')
                    shd.set(qn('w:fill'), '4472C4')
                    cell._element.get_or_add_tcPr().append(shd)

                # Add data rows
                for idx, peserta in enumerate(data['peserta_list'], 1):
                    row = table.add_row()
                    values = [
                        str(idx),
                        str(peserta.get('nama', '')),
                        str(peserta.get('kad_pengenalan', '')),
                        str(peserta.get('no_telefon', '')),
                        str(peserta.get('jantina', '')),
                        str(peserta.get('alamat', '')),
                        str(peserta.get('kehadiran_sabtu', '')),
                        str(peserta.get('kehadiran_ahad', '')),
                        str(peserta.get('nama_pre', '')),
                        str(peserta.get('markah_pre', '')),
                        str(peserta.get('nama_post', '')),
                        str(peserta.get('markah_post', ''))
                    ]
                    for i, val in enumerate(values):
                        row.cells[i].text = val if val else ''
                        if row.cells[i].paragraphs and row.cells[i].paragraphs[0].runs:
                            row.cells[i].paragraphs[0].runs[0].font.size = Pt(8)

                # Save with table
                doc.save(output_path)
                logger.info(f"✓ Participant table added successfully")

            # Add charts if provided in config
            if 'charts' in config and isinstance(config['charts'], list) and CHARTS_AVAILABLE:
                logger.info(f"📊 Processing {len(config['charts'])} charts for embedding")
                doc = Document(output_path)

                for chart_config in config['charts']:
                    try:
                        # Generate chart image
                        file_path, base64_data = chart_generator_service.generate_chart_from_config(chart_config)

                        if file_path and os.path.exists(file_path):
                            # Add page break and chart title
                            doc.add_page_break()
                            chart_title = chart_config.get('title', 'Chart')
                            doc.add_heading(chart_title, level=2)

                            # Add the chart image
                            from docx.shared import Inches
                            doc.add_picture(file_path, width=Inches(6))

                            logger.info(f"✅ Chart '{chart_title}' embedded successfully")
                        else:
                            logger.warning(f"⚠️ Chart image not generated for '{chart_config.get('title')}'")

                    except Exception as chart_error:
                        logger.error(f"❌ Error embedding chart: {str(chart_error)}")
                        # Continue with other charts even if one fails

                doc.save(output_path)
                logger.info(f"✓ All charts embedded successfully")

            # Add images if provided in config
            if 'images' in config and isinstance(config['images'], list):
                logger.info(f"🖼️ Processing {len(config['images'])} images for embedding")
                doc = Document(output_path)

                for image_config in config['images']:
                    try:
                        image_path = image_config.get('path') or image_config.get('src')
                        if image_path and os.path.exists(image_path):
                            # Add page break and image caption
                            doc.add_page_break()
                            caption = image_config.get('caption', 'Image')
                            doc.add_heading(caption, level=2)

                            # Add the image
                            from docx.shared import Inches
                            width = image_config.get('width', 6)
                            doc.add_picture(image_path, width=Inches(width))

                            logger.info(f"✅ Image '{caption}' embedded successfully")
                        else:
                            logger.warning(f"⚠️ Image not found: {image_path}")

                    except Exception as image_error:
                        logger.error(f"❌ Error embedding image: {str(image_error)}")

                doc.save(output_path)
                logger.info(f"✓ All images embedded successfully")

            logger.info(f"DOCX template processed and saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error handling DOCX template: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ReportGenerationError(f"Failed to process DOCX template: {str(e)}")

    def _populate_latex_template(self, template_path: str, data: Dict[str, Any]) -> str:
        """
        Populate LaTeX template with data using Jinja2

        Args:
            template_path: Path to the LaTeX template file
            data: Data to populate the template with

        Returns:
            Path to the populated LaTeX file
        """
        try:
            from jinja2 import Template, Environment, BaseLoader, StrictUndefined

            # Read template content
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Create Jinja2 environment with LaTeX-friendly settings
            env = Environment(
                loader=BaseLoader(),
                variable_start_string='{{',
                variable_end_string='}}',
                block_start_string='{%',
                block_end_string='%}',
                comment_start_string='{#',
                comment_end_string='#}',
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True
            )

            # Add LaTeX-specific filters
            def latex_escape(text):
                """Escape special LaTeX characters"""
                if text is None:
                    return ''
                text = str(text)
                # Escape common LaTeX special characters
                chars = {
                    '&': r'\&',
                    '%': r'\%',
                    '$': r'\$',
                    '#': r'\#',
                    '^': r'\textasciicircum{}',
                    '_': r'\_',
                    '{': r'\{',
                    '}': r'\}',
                    '~': r'\textasciitilde{}',
                    '\\': r'\textbackslash{}'
                }
                for char, replacement in chars.items():
                    text = text.replace(char, replacement)
                return text

            env.filters['latex_escape'] = latex_escape
            env.filters['e'] = latex_escape  # Shorter alias

            # Create template
            template = env.from_string(template_content)

            # Log data being used for debugging
            logger.info(f"Populating LaTeX template with data keys: {list(data.keys())}")

            # Render template with data
            try:
                rendered_content = template.render(**data)
                logger.info("LaTeX template rendered successfully")
            except Exception as render_error:
                logger.warning(f"Template rendering failed with strict mode: {render_error}")
                logger.warning(f"Missing variables or rendering issue - attempting fallback")
                # Try with undefined variables as empty strings
                env.undefined = lambda name: ''
                template = env.from_string(template_content)
                rendered_content = template.render(**data)
                logger.warning("Template rendered with undefined variables as empty strings")

            # Save populated template to temp file
            temp_filename = f"populated_{os.path.basename(template_path)}"
            temp_path = os.path.join(self.static_dir, temp_filename)

            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)

            logger.info(f"LaTeX template populated and saved to: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Error populating LaTeX template: {str(e)}")
            # Return original template path as fallback
            return template_path

# Global instance
report_generation_service = ReportGenerationService()
