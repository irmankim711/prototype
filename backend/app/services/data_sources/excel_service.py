"""
Excel Data Source Service

Handles data access from Excel file uploads.
Supports both excel-upload (general) and excel_{filename} (specific file) sources.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import os
import re
from pathlib import Path
from datetime import datetime
from flask import current_app

try:
    import openpyxl
    from openpyxl.utils import get_column_letter
    import pandas as pd
    import numpy as np
    EXCEL_LIBRARIES_AVAILABLE = True
except ImportError as e:
    EXCEL_LIBRARIES_AVAILABLE = False
    logging.warning(f"Excel processing libraries not available: {e}")

from .base_service import BaseDataSourceService, DataSourceResponse, DataSourceRecord, DataSourceColumn
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExcelDataService(BaseDataSourceService):
    """
    Service for accessing data from Excel file uploads.
    
    Supports source IDs:
    - 'excel-upload': General Excel upload data source
    - 'excel_{filename}': Specific Excel file by filename
    """

    def __init__(self):
        super().__init__('excel_data_service')
        self.service_type = 'excel'
        self.supported_extensions = ['.xlsx', '.xls', '.xlsm']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.upload_path = os.path.join(
            current_app.root_path if current_app else os.getcwd(),
            'static', 'uploads', 'excel'
        )

    def supports_source(self, source_id: str) -> bool:
        """Check if this service supports the given source ID"""
        return (source_id == 'excel-upload' or
                source_id.startswith('excel_') or
                source_id == 'mock-excel-1')

    def get_data(self, source_id: str, params: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """Get data records from Excel source"""
        try:
            # Use the preview method to get data with optional limit
            limit = params.get('limit', 1000) if params else 1000
            return self.get_preview(source_id, limit)
        except Exception as e:
            logger.error(f"Error getting data for Excel source {source_id}: {str(e)}")
            return self._create_error_response(
                'DATA_ERROR',
                f'Failed to get data from Excel source: {str(e)}',
                {'source_id': source_id, 'error': str(e)}
            )

    def get_fields(self, source_id: str) -> DataSourceResponse:
        """Get field definitions for Excel data source"""
        try:
            # Parse source_id to get file path
            file_path = self._get_excel_file_path(source_id)
            if not file_path or not os.path.exists(file_path):
                return self._create_error_response(
                    'FILE_NOT_FOUND',
                    f'Excel file not found for source: {source_id}',
                    {'source_id': source_id}
                )

            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Generate field definitions
            fields = []
            for col_name in df.columns:
                col_data = df[col_name]

                # Determine field type
                field_type = 'measure' if pd.api.types.is_numeric_dtype(col_data) else 'dimension'

                # Determine data type
                if pd.api.types.is_numeric_dtype(col_data):
                    data_type = 'numerical'
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    data_type = 'temporal'
                elif pd.api.types.is_bool_dtype(col_data):
                    data_type = 'boolean'
                else:
                    # Check if it's categorical by unique value ratio
                    unique_ratio = col_data.nunique() / len(col_data) if len(col_data) > 0 else 1
                    data_type = 'categorical' if unique_ratio < 0.5 else 'text'

                # Get sample values
                sample_values = col_data.dropna().head(5).tolist()

                fields.append({
                    'id': self._sanitize_field_id(col_name),
                    'name': str(col_name),
                    'type': field_type,
                    'dataType': data_type,
                    'sampleValues': sample_values,
                    'usageCount': 0,
                    'description': f'Column from Excel: {col_name}'
                })

            return DataSourceResponse(
                success=True,
                data={'fields': fields},
                message=f'Retrieved {len(fields)} fields from Excel file',
                metadata={
                    'source_id': source_id,
                    'file_path': file_path,
                    'row_count': len(df),
                    'column_count': len(df.columns)
                }
            )

        except Exception as e:
            logger.error(f"Error getting fields for Excel source {source_id}: {str(e)}")
            return self._create_error_response(
                'PROCESSING_ERROR',
                f'Failed to extract fields from Excel file: {str(e)}',
                {'source_id': source_id, 'error': str(e)}
            )

    def get_preview(self, source_id: str, limit: int = 10) -> DataSourceResponse:
        """Get preview sample of Excel data"""
        try:
            # Parse source_id to get file path
            file_path = self._get_excel_file_path(source_id)
            if not file_path or not os.path.exists(file_path):
                return self._create_error_response(
                    'FILE_NOT_FOUND',
                    f'Excel file not found for source: {source_id}',
                    {'source_id': source_id}
                )

            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Get preview data
            preview_df = df.head(limit)

            # Convert to records format
            records = []
            for _, row in preview_df.iterrows():
                record = {}
                for col in preview_df.columns:
                    value = row[col]
                    # Handle NaN values
                    if pd.isna(value):
                        record[col] = None
                    elif isinstance(value, (np.integer, np.floating)):
                        record[col] = float(value) if pd.api.types.is_float_dtype(type(value)) else int(value)
                    else:
                        record[col] = str(value)
                records.append(record)

            # Get column info
            columns = [
                DataSourceColumn(
                    id=self._sanitize_field_id(col),
                    name=str(col),
                    type=self._infer_column_type(df[col])
                )
                for col in df.columns
            ]

            return DataSourceResponse(
                success=True,
                data={'records': records, 'columns': [col.__dict__ for col in columns]},
                message=f'Preview of {len(records)} records from Excel file',
                metadata={
                    'source_id': source_id,
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'preview_rows': len(records)
                }
            )

        except Exception as e:
            logger.error(f"Error getting preview for Excel source {source_id}: {str(e)}")
            return self._create_error_response(
                'PROCESSING_ERROR',
                f'Failed to generate preview from Excel file: {str(e)}',
                {'source_id': source_id, 'error': str(e)}
            )

    def refresh_data(self, source_id: str) -> DataSourceResponse:
        """Refresh Excel data (re-parse files)"""
        try:
            # Parse source_id to get file path
            file_path = self._get_excel_file_path(source_id)
            if not file_path or not os.path.exists(file_path):
                return self._create_error_response(
                    'FILE_NOT_FOUND',
                    f'Excel file not found for source: {source_id}',
                    {'source_id': source_id}
                )

            # Clear any cached data (if implemented)
            # self._clear_cache(source_id)

            # Re-read and validate the file
            df = pd.read_excel(file_path, sheet_name=0)

            # Get file stats
            file_stats = os.stat(file_path)

            return DataSourceResponse(
                success=True,
                data={
                    'refreshed': True,
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'file_size': file_stats.st_size,
                    'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                },
                message='Excel data refreshed successfully',
                metadata={
                    'source_id': source_id,
                    'file_path': file_path
                }
            )

        except Exception as e:
            logger.error(f"Error refreshing Excel source {source_id}: {str(e)}")
            return self._create_error_response(
                'REFRESH_ERROR',
                f'Failed to refresh Excel data: {str(e)}',
                {'source_id': source_id, 'error': str(e)}
            )

    def get_status(self, source_id: str) -> DataSourceResponse:
        """Get status of Excel data source"""
        try:
            # Parse source_id to get file path
            file_path = self._get_excel_file_path(source_id)

            if not file_path or not os.path.exists(file_path):
                return DataSourceResponse(
                    success=True,
                    data={'status': 'disconnected', 'available': False},
                    message='Excel file not found',
                    metadata={'source_id': source_id}
                )

            # Check file accessibility
            try:
                # Try to open the file
                with pd.ExcelFile(file_path) as xls:
                    sheet_names = xls.sheet_names

                file_stats = os.stat(file_path)

                return DataSourceResponse(
                    success=True,
                    data={
                        'status': 'connected',
                        'available': True,
                        'sheets': sheet_names,
                        'file_size': file_stats.st_size,
                        'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    },
                    message='Excel data source is available',
                    metadata={'source_id': source_id, 'file_path': file_path}
                )

            except Exception as access_error:
                return DataSourceResponse(
                    success=True,
                    data={'status': 'error', 'available': False},
                    message=f'Excel file exists but cannot be accessed: {str(access_error)}',
                    metadata={'source_id': source_id}
                )

        except Exception as e:
            logger.error(f"Error checking status for Excel source {source_id}: {str(e)}")
            return self._create_error_response(
                'STATUS_ERROR',
                f'Failed to check Excel status: {str(e)}',
                {'source_id': source_id, 'error': str(e)}
            )

    def validate_source(self, source_config: Dict[str, Any]) -> DataSourceResponse:
        """Validate Excel data source configuration"""
        try:
            # Extract file path from config
            file_path = source_config.get('file_path') or source_config.get('path')

            if not file_path:
                return DataSourceResponse(
                    success=False,
                    data={'valid': False},
                    message='File path is required in configuration',
                    metadata={'config': source_config}
                )

            # Check file existence
            if not os.path.exists(file_path):
                return DataSourceResponse(
                    success=False,
                    data={'valid': False},
                    message='File does not exist',
                    metadata={'file_path': file_path}
                )

            # Check file extension
            ext = Path(file_path).suffix.lower()
            if ext not in self.supported_extensions:
                return DataSourceResponse(
                    success=False,
                    data={'valid': False},
                    message=f'Unsupported file extension: {ext}',
                    metadata={'supported': self.supported_extensions}
                )

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return DataSourceResponse(
                    success=False,
                    data={'valid': False},
                    message=f'File size exceeds maximum allowed ({self.max_file_size} bytes)',
                    metadata={'file_size': file_size}
                )

            # Try to read the file
            try:
                df = pd.read_excel(file_path, sheet_name=0, nrows=1)

                return DataSourceResponse(
                    success=True,
                    data={
                        'valid': True,
                        'columns': list(df.columns),
                        'file_size': file_size
                    },
                    message='Excel source configuration is valid',
                    metadata={'file_path': file_path}
                )

            except Exception as read_error:
                return DataSourceResponse(
                    success=False,
                    data={'valid': False},
                    message=f'File cannot be read as Excel: {str(read_error)}',
                    metadata={'file_path': file_path}
                )

        except Exception as e:
            logger.error(f"Error validating Excel source config: {str(e)}")
            return self._create_error_response(
                'VALIDATION_ERROR',
                f'Failed to validate Excel configuration: {str(e)}',
                {'config': source_config, 'error': str(e)}
            )

    # Helper methods
    def _get_excel_file_path(self, source_id: str) -> Optional[str]:
        """Extract file path from source ID"""
        if source_id == 'excel-upload':
            # Get the most recent Excel file
            try:
                files = [f for f in os.listdir(self.upload_path)
                        if f.endswith(tuple(self.supported_extensions))]
                if files:
                    # Sort by modification time
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(self.upload_path, x)), reverse=True)
                    return os.path.join(self.upload_path, files[0])
            except Exception as e:
                logger.error(f"Error finding Excel files: {str(e)}")
                return None

        elif source_id.startswith('excel_'):
            # Extract filename from source_id
            filename_parts = source_id[6:].split('_')

            # Try to find the file
            for file in os.listdir(self.upload_path):
                if all(part in file for part in filename_parts):
                    return os.path.join(self.upload_path, file)

        return None

    def _sanitize_field_id(self, field_name: str) -> str:
        """Sanitize field name to create valid ID"""
        # Replace spaces and special characters
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(field_name))
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'field_' + sanitized
        return sanitized.lower() or 'field'

    def _infer_column_type(self, column_data) -> str:
        """Infer column data type"""
        if pd.api.types.is_numeric_dtype(column_data):
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(column_data):
            return 'datetime'
        elif pd.api.types.is_bool_dtype(column_data):
            return 'boolean'
        else:
            return 'text'