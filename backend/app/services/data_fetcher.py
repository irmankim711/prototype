"""
Data Fetcher Service for Report Generation
Centralized service for fetching data from various sources for reports
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from flask import current_app
from sqlalchemy import text

from .. import db
from ..models import Form, FormSubmission, User
from .data_sources.excel_service import ExcelDataService
# Note: Google Forms service import will be added when available
# from .data_sources.google_forms_service import GoogleFormsService

logger = logging.getLogger(__name__)


class DataFetcher:
    """Service for fetching data from various sources for report generation"""

    def __init__(self):
        self.excel_service = ExcelDataService()
        # self.google_forms_service = GoogleFormsService()  # Will be added when available

    def fetch_data_by_source_type(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data based on source type configuration

        Args:
            source_config: Configuration specifying data source and parameters

        Returns:
            Dictionary containing fetched data and metadata
        """
        source_type = source_config.get('type', '').lower()

        try:
            if source_type == 'form':
                return self.fetch_form_data(source_config)
            elif source_type == 'excel':
                return self.fetch_excel_data(source_config)
            elif source_type == 'google_forms':
                return self.fetch_google_forms_data(source_config)
            elif source_type == 'database':
                return self.fetch_database_data(source_config)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")

        except Exception as e:
            logger.error(f"Error fetching data for source type {source_type}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'metadata': {'source_config': source_config}
            }

    def fetch_form_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch form submission data from database

        Args:
            config: Configuration with form_id and optional filters

        Returns:
            Dictionary with form submissions and metadata
        """
        try:
            form_id = config.get('form_id')
            if not form_id:
                raise ValueError("form_id is required for form data source")

            # Get form details
            form = Form.query.get(form_id)
            if not form:
                raise ValueError(f"Form with ID {form_id} not found")

            # Build query with optional filters
            query = FormSubmission.query.filter_by(form_id=form_id)

            # Apply date filters if provided
            if config.get('start_date'):
                start_date = datetime.fromisoformat(config['start_date'])
                query = query.filter(FormSubmission.submitted_at >= start_date)

            if config.get('end_date'):
                end_date = datetime.fromisoformat(config['end_date'])
                query = query.filter(FormSubmission.submitted_at <= end_date)

            # Apply limit if provided
            limit = config.get('limit', 1000)
            if limit:
                query = query.limit(limit)

            # Fetch submissions
            submissions = query.order_by(FormSubmission.submitted_at.desc()).all()

            # Convert submissions to structured data
            data = []
            for submission in submissions:
                submission_data = {
                    'id': submission.id,
                    'submitted_at': submission.submitted_at.isoformat(),
                    'status': submission.status,
                    'user_id': submission.submitter_id
                }

                # Parse submission data
                if submission.data:
                    if isinstance(submission.data, str):
                        import json
                        parsed_data = json.loads(submission.data)
                    else:
                        parsed_data = submission.data

                    submission_data.update(parsed_data)

                data.append(submission_data)

            return {
                'success': True,
                'data': data,
                'metadata': {
                    'form_id': form_id,
                    'form_title': form.title,
                    'form_description': form.description,
                    'total_submissions': len(data),
                    'fetched_at': datetime.utcnow().isoformat(),
                    'date_range': {
                        'start': config.get('start_date'),
                        'end': config.get('end_date')
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error fetching form data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'metadata': {'config': config}
            }

    def fetch_excel_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from Excel files

        Args:
            config: Configuration with source_id or file_path

        Returns:
            Dictionary with Excel data and metadata
        """
        try:
            source_id = config.get('source_id')
            file_path = config.get('file_path')

            if source_id:
                # Use Excel service to get data
                response = self.excel_service.get_preview(source_id, limit=config.get('limit', 1000))
                if response.success:
                    return {
                        'success': True,
                        'data': response.data.get('records', []),
                        'metadata': {
                            'source_id': source_id,
                            'columns': response.data.get('columns', []),
                            'fetched_at': datetime.utcnow().isoformat(),
                            **response.metadata
                        }
                    }
                else:
                    raise ValueError(f"Excel service error: {response.message}")

            elif file_path:
                # Direct file access
                if not os.path.exists(file_path):
                    raise ValueError(f"Excel file not found: {file_path}")

                # Read Excel file
                sheet_name = config.get('sheet_name', 0)
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Convert to records
                records = df.to_dict('records')

                # Clean NaN values
                for record in records:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None

                return {
                    'success': True,
                    'data': records,
                    'metadata': {
                        'file_path': file_path,
                        'sheet_name': sheet_name,
                        'row_count': len(df),
                        'column_count': len(df.columns),
                        'columns': list(df.columns),
                        'fetched_at': datetime.utcnow().isoformat()
                    }
                }

            else:
                raise ValueError("Either source_id or file_path is required for Excel data source")

        except Exception as e:
            logger.error(f"Error fetching Excel data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'metadata': {'config': config}
            }

    def fetch_google_forms_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from Google Forms

        Args:
            config: Configuration with form_id

        Returns:
            Dictionary with Google Forms data and metadata
        """
        try:
            # Google Forms integration will be implemented later
            return {
                'success': False,
                'error': 'Google Forms integration not yet implemented',
                'data': [],
                'metadata': {'config': config}
            }

        except Exception as e:
            logger.error(f"Error fetching Google Forms data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'metadata': {'config': config}
            }

    def fetch_database_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data using custom database query

        Args:
            config: Configuration with query and optional parameters

        Returns:
            Dictionary with query results and metadata
        """
        try:
            query = config.get('query')
            if not query:
                raise ValueError("query is required for database data source")

            # Validate query (basic security check)
            query_lower = query.lower().strip()
            if not query_lower.startswith('select'):
                raise ValueError("Only SELECT queries are allowed")

            # Prevent dangerous operations
            dangerous_keywords = ['delete', 'update', 'insert', 'drop', 'alter', 'create']
            for keyword in dangerous_keywords:
                if keyword in query_lower:
                    raise ValueError(f"Query contains forbidden keyword: {keyword}")

            # Execute query
            result = db.session.execute(text(query))

            # Convert to list of dictionaries
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result.fetchall()]

            return {
                'success': True,
                'data': data,
                'metadata': {
                    'query': query,
                    'row_count': len(data),
                    'columns': list(columns),
                    'fetched_at': datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error fetching database data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'metadata': {'config': config}
            }

    def get_data_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for fetched data

        Args:
            data: List of data records

        Returns:
            Dictionary with summary statistics
        """
        if not data:
            return {'record_count': 0, 'columns': []}

        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data)

            summary = {
                'record_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'column_types': {},
                'numeric_summary': {},
                'categorical_summary': {}
            }

            # Analyze each column
            for col in df.columns:
                col_data = df[col]

                # Determine column type
                if pd.api.types.is_numeric_dtype(col_data):
                    summary['column_types'][col] = 'numeric'
                    summary['numeric_summary'][col] = {
                        'min': float(col_data.min()) if not col_data.empty else None,
                        'max': float(col_data.max()) if not col_data.empty else None,
                        'mean': float(col_data.mean()) if not col_data.empty else None,
                        'std': float(col_data.std()) if not col_data.empty else None,
                        'null_count': int(col_data.isnull().sum())
                    }
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    summary['column_types'][col] = 'datetime'
                else:
                    summary['column_types'][col] = 'categorical'
                    value_counts = col_data.value_counts()
                    summary['categorical_summary'][col] = {
                        'unique_count': int(col_data.nunique()),
                        'null_count': int(col_data.isnull().sum()),
                        'top_values': value_counts.head(5).to_dict()
                    }

            return summary

        except Exception as e:
            logger.error(f"Error generating data summary: {str(e)}")
            return {
                'record_count': len(data),
                'error': str(e)
            }


# Create singleton instance
data_fetcher = DataFetcher()