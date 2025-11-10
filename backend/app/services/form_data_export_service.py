"""
Professional Form Data Export Service
Supports exporting form submissions to Excel, CSV, and Google Sheets
with advanced filtering, analytics, and formatting options.
"""

import os
import io
import csv
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
from pathlib import Path
import logging

# Excel/Data Processing
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference
import pandas as pd

# Google Sheets (optional)
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    HAS_GOOGLE_SHEETS = True
except ImportError:
    HAS_GOOGLE_SHEETS = False

from sqlalchemy import and_, or_, func
from .. import db
from ..models import Form, FormSubmission, User

logger = logging.getLogger(__name__)


class FormDataExportService:
    """
    Professional service for exporting form data to multiple formats
    with filtering, analytics, and professional formatting.
    """

    def __init__(self, export_folder: str = None):
        self.export_folder = export_folder or os.path.join(os.getcwd(), 'static', 'exports')
        self.ensure_export_directory()

        # Styling configurations
        self.header_style = {
            'font': Font(bold=True, color="FFFFFF", size=11),
            'fill': PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid"),
            'alignment': Alignment(horizontal='center', vertical='center'),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }

        # Formula injection protection - characters that can start a formula
        self.formula_chars = ['=', '+', '-', '@', '\t', '\r']

    def ensure_export_directory(self):
        """Ensure the export directory exists"""
        Path(self.export_folder).mkdir(parents=True, exist_ok=True)
        logger.info(f"Export directory ensured: {self.export_folder}")

    def generate_export_filename(self, form_id: int, export_format: str) -> str:
        """Generate a unique export filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"form_{form_id}_export_{timestamp}_{unique_id}.{export_format}"

    def sanitize_cell_value(self, value: Any) -> str:
        """
        Sanitize cell values to prevent CSV/Excel formula injection attacks.

        CSV Injection (also known as Formula Injection) is a security vulnerability
        where user-controlled data is exported to CSV/Excel files without proper
        sanitization, allowing attackers to inject formulas that execute when the
        file is opened.

        Protection strategy:
        1. Prefix dangerous characters with a single quote (')
        2. This tells Excel/CSV readers to treat the cell as text
        3. Preserves the original data while preventing formula execution

        Args:
            value: The cell value to sanitize

        Returns:
            Sanitized string value safe for Excel/CSV export
        """
        if value is None or value == '':
            return ''

        # Convert to string
        str_value = str(value)

        # Check if value starts with a potentially dangerous character
        if str_value and str_value[0] in self.formula_chars:
            # Prefix with single quote to force text interpretation
            # Also escape any existing single quotes
            str_value = "'" + str_value.replace("'", "''")
            logger.debug(f"Sanitized potentially dangerous value: {value[:50]}...")

        return str_value

    # ==================== MAIN EXPORT METHODS ====================

    def export_form_data(
        self,
        form_id: int,
        export_format: str = 'excel',
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Main export method that routes to the appropriate format handler.

        Args:
            form_id: The form ID to export
            export_format: 'excel', 'csv', or 'googlesheets'
            options: Export options including:
                - date_range: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
                - filters: {'status': 'approved', 'submitter_email': 'user@example.com'}
                - include_analytics: bool
                - excel_options: formatting preferences

        Returns:
            Dict with export results including download_url, file_size, etc.
        """
        start_time = time.time()
        options = options or {}

        try:
            # Validate form exists
            form = Form.query.get(form_id)
            if not form:
                raise ValueError(f"Form with ID {form_id} not found")

            # Get filtered submissions
            submissions, total_count = self._get_filtered_submissions(form_id, options)

            if not submissions:
                return {
                    'success': False,
                    'error': 'No submissions found matching the criteria',
                    'submissions_count': 0
                }

            # Route to appropriate export handler
            if export_format.lower() in ['excel', 'xlsx']:
                result = self._export_to_excel(form, submissions, options)
            elif export_format.lower() == 'csv':
                result = self._export_to_csv(form, submissions, options)
            elif export_format.lower() == 'googlesheets':
                result = self._export_to_google_sheets(form, submissions, options)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            # Calculate metrics
            generation_time = time.time() - start_time
            data_quality_score = self._calculate_data_quality(submissions)

            return {
                'success': True,
                'message': f'Successfully exported {len(submissions)} submissions to {export_format}',
                'download_url': result['download_url'],
                'file_path': result['file_path'],
                'file_size': result['file_size'],
                'submissions_count': len(submissions),
                'total_available': total_count,
                'generation_time': generation_time,
                'data_quality_score': data_quality_score,
                'format': export_format,
                'google_sheets_url': result.get('google_sheets_url')
            }

        except Exception as e:
            logger.error(f"Error exporting form {form_id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'submissions_count': 0
            }

    # ==================== EXCEL EXPORT ====================

    def _export_to_excel(
        self,
        form: Form,
        submissions: List[FormSubmission],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export form data to Excel with professional formatting"""

        # Create workbook
        wb = openpyxl.Workbook()

        # Remove default sheet
        wb.remove(wb.active)

        # Add data sheet
        ws_data = wb.create_sheet("Submissions", 0)
        self._populate_submissions_sheet(ws_data, form, submissions, options)

        # Add analytics sheet if requested
        if options.get('include_analytics', True):
            ws_analytics = wb.create_sheet("Analytics", 1)
            self._populate_analytics_sheet(ws_analytics, form, submissions)

        # Add form schema sheet if requested
        excel_options = options.get('excel_options', {})
        if excel_options.get('include_form_schema', True):
            ws_schema = wb.create_sheet("Form Schema", 2)
            self._populate_schema_sheet(ws_schema, form)

        # Save workbook
        filename = self.generate_export_filename(form.id, 'xlsx')
        file_path = os.path.join(self.export_folder, filename)
        wb.save(file_path)

        file_size = os.path.getsize(file_path)

        return {
            'download_url': f'/api/exports/download/{filename}',
            'file_path': file_path,
            'file_size': file_size
        }

    def _populate_submissions_sheet(
        self,
        ws,
        form: Form,
        submissions: List[FormSubmission],
        options: Dict[str, Any]
    ):
        """Populate the submissions data sheet"""

        # Get form fields
        form_schema = form.schema or {}
        fields = form_schema.get('fields', [])

        # Create headers
        headers = ['ID', 'Submitted At', 'Status', 'Submitter Email']
        for field in fields:
            headers.append(field.get('label', field.get('name', 'Unknown')))

        # Write headers with styling
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = self.header_style['font']
            cell.fill = self.header_style['fill']
            cell.alignment = self.header_style['alignment']
            cell.border = self.header_style['border']

        # Write data rows
        for row_num, submission in enumerate(submissions, 2):
            col_num = 1

            # Submission metadata
            ws.cell(row=row_num, column=col_num, value=submission.id)
            col_num += 1

            ws.cell(row=row_num, column=col_num, value=submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if submission.submitted_at else '')
            col_num += 1

            ws.cell(row=row_num, column=col_num, value=submission.status or 'submitted')
            col_num += 1

            ws.cell(row=row_num, column=col_num, value=submission.submitter_email or '')
            col_num += 1

            # Form field data
            submission_data = submission.data or {}
            for field in fields:
                field_name = field.get('name', '')
                field_value = submission_data.get(field_name, '')

                # Format complex values
                if isinstance(field_value, (dict, list)):
                    field_value = json.dumps(field_value, ensure_ascii=False)

                # Sanitize value to prevent formula injection
                sanitized_value = self.sanitize_cell_value(field_value)

                cell = ws.cell(row=row_num, column=col_num, value=sanitized_value)

                # Apply alternating row colors
                if row_num % 2 == 0:
                    cell.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

                col_num += 1

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)

            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Freeze header row
        ws.freeze_panes = 'A2'

    def _populate_analytics_sheet(self, ws, form: Form, submissions: List[FormSubmission]):
        """Populate analytics sheet with charts and statistics"""

        # Title
        ws.merge_cells('A1:D1')
        title_cell = ws['A1']
        title_cell.value = f'Analytics for {form.title}'
        title_cell.font = Font(bold=True, size=16, color="1E293B")
        title_cell.alignment = Alignment(horizontal='center')

        row = 3

        # Summary Statistics
        ws.cell(row=row, column=1, value='Summary Statistics').font = Font(bold=True, size=14)
        row += 1

        ws.cell(row=row, column=1, value='Total Submissions:')
        ws.cell(row=row, column=2, value=len(submissions))
        row += 1

        # Status breakdown
        status_counts = {}
        for sub in submissions:
            status = sub.status or 'submitted'
            status_counts[status] = status_counts.get(status, 0) + 1

        ws.cell(row=row, column=1, value='Status Breakdown:').font = Font(bold=True)
        row += 1

        for status, count in status_counts.items():
            ws.cell(row=row, column=1, value=f'  {status.title()}:')
            ws.cell(row=row, column=2, value=count)
            row += 1

        row += 1

        # Submission timeline
        ws.cell(row=row, column=1, value='Submission Timeline:').font = Font(bold=True)
        row += 1

        # Group by date
        date_counts = {}
        for sub in submissions:
            if sub.submitted_at:
                date_key = sub.submitted_at.date()
                date_counts[date_key] = date_counts.get(date_key, 0) + 1

        ws.cell(row=row, column=1, value='Date')
        ws.cell(row=row, column=2, value='Count')
        row += 1

        for date, count in sorted(date_counts.items()):
            ws.cell(row=row, column=1, value=date.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=2, value=count)
            row += 1

        # Add a simple bar chart
        if len(date_counts) > 0:
            chart = BarChart()
            chart.title = "Submissions Over Time"
            chart.x_axis.title = "Date"
            chart.y_axis.title = "Count"

            data = Reference(ws, min_col=2, min_row=row-len(date_counts)-1, max_row=row-1)
            categories = Reference(ws, min_col=1, min_row=row-len(date_counts), max_row=row-1)

            chart.add_data(data, titles_from_data=True)
            chart.set_categories(categories)

            ws.add_chart(chart, f"D{row-len(date_counts)-5}")

    def _populate_schema_sheet(self, ws, form: Form):
        """Populate form schema information sheet"""

        ws.cell(row=1, column=1, value='Form Schema Information').font = Font(bold=True, size=14)

        row = 3
        ws.cell(row=row, column=1, value='Form Title:').font = Font(bold=True)
        ws.cell(row=row, column=2, value=form.title)
        row += 1

        ws.cell(row=row, column=1, value='Form ID:').font = Font(bold=True)
        ws.cell(row=row, column=2, value=form.id)
        row += 1

        ws.cell(row=row, column=1, value='Created At:').font = Font(bold=True)
        ws.cell(row=row, column=2, value=form.created_at.strftime('%Y-%m-%d %H:%M:%S') if form.created_at else 'N/A')
        row += 2

        # Field definitions
        ws.cell(row=row, column=1, value='Field Definitions:').font = Font(bold=True, size=12)
        row += 1

        ws.cell(row=row, column=1, value='Name').font = Font(bold=True)
        ws.cell(row=row, column=2, value='Label').font = Font(bold=True)
        ws.cell(row=row, column=3, value='Type').font = Font(bold=True)
        ws.cell(row=row, column=4, value='Required').font = Font(bold=True)
        row += 1

        form_schema = form.schema or {}
        fields = form_schema.get('fields', [])

        for field in fields:
            ws.cell(row=row, column=1, value=field.get('name', ''))
            ws.cell(row=row, column=2, value=field.get('label', ''))
            ws.cell(row=row, column=3, value=field.get('type', 'text'))
            ws.cell(row=row, column=4, value='Yes' if field.get('required') else 'No')
            row += 1

    # ==================== CSV EXPORT ====================

    def _export_to_csv(
        self,
        form: Form,
        submissions: List[FormSubmission],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export form data to CSV format"""

        # Get form fields
        form_schema = form.schema or {}
        fields = form_schema.get('fields', [])

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = ['ID', 'Submitted At', 'Status', 'Submitter Email']
        for field in fields:
            headers.append(field.get('label', field.get('name', 'Unknown')))
        writer.writerow(headers)

        # Write data rows
        for submission in submissions:
            row = [
                submission.id,
                submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if submission.submitted_at else '',
                submission.status or 'submitted',
                submission.submitter_email or ''
            ]

            submission_data = submission.data or {}
            for field in fields:
                field_name = field.get('name', '')
                field_value = submission_data.get(field_name, '')

                if isinstance(field_value, (dict, list)):
                    field_value = json.dumps(field_value)

                # Sanitize value to prevent formula injection
                sanitized_value = self.sanitize_cell_value(field_value)
                row.append(sanitized_value)

            writer.writerow(row)

        # Save to file
        filename = self.generate_export_filename(form.id, 'csv')
        file_path = os.path.join(self.export_folder, filename)

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write(output.getvalue())

        file_size = os.path.getsize(file_path)

        return {
            'download_url': f'/api/exports/download/{filename}',
            'file_path': file_path,
            'file_size': file_size
        }

    # ==================== GOOGLE SHEETS EXPORT ====================

    def _export_to_google_sheets(
        self,
        form: Form,
        submissions: List[FormSubmission],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export form data to Google Sheets.
        Requires Google Service Account credentials.
        """

        if not HAS_GOOGLE_SHEETS:
            raise ImportError("Google Sheets API libraries not installed. Run: pip install google-api-python-client google-auth")

        # This is a placeholder - you'll need to configure Google credentials
        # For now, we'll export to Excel and provide instructions

        # First create Excel file
        excel_result = self._export_to_excel(form, submissions, options)

        # TODO: Implement actual Google Sheets upload
        # 1. Set up Google Service Account
        # 2. Share spreadsheet with service account email
        # 3. Use Google Sheets API to create and populate spreadsheet

        return {
            **excel_result,
            'google_sheets_url': None,
            'note': 'Google Sheets export requires additional configuration. Excel file generated instead.'
        }

    # ==================== HELPER METHODS ====================

    def _get_filtered_submissions(
        self,
        form_id: int,
        options: Dict[str, Any]
    ) -> Tuple[List[FormSubmission], int]:
        """Get submissions with applied filters"""

        query = FormSubmission.query.filter_by(form_id=form_id)

        # Apply date range filter
        date_range = options.get('date_range', {})
        if date_range.get('start'):
            try:
                start_date = datetime.fromisoformat(date_range['start'])
                query = query.filter(FormSubmission.submitted_at >= start_date)
            except ValueError:
                logger.warning(f"Invalid start date: {date_range['start']}")

        if date_range.get('end'):
            try:
                end_date = datetime.fromisoformat(date_range['end'])
                # Add one day to include the end date
                end_date = end_date + timedelta(days=1)
                query = query.filter(FormSubmission.submitted_at < end_date)
            except ValueError:
                logger.warning(f"Invalid end date: {date_range['end']}")

        # Apply status filter
        filters = options.get('filters', {})
        status = filters.get('status')
        if status and status.lower() != 'all':
            query = query.filter(FormSubmission.status == status.lower())

        # Apply email filter
        submitter_email = filters.get('submitter_email')
        if submitter_email:
            query = query.filter(FormSubmission.submitter_email.ilike(f'%{submitter_email}%'))

        # Get total count before limiting
        total_count = query.count()

        # Order by submission date (newest first)
        query = query.order_by(FormSubmission.submitted_at.desc())

        # Limit results (default: 10000)
        max_records = options.get('max_records', 10000)
        submissions = query.limit(max_records).all()

        return submissions, total_count

    def _calculate_data_quality(self, submissions: List[FormSubmission]) -> float:
        """Calculate data quality score based on completeness"""

        if not submissions:
            return 0.0

        total_fields = 0
        filled_fields = 0

        for submission in submissions:
            data = submission.data or {}
            for value in data.values():
                total_fields += 1
                if value is not None and value != '':
                    filled_fields += 1

        if total_fields == 0:
            return 1.0

        return round(filled_fields / total_fields, 2)

    # ==================== GOOGLE FORMS SUPPORT ====================

    def export_google_form_responses(
        self,
        google_form_id: str,
        form_responses: List[Dict[str, Any]],
        form_info: Dict[str, Any],
        export_format: str = 'excel',
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Export Google Forms responses to Excel/CSV.

        Args:
            google_form_id: The Google Form ID
            form_responses: List of response dictionaries
            form_info: Form metadata (title, questions, etc.)
            export_format: 'excel' or 'csv'
            options: Export options
        """
        start_time = time.time()
        options = options or {}

        try:
            if export_format.lower() in ['excel', 'xlsx']:
                result = self._export_google_responses_to_excel(
                    google_form_id, form_responses, form_info, options
                )
            elif export_format.lower() == 'csv':
                result = self._export_google_responses_to_csv(
                    google_form_id, form_responses, form_info, options
                )
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            generation_time = time.time() - start_time

            return {
                'success': True,
                'message': f'Successfully exported {len(form_responses)} Google Form responses to {export_format}',
                'download_url': result['download_url'],
                'file_path': result['file_path'],
                'file_size': result['file_size'],
                'responses_count': len(form_responses),
                'generation_time': generation_time,
                'format': export_format
            }

        except Exception as e:
            logger.error(f"Error exporting Google Form {google_form_id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'responses_count': 0
            }

    def _export_google_responses_to_excel(
        self,
        google_form_id: str,
        form_responses: List[Dict[str, Any]],
        form_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export Google Forms responses to Excel"""

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Responses"

        # Get questions - questions dict is keyed by itemId with title as value
        questions_dict = form_info.get('questions', {})

        # Build ordered list of question titles from the questions dict
        question_titles = []
        if isinstance(questions_dict, dict):
            # Questions dict format: {itemId: {title: ..., type: ..., required: ...}}
            for question_data in questions_dict.values():
                if isinstance(question_data, dict):
                    question_titles.append(question_data.get('title', 'Question'))
        elif isinstance(questions_dict, list):
            # Fallback: questions as list
            for question in questions_dict:
                question_titles.append(question.get('title', 'Question'))

        logger.info(f"📊 Exporting {len(form_responses)} responses with {len(question_titles)} questions")
        logger.debug(f"Question titles: {question_titles}")

        # Create headers
        headers = ['Response ID', 'Timestamp']
        headers.extend(question_titles)

        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = self.header_style['font']
            cell.fill = self.header_style['fill']
            cell.alignment = self.header_style['alignment']

        # Write responses
        for row_num, response in enumerate(form_responses, 2):
            ws.cell(row=row_num, column=1, value=response.get('response_id', ''))
            ws.cell(row=row_num, column=2, value=response.get('create_time', ''))

            # Answers are keyed by question TITLE, not ID
            answers = response.get('answers', {})
            logger.debug(f"Response {row_num-1} has {len(answers)} answers: {list(answers.keys())[:3]}...")

            for col_num, question_title in enumerate(question_titles, 3):
                # Get answer directly by question title
                answer_value = answers.get(question_title, '')

                # Convert to string if needed
                if isinstance(answer_value, (dict, list)):
                    answer_text = json.dumps(answer_value, ensure_ascii=False)
                else:
                    answer_text = str(answer_value) if answer_value else ''

                # Sanitize value to prevent formula injection
                sanitized_answer = self.sanitize_cell_value(answer_text)
                ws.cell(row=row_num, column=col_num, value=sanitized_answer)

        # Auto-adjust columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # Save
        filename = f"google_form_{google_form_id[:8]}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(self.export_folder, filename)

        logger.info(f"Saving Google Forms export to: {file_path}")
        wb.save(file_path)

        # Verify file was created
        if not os.path.exists(file_path):
            logger.error(f"File was not created at {file_path}")
            raise Exception(f"Failed to create export file at {file_path}")

        file_size = os.path.getsize(file_path)
        logger.info(f"Google Forms export saved successfully. File size: {file_size} bytes")

        return {
            'download_url': f'/api/exports/download/{filename}',
            'file_path': file_path,
            'file_size': file_size
        }

    def _export_google_responses_to_csv(
        self,
        google_form_id: str,
        form_responses: List[Dict[str, Any]],
        form_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export Google Forms responses to CSV"""

        output = io.StringIO()
        writer = csv.writer(output)

        # Get questions - questions dict is keyed by itemId with title as value
        questions_dict = form_info.get('questions', {})

        # Build ordered list of question titles from the questions dict
        question_titles = []
        if isinstance(questions_dict, dict):
            # Questions dict format: {itemId: {title: ..., type: ..., required: ...}}
            for question_data in questions_dict.values():
                if isinstance(question_data, dict):
                    question_titles.append(question_data.get('title', 'Question'))
        elif isinstance(questions_dict, list):
            # Fallback: questions as list
            for question in questions_dict:
                question_titles.append(question.get('title', 'Question'))

        # Write headers
        headers = ['Response ID', 'Timestamp']
        headers.extend(question_titles)
        writer.writerow(headers)

        # Write responses
        for response in form_responses:
            row = [
                response.get('response_id', ''),
                response.get('create_time', '')
            ]

            # Answers are keyed by question TITLE, not ID
            answers = response.get('answers', {})
            for question_title in question_titles:
                # Get answer directly by question title
                answer_value = answers.get(question_title, '')

                # Convert to string if needed
                if isinstance(answer_value, (dict, list)):
                    answer_text = json.dumps(answer_value, ensure_ascii=False)
                else:
                    answer_text = str(answer_value) if answer_value else ''

                # Sanitize value to prevent formula injection
                sanitized_answer = self.sanitize_cell_value(answer_text)
                row.append(sanitized_answer)

            writer.writerow(row)

        # Save
        filename = f"google_form_{google_form_id[:8]}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(self.export_folder, filename)

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write(output.getvalue())

        return {
            'download_url': f'/api/exports/download/{filename}',
            'file_path': file_path,
            'file_size': os.path.getsize(file_path)
        }


# Global service instance
form_data_export_service = FormDataExportService()
