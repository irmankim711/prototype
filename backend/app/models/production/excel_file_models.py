"""
Excel File Tracking Models
Models for tracking uploaded and parsed Excel files for multi-file support.
"""

from datetime import datetime
from typing import Dict, Any
from ... import db


class ParsedExcelFile(db.Model):
    """
    Model for tracking uploaded and parsed Excel files for multi-file support.
    Enables users to upload multiple Excel files and select from them for report generation.
    """
    __tablename__ = 'parsed_excel_files'

    id = db.Column(db.String(64), primary_key=True)  # UUID
    user_id = db.Column(db.String(64), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    status = db.Column(db.String(50), default='completed')  # completed, processing, error
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Parsing metadata
    tables_count = db.Column(db.Integer, default=0)
    total_rows = db.Column(db.Integer, default=0)
    total_columns = db.Column(db.Integer, default=0)
    sheets_processed = db.Column(db.Integer, default=0)

    # Additional metadata stored as JSON (using file_metadata to avoid SQLAlchemy reserved word)
    file_metadata = db.Column('metadata', db.JSON)

    # Error tracking
    error_message = db.Column(db.Text)

    def __init__(self, **kwargs):
        """ParsedExcelFile constructor"""
        super(ParsedExcelFile, self).__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'status': self.status,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'tables_count': self.tables_count,
            'total_rows': self.total_rows,
            'total_columns': self.total_columns,
            'sheets_processed': self.sheets_processed,
            'metadata': self.file_metadata,  # Return as 'metadata' in API
            'error_message': self.error_message
        }


class ExcelTable(db.Model):
    """
    Model for storing individual tables extracted from Excel files.
    Each Excel file can contain multiple sheets/tables.
    """
    __tablename__ = 'excel_tables'

    id = db.Column(db.String(64), primary_key=True)  # UUID
    parsed_file_id = db.Column(db.String(64), db.ForeignKey('parsed_excel_files.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sheet_name = db.Column(db.String(255))
    row_count = db.Column(db.Integer, default=0)
    column_count = db.Column(db.Integer, default=0)

    # Table structure
    headers = db.Column(db.JSON)  # List of column headers
    data_types = db.Column(db.JSON)  # List of inferred data types
    table_range = db.Column(db.String(50))  # Excel range (e.g., "A1:D100")

    # Optional: Store preview data (first few rows)
    data = db.Column(db.JSON)  # Full table data or preview

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        """ExcelTable constructor"""
        super(ExcelTable, self).__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'parsed_file_id': self.parsed_file_id,
            'name': self.name,
            'sheet_name': self.sheet_name,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'headers': self.headers,
            'data_types': self.data_types,
            'table_range': self.table_range,
            'has_data': self.data is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
