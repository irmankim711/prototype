"""
Report Generation Service
Encapsulates logic for generating reports from Excel data, including data extraction,
template mapping, and chart generation.
"""

import os
import logging
import uuid
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from flask import current_app
from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Inches

from app import db
from app.models import User, ParsedExcelFile, ExcelTable, Report, Program, ReportTemplate
from app.services.excel_data_extractor import excel_data_extractor
from app.services.template_data_mapper import template_data_mapper
from app.services.chart_generator_service import chart_generator_service
from app.utils.railway_paths import get_reports_dir, get_templates_dir, validate_excel_path

logger = logging.getLogger(__name__)

class ReportGenerationService:
    """Service for generating and regenerating reports"""

    def __init__(self):
        self.logger = logger

    def generate_report(self, 
                       user_id: int, 
                       template_id: str, 
                       file_ids: List[str] = None, 
                       excel_file_path: str = None,
                       report_title: str = "Automated Report",
                       charts: List[Dict] = None,
                       images: List[Dict] = None,
                       existing_report_id: int = None) -> Dict[str, Any]:
        """
        Generate a report from Excel data and a template.
        
        Args:
            user_id: ID of the user generating the report
            template_id: ID of the template to use
            file_ids: List of ParsedExcelFile IDs to use as data source
            excel_file_path: Legacy path to Excel file (fallback)
            report_title: Title of the report
            charts: Configuration for charts to generate
            images: Configuration for images to embed
            existing_report_id: If provided, update this report record instead of creating new
            
        Returns:
            Dictionary containing generation result (success, paths, etc.)
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"🆔 [{request_id}] Starting report generation for user {user_id}")
        
        start_time = time.time()
        
        try:
            # 1. Load and prepare data
            data_context = self._load_data(request_id, user_id, file_ids, excel_file_path)
            if not data_context.get('success'):
                return data_context
                
            excel_records = data_context['excel_records']
            excel_columns = data_context['excel_columns']
            excel_metadata = data_context['excel_metadata']
            file_size = data_context['file_size']
            source_files = data_context['source_files']
            actual_excel_path = data_context['actual_excel_path']
            
            # 2. Get Template
            template_file, template_db_record = self._get_template(request_id, template_id, user_id)
            if not template_file:
                return {
                    'success': False, 
                    'error': f'Template not found: {template_id}'
                }
                
            # 3. Map Data to Template
            mapped_data = self._map_data(request_id, excel_records, excel_columns, excel_metadata, 
                                        file_size, actual_excel_path, template_file.name)
                                        
            # 4. Render Report
            render_result = self._render_report(
                request_id, 
                template_file, 
                mapped_data, 
                excel_records, 
                data_context.get('structured_data', {}),
                template_id,
                charts,
                images,
                actual_excel_path,
                file_ids
            )
            
            if not render_result.get('success'):
                return render_result
                
            output_path = render_result['output_path']
            output_filename = render_result['output_filename']
            
            # 5. Save/Update Database Record
            report_record = self._save_report_record(
                user_id,
                report_title,
                template_id,
                template_db_record,
                output_path,
                output_filename,
                data_context,
                existing_report_id
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"🆔 [{request_id}] Report generation completed in {elapsed:.2f}s")
            
            return {
                'success': True,
                'report_id': report_record.id,
                'output_path': str(output_path),
                'report_path': str(output_path),
                'output_filename': output_filename,
                'file_url': f'/static/reports/{output_filename}', # Approximate URL
                'template_used': template_file.name
            }
            
        except Exception as e:
            self.logger.error(f"🆔 [{request_id}] Report generation failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': 'Report generation failed',
                'details': str(e)
            }

    def _load_data(self, request_id: str, user_id: int, file_ids: List[str], excel_file_path: str) -> Dict[str, Any]:
        """Load data from Excel files or legacy path"""
        excel_records = []
        excel_columns = []
        excel_metadata = {}
        file_size = 0
        source_files = []
        actual_excel_path = None
        
        # Normalize file_ids
        if not file_ids and not excel_file_path:
             return {'success': False, 'error': 'No data source provided'}

        try:
            if file_ids:
                self.logger.info(f"🆔 [{request_id}] Loading data from {len(file_ids)} files: {file_ids}")
                
                for fid in file_ids:
                    parsed_file = ParsedExcelFile.query.filter_by(id=fid, user_id=user_id).first()
                    if not parsed_file:
                        self.logger.warning(f"🆔 [{request_id}] File not found: {fid}")
                        continue
                        
                    # Use the first file's path as the main path (for charts etc)
                    if not actual_excel_path:
                        actual_excel_path = parsed_file.file_path
                        
                    # Get table metadata
                    table = ExcelTable.query.filter_by(parsed_file_id=fid).first()
                    
                    # Read full data from disk
                    if os.path.exists(parsed_file.file_path):
                        import pandas as pd
                        try:
                            if table and table.sheet_name:
                                df = pd.read_excel(parsed_file.file_path, sheet_name=table.sheet_name)
                            else:
                                df = pd.read_excel(parsed_file.file_path)
                                
                            # Extract headers and records
                            headers = df.columns.tolist()
                            records = df.to_dict('records')
                            
                            # Merge columns
                            for h in headers:
                                if h not in excel_columns:
                                    excel_columns.append(h)
                                    
                            # Add source metadata
                            for record in records:
                                record['_source_file'] = parsed_file.original_filename
                                record['_source_file_id'] = fid
                                excel_records.append(record)
                                
                            file_size += parsed_file.file_size or 0
                            source_files.append(parsed_file.original_filename)
                            
                        except Exception as e:
                            self.logger.error(f"🆔 [{request_id}] Error reading file {parsed_file.file_path}: {e}")
                    else:
                        self.logger.warning(f"🆔 [{request_id}] File not found on disk: {parsed_file.file_path}")
                        
            elif excel_file_path:
                # Legacy path mode
                self.logger.info(f"🆔 [{request_id}] Loading data from legacy path: {excel_file_path}")
                path_obj = validate_excel_path(excel_file_path)
                if not path_obj:
                    return {'success': False, 'error': 'Excel file not found'}
                    
                actual_excel_path = str(path_obj)
                file_size = path_obj.stat().st_size
                
                # Parse with pandas directly for consistency
                import pandas as pd
                try:
                    df = pd.read_excel(actual_excel_path)
                    excel_columns = df.columns.tolist()
                    excel_records = df.to_dict('records')
                    source_files.append(path_obj.name)
                except Exception as e:
                    return {'success': False, 'error': f'Failed to parse Excel: {str(e)}'}

            if not excel_records:
                return {'success': False, 'error': 'No data found in selected files'}
                
            # Extract structured data
            structured_data = {}
            if actual_excel_path:
                try:
                    structured_data = excel_data_extractor.extract_data_from_file(actual_excel_path)
                except Exception as e:
                    self.logger.warning(f"🆔 [{request_id}] Structured extraction failed: {e}")
            
            return {
                'success': True,
                'excel_records': excel_records,
                'excel_columns': excel_columns,
                'excel_metadata': excel_metadata,
                'file_size': file_size,
                'source_files': source_files,
                'actual_excel_path': actual_excel_path,
                'structured_data': structured_data
            }
            
        except Exception as e:
            self.logger.error(f"🆔 [{request_id}] Data loading failed: {e}", exc_info=True)
            return {'success': False, 'error': f'Data loading failed: {str(e)}'}

        return template_file, template_db_record

    def _get_template(self, request_id: str, template_id: str, user_id: int) -> Tuple[Optional[Path], Any]:
        """Retrieve template file and DB record"""
        # This logic mimics the existing logic in nextgen_report_builder
        # For brevity, I'll simplify slightly but keep core lookup logic
        
        # 1. Try DB lookup
        template_db_record = None
        try:
            # Try integer ID
            if str(template_id).isdigit():
                template_db_record = ReportTemplate.query.get(int(template_id))
            
            # Try name lookup if not found
            if not template_db_record:
                template_db_record = ReportTemplate.query.filter_by(name=str(template_id)).first()
        except Exception as e:
            self.logger.warning(f"🆔 [{request_id}] DB template lookup failed: {e}")

        # 2. Filesystem lookup
        templates_dir = get_templates_dir()
        template_file = None
        
        # Check DB path first
        if template_db_record and template_db_record.file_path:
            p = Path(template_db_record.file_path)
            if p.exists():
                template_file = p
        
        # Fallback to searching directory
        if not template_file:
            # TEMPLATE MAPPINGS (Fix for missing DB templates)
            TEMPLATE_MAPPINGS = {
                'uwais_global_solution': 'report_template_copy.docx',
                'puncak_alam_fu': '04- LAPORAN FU _ PUNCAK ALAM_final.docx'
            }
            
            # Check mapping first
            mapped_name = TEMPLATE_MAPPINGS.get(str(template_id))
            if mapped_name:
                p = templates_dir / mapped_name
                if p.exists():
                    self.logger.info(f"🆔 [{request_id}] Found template via mapping: {template_id} -> {mapped_name}")
                    template_file = p

            # Try exact match if no mapping found or mapping file missing
            if not template_file:
                p = templates_dir / str(template_id)
                if p.exists():
                    template_file = p
                else:
                    # Try extensions
                    for ext in ['.docx', '.jinja', '.html']:
                        p = templates_dir / f"{template_id}{ext}"
                        if p.exists():
                            template_file = p
                            break
        
        return template_file, template_db_record

    def _map_data(self, request_id: str, records: List[Dict], columns: List[str], 
                 metadata: Dict, file_size: int, file_path: str, template_name: str) -> Dict:
        """Map raw data to template context"""
        raw_data = {
            'records': records,
            'submissions': records,
            'columns': columns,
            'metadata': {
                'file_path': file_path,
                'file_size': file_size,
                'record_count': len(records),
                'column_count': len(columns),
                **metadata
            }
        }
        
        return template_data_mapper.map_data_for_template(raw_data, template_name)

    def _render_report(self, request_id: str, template_file: Path, mapped_data: Dict, 
                      excel_records: List[Dict], structured_data: Dict, template_id: str,
                      charts: List[Dict], images: List[Dict], excel_file_path: str,
                      file_ids: List[str]) -> Dict[str, Any]:
        """Render the DOCX template with data and embed charts"""
        try:
            output_dir = get_reports_dir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'report_{template_id}_{timestamp}.docx'
            output_path = output_dir / output_filename
            
            doc = DocxTemplate(template_file)
            
            # Prepare context
            context = dict(mapped_data) if mapped_data else {}
            
            # Add standard fields
            context.update({
                'records': excel_records,
                'data': excel_records,
                'total_records': len(excel_records),
                'generated_date': datetime.now().strftime('%d/%m/%Y'),
                'generated_time': datetime.now().strftime('%H:%M'),
                
                # Structured data
                'program': structured_data.get('program_info', {}),
                'participants': structured_data.get('participants', []),
                'attendance': structured_data.get('attendance', []),
                'statistics': structured_data.get('statistics', {}),
            })
            
            # Add flattened fields for convenience
            prog = structured_data.get('program_info', {})
            context.update({
                'program_title': prog.get('title', 'Program Report'),
                'program_date': prog.get('date', ''),
                'program_location': prog.get('location', ''),
            })
            
            # Add first record fields as top-level variables
            if excel_records:
                first = excel_records[0]
                for k, v in first.items():
                    context[k] = v
                    clean_k = k.replace(' ', '_').lower()
                    if clean_k != k:
                        context[clean_k] = v
            
            # Render
            doc.render(context)
            doc.save(output_path)
            
            # Embed Charts
            if charts:
                self._embed_charts(request_id, output_path, charts, context, excel_file_path, file_ids)
                
            # Embed Images
            if images:
                self._embed_images(request_id, output_path, images)
                
            return {
                'success': True,
                'output_path': output_path,
                'output_filename': output_filename
            }
            
        except Exception as e:
            self.logger.error(f"🆔 [{request_id}] Rendering failed: {e}", exc_info=True)
            return {'success': False, 'error': f'Rendering failed: {str(e)}'}

    def _embed_charts(self, request_id: str, doc_path: Path, charts: List[Dict], 
                     context: Dict, excel_file_path: str, file_ids: List[str]):
        """Generate and embed charts into the document"""
        try:
            doc = Document(doc_path)
            
            for chart_config in charts:
                chart_data = []
                
                # 1. Try loading from specific sheet
                if 'sheetName' in chart_config and excel_file_path:
                    try:
                        import pandas as pd
                        # Handle multiple files case - use first file
                        path_to_read = excel_file_path
                        if path_to_read == 'multiple_files' and file_ids:
                            pf = ParsedExcelFile.query.get(file_ids[0])
                            if pf: path_to_read = pf.file_path
                            
                        if path_to_read and os.path.exists(path_to_read):
                            df = pd.read_excel(path_to_read, sheet_name=chart_config['sheetName'])
                            chart_data = df.to_dict('records')
                    except Exception as e:
                        self.logger.warning(f"🆔 [{request_id}] Failed to load sheet for chart: {e}")
                
                # 2. Fallback to context data
                if not chart_data and 'data' in chart_config:
                    data_ref = chart_config['data']
                    if isinstance(data_ref, str) and data_ref in context:
                        chart_data = context[data_ref]
                    elif isinstance(data_ref, list):
                        chart_data = data_ref
                
                if not chart_data:
                    continue
                    
                # Generate Chart
                resolved_config = {
                    'chartType': chart_config.get('type', 'bar'),
                    'data': chart_data,
                    'config': chart_config
                }
                
                img_path, _ = chart_generator_service.generate_chart_from_config(resolved_config)
                
                if img_path and os.path.exists(img_path):
                    doc.add_page_break()
                    doc.add_heading(chart_config.get('title', 'Chart'), level=2)
                    doc.add_picture(img_path, width=Inches(6))
            
            doc.save(doc_path)
            
        except Exception as e:
            self.logger.error(f"🆔 [{request_id}] Chart embedding failed: {e}")

    def _embed_images(self, request_id: str, doc_path: Path, images: List[Dict]):
        """Embed images into the document"""
        try:
            doc = Document(doc_path)
            for img_config in images:
                path = img_config.get('path') or img_config.get('src')
                if path and os.path.exists(path):
                    doc.add_page_break()
                    doc.add_heading(img_config.get('caption', 'Image'), level=2)
                    doc.add_picture(path, width=Inches(img_config.get('width', 6)))
            doc.save(doc_path)
        except Exception as e:
            self.logger.error(f"🆔 [{request_id}] Image embedding failed: {e}")

    def _save_report_record(self, user_id: int, title: str, template_id: str, 
                           template_record: Any, output_path: Path, output_filename: str,
                           data_context: Dict, existing_report_id: int = None) -> Report:
        """Save or update the report record in the database"""
        
        # Get default program if needed
        program_id = None
        default_program = Program.query.first()
        if default_program:
            program_id = default_program.id
            
        # Prepare data source blob
        data_source = {
            'file_ids': [f for f in data_context.get('source_files', [])], # Store names/ids
            'record_count': len(data_context.get('excel_records', [])),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if existing_report_id:
            report = Report.query.get(existing_report_id)
            if report:
                report.title = title
                report.file_path = str(output_path)
                report.file_size = output_path.stat().st_size
                # report.updated_at = datetime.utcnow() # Report model doesn't have updated_at
                report.generated_at = datetime.utcnow()
                report.data_source = data_source
                # Don't change template_id or program_id usually
                db.session.commit()
                return report
        
        # Create new
        # Handle template_id conversion
        db_template_id = None
        if template_record and hasattr(template_record, 'id'):
            # If template_record.id is string (UUID) but Report.template_id is Integer, we might have an issue.
            # Report.template_id is Integer. ReportTemplate.id is String.
            # We'll try to use it if it's an int, otherwise leave None or try conversion
            try:
                db_template_id = int(template_record.id)
            except (ValueError, TypeError):
                # If template ID is string (e.g. 'uwais_global_solution'), we can't store it in Integer column
                # We might need to store it in generation_config or just skip it
                pass

        report = Report(
            created_by=str(user_id), # Report uses string created_by
            program_id=program_id,
            template_id=db_template_id,
            title=title,
            file_path=str(output_path),
            file_size=output_path.stat().st_size,
            generation_status='completed',
            data_source=data_source,
            created_at=datetime.utcnow(),
            generated_at=datetime.utcnow()
        )
        db.session.add(report)
        db.session.commit()
        return report

# Global instance
report_generation_service = ReportGenerationService()
