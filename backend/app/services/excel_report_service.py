"""
Excel Report Generation Service
Combines Excel processing, DOCX generation, and PDF conversion using ConvertAPI
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .convertapi_service import convertapi_service
from .report_generator import create_word_report, create_pdf_report
from .excel_processing_service import excel_processing_service
from .. import db
from ..models import Report

logger = logging.getLogger(__name__)

class ExcelReportService:
    """Service for generating reports from Excel data with PDF conversion"""

    def __init__(self):
        self.upload_folder = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
        self.reports_dir = self.upload_folder / 'reports'
        self.pdfs_dir = self.upload_folder / 'pdfs'

        # Create directories
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.pdfs_dir.mkdir(parents=True, exist_ok=True)

    def generate_report_from_excel(
        self,
        excel_path: str,
        user_id: int,
        title: Optional[str] = None,
        template: str = 'excel_analysis',
        formats: List[str] = ['docx', 'pdf']
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report from Excel data

        Args:
            excel_path: Path to Excel file
            user_id: User ID for the report
            title: Optional report title
            template: Template type to use
            formats: List of output formats ('docx', 'pdf')

        Returns:
            Dictionary with generation results
        """
        try:
            # Extract data from Excel
            logger.info(f"Processing Excel file: {excel_path}")
            excel_data = self._process_excel_file(excel_path)

            if not excel_data['success']:
                return {
                    'success': False,
                    'error': excel_data.get('error', 'Failed to process Excel file')
                }

            # Generate report title if not provided
            if not title:
                filename = Path(excel_path).stem
                title = f"Analysis Report - {filename}"

            # Prepare report data
            report_data = self._prepare_report_data(excel_data['data'], title)

            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"report_{timestamp}"

            results = {
                'success': True,
                'title': title,
                'formats': {},
                'metadata': {
                    'source_file': Path(excel_path).name,
                    'generated_at': datetime.now().isoformat(),
                    'template': template,
                    'sheets_processed': len(excel_data['data'].get('sheets', {}))
                }
            }

            # Generate DOCX if requested
            if 'docx' in formats:
                docx_result = self._generate_docx_report(report_data, template, base_filename)
                if docx_result['success']:
                    results['formats']['docx'] = docx_result
                else:
                    logger.error(f"DOCX generation failed: {docx_result['error']}")

            # Generate PDF if requested
            if 'pdf' in formats:
                pdf_result = self._generate_pdf_report(report_data, template, base_filename, results.get('formats', {}).get('docx'))
                if pdf_result['success']:
                    results['formats']['pdf'] = pdf_result
                else:
                    logger.error(f"PDF generation failed: {pdf_result['error']}")

            # Create database record if any format was successful
            if results['formats']:
                report_record = self._create_report_record(results, user_id)
                results['report_id'] = report_record.id

            return results

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return {
                'success': False,
                'error': f"Report generation failed: {str(e)}"
            }

    def _process_excel_file(self, excel_path: str) -> Dict[str, Any]:
        """Process Excel file and extract data"""
        try:
            # Parse Excel file metadata
            parse_result = excel_processing_service.parse_excel(excel_path)

            if not parse_result['success']:
                return parse_result

            # Extract data from each sheet
            sheets_data = {}
            total_rows = 0

            for sheet_name in parse_result['sheet_names']:
                try:
                    # Extract data as DataFrame
                    df = excel_processing_service.extract_data(excel_path, sheet_name, max_rows=1000)

                    if not df.empty:
                        # Get basic statistics
                        stats = self._calculate_sheet_statistics(df)

                        # Prepare sheet data
                        sheets_data[sheet_name] = {
                            'name': sheet_name,
                            'rows': len(df),
                            'columns': list(df.columns),
                            'data': df.head(50).to_dict('records'),  # First 50 rows for preview
                            'statistics': stats,
                            'data_types': excel_processing_service.infer_data_types(df)
                        }

                        total_rows += len(df)

                except Exception as e:
                    logger.warning(f"Error processing sheet '{sheet_name}': {e}")
                    continue

            return {
                'success': True,
                'data': {
                    'sheets': sheets_data,
                    'summary': {
                        'total_sheets': len(sheets_data),
                        'total_rows': total_rows,
                        'processed_at': datetime.now().isoformat()
                    }
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_sheet_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for a DataFrame"""
        try:
            stats = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'null_count': df.isnull().sum().sum(),
                'numeric_columns': [],
                'text_columns': [],
                'date_columns': []
            }

            # Categorize columns by type
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    stats['numeric_columns'].append({
                        'name': col,
                        'mean': float(df[col].mean()) if not df[col].isna().all() else 0,
                        'min': float(df[col].min()) if not df[col].isna().all() else 0,
                        'max': float(df[col].max()) if not df[col].isna().all() else 0
                    })
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    stats['date_columns'].append({
                        'name': col,
                        'earliest': str(df[col].min()) if not df[col].isna().all() else '',
                        'latest': str(df[col].max()) if not df[col].isna().all() else ''
                    })
                else:
                    unique_count = df[col].nunique()
                    stats['text_columns'].append({
                        'name': col,
                        'unique_values': unique_count,
                        'most_common': str(df[col].mode().iloc[0]) if len(df[col].mode()) > 0 else ''
                    })

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {'error': str(e)}

    def _prepare_report_data(self, excel_data: Dict[str, Any], title: str) -> Dict[str, Any]:
        """Prepare data structure for report generation"""
        sheets = excel_data.get('sheets', {})
        summary = excel_data.get('summary', {})

        # Prepare comprehensive report data
        report_data = {
            'title': title,
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'summary': {
                'total_sheets': summary.get('total_sheets', 0),
                'total_rows': summary.get('total_rows', 0),
                'data_quality_score': self._calculate_data_quality(sheets)
            },
            'sheets': [],
            'insights': self._generate_insights(sheets),
            'recommendations': self._generate_recommendations(sheets)
        }

        # Process each sheet
        for sheet_name, sheet_data in sheets.items():
            sheet_info = {
                'name': sheet_name,
                'rows': sheet_data.get('rows', 0),
                'columns': sheet_data.get('columns', []),
                'statistics': sheet_data.get('statistics', {}),
                'data_preview': sheet_data.get('data', [])[:10],  # First 10 rows
                'data_types': sheet_data.get('data_types', {})
            }
            report_data['sheets'].append(sheet_info)

        return report_data

    def _calculate_data_quality(self, sheets: Dict[str, Any]) -> int:
        """Calculate overall data quality score"""
        try:
            if not sheets:
                return 0

            total_score = 0
            sheet_count = 0

            for sheet_data in sheets.values():
                stats = sheet_data.get('statistics', {})
                rows = stats.get('row_count', 0)
                null_count = stats.get('null_count', 0)

                if rows > 0:
                    completeness = max(0, (rows - null_count) / rows)
                    score = int(completeness * 100)
                    total_score += score
                    sheet_count += 1

            return int(total_score / sheet_count) if sheet_count > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 50  # Default score

    def _generate_insights(self, sheets: Dict[str, Any]) -> List[str]:
        """Generate insights from the data"""
        insights = []

        try:
            total_rows = sum(sheet.get('rows', 0) for sheet in sheets.values())
            total_sheets = len(sheets)

            insights.append(f"Dataset contains {total_rows:,} total records across {total_sheets} sheet(s)")

            # Find largest sheet
            if sheets:
                largest_sheet = max(sheets.items(), key=lambda x: x[1].get('rows', 0))
                insights.append(f"'{largest_sheet[0]}' is the largest sheet with {largest_sheet[1].get('rows', 0):,} rows")

            # Data type insights
            numeric_columns = 0
            text_columns = 0

            for sheet_data in sheets.values():
                stats = sheet_data.get('statistics', {})
                numeric_columns += len(stats.get('numeric_columns', []))
                text_columns += len(stats.get('text_columns', []))

            if numeric_columns > 0:
                insights.append(f"Found {numeric_columns} numeric columns suitable for analysis")
            if text_columns > 0:
                insights.append(f"Found {text_columns} text columns for categorical analysis")

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights.append("Data analysis completed successfully")

        return insights

    def _generate_recommendations(self, sheets: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the data"""
        recommendations = []

        try:
            for sheet_name, sheet_data in sheets.items():
                stats = sheet_data.get('statistics', {})
                null_count = stats.get('null_count', 0)
                row_count = stats.get('row_count', 0)

                if null_count > 0 and row_count > 0:
                    null_percentage = (null_count / row_count) * 100
                    if null_percentage > 20:
                        recommendations.append(f"Sheet '{sheet_name}' has {null_percentage:.1f}% missing data - consider data cleaning")

                numeric_cols = len(stats.get('numeric_columns', []))
                if numeric_cols >= 2:
                    recommendations.append(f"Sheet '{sheet_name}' has {numeric_cols} numeric columns - suitable for correlation analysis")

            # General recommendations
            if len(sheets) > 3:
                recommendations.append("Consider consolidating related data into fewer sheets for better organization")

            if not recommendations:
                recommendations.append("Data quality appears good - ready for analysis")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Consider reviewing data structure for optimization opportunities")

        return recommendations

    def _generate_docx_report(self, report_data: Dict[str, Any], template: str, base_filename: str) -> Dict[str, Any]:
        """Generate DOCX report"""
        try:
            docx_filename = f"{base_filename}.docx"
            docx_path = str(self.reports_dir / docx_filename)

            # Use existing report generator with a custom template
            actual_path = create_word_report('excel_analysis', report_data, docx_path)

            file_size = os.path.getsize(actual_path)

            return {
                'success': True,
                'path': actual_path,
                'filename': docx_filename,
                'size': file_size,
                'url': f"/api/reports/download/{docx_filename}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_pdf_report(self, report_data: Dict[str, Any], template: str, base_filename: str, docx_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate PDF report using ConvertAPI"""
        try:
            pdf_filename = f"{base_filename}.pdf"
            pdf_path = str(self.pdfs_dir / pdf_filename)

            # Try ConvertAPI first if DOCX was generated
            if docx_info and convertapi_service.api_key:
                success, message, result_path = convertapi_service.convert_docx_to_pdf(docx_info['path'], pdf_path)

                if success and result_path:
                    file_size = os.path.getsize(result_path)
                    return {
                        'success': True,
                        'path': result_path,
                        'filename': pdf_filename,
                        'size': file_size,
                        'url': f"/api/reports/download/{pdf_filename}",
                        'method': 'convertapi'
                    }
                else:
                    logger.warning(f"ConvertAPI failed: {message}. Falling back to direct PDF generation.")

            # Fallback to direct PDF generation
            actual_path = create_pdf_report('excel_analysis', report_data, pdf_path)
            file_size = os.path.getsize(actual_path)

            return {
                'success': True,
                'path': actual_path,
                'filename': pdf_filename,
                'size': file_size,
                'url': f"/api/reports/download/{pdf_filename}",
                'method': 'reportlab'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_report_record(self, results: Dict[str, Any], user_id: int) -> Report:
        """Create database record for the generated report"""
        try:
            # Determine primary file (prefer PDF, fallback to DOCX)
            primary_format = 'pdf' if 'pdf' in results['formats'] else 'docx'
            primary_file = results['formats'][primary_format]

            report = Report(
                title=results['title'],
                description=f"Generated from Excel file: {results['metadata']['source_file']}",
                file_path=primary_file['path'],
                file_size=primary_file['size'],
                file_format=primary_format,
                generation_status='completed',
                generated_at=datetime.utcnow(),
                created_by=str(user_id),
                data_source=json.dumps(results['metadata']),
                report_type='automated'
            )

            db.session.add(report)
            db.session.commit()

            return report

        except Exception as e:
            logger.error(f"Failed to create report record: {e}")
            db.session.rollback()
            raise

# Global service instance
excel_report_service = ExcelReportService()