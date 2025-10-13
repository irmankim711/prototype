"""
Extended Template Models for Template-Based Report Generation
Extends existing ReportTemplate model with additional functionality
"""
from .. import db
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

class ReportStatus(Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EDITING = "editing"

class Template(db.Model):
    """
    Extended Template model for template-based report generation
    Works alongside existing ReportTemplate model
    """
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    template_content = db.Column(db.Text, nullable=False)  # HTML/Jinja2 template
    variables = db.Column(db.JSON)  # Template variable definitions
    preview_image = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Template metadata
    template_type = db.Column(db.String(50), default='report')  # report, document, form
    file_path = db.Column(db.String(500))  # Path to template file if file-based
    supports_excel = db.Column(db.Boolean, default=True)
    required_fields = db.Column(db.JSON)  # Required data fields
    
    # Relationships
    reports = db.relationship('GeneratedReport', backref='template', lazy=True)
    data_mappings = db.relationship('DataMapping', backref='template', lazy=True)
    
    def __init__(self, **kwargs):
        super(Template, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'template_type': self.template_type,
            'variables': self.variables,
            'preview_image': self.preview_image,
            'supports_excel': self.supports_excel,
            'required_fields': self.required_fields,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GeneratedReport(db.Model):
    """
    Generated Report model for template-based reports
    Extends existing Report model functionality
    """
    __tablename__ = 'generated_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'))
    excel_file_path = db.Column(db.String(500))
    data_mapping_id = db.Column(db.Integer, db.ForeignKey('data_mappings.id'))
    content = db.Column(db.Text)  # Generated report content
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.DRAFT)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generation_task_id = db.Column(db.String(255))  # Celery task ID
    
    # Generation metadata
    generation_started_at = db.Column(db.DateTime)
    generation_completed_at = db.Column(db.DateTime)
    generation_duration = db.Column(db.Integer)  # Duration in seconds
    error_message = db.Column(db.Text)
    
    # File outputs
    pdf_path = db.Column(db.String(500))
    docx_path = db.Column(db.String(500))
    html_path = db.Column(db.String(500))
    
    # Relationships
    versions = db.relationship('ReportVersion', backref='report', lazy=True, cascade='all, delete-orphan')
    data_mapping = db.relationship('DataMapping', backref='reports')
    
    def __init__(self, **kwargs):
        super(GeneratedReport, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_id': self.template_id,
            'excel_file_path': self.excel_file_path,
            'data_mapping_id': self.data_mapping_id,
            'status': self.status.value if self.status else None,
            'content': self.content,
            'generation_task_id': self.generation_task_id,
            'generation_started_at': self.generation_started_at.isoformat() if self.generation_started_at else None,
            'generation_completed_at': self.generation_completed_at.isoformat() if self.generation_completed_at else None,
            'generation_duration': self.generation_duration,
            'error_message': self.error_message,
            'pdf_path': self.pdf_path,
            'docx_path': self.docx_path,
            'html_path': self.html_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DataMapping(db.Model):
    """
    Data Mapping model for Excel-to-template field mappings
    """
    __tablename__ = 'data_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'))
    excel_file_path = db.Column(db.String(500))
    sheet_name = db.Column(db.String(100))
    field_mappings = db.Column(db.JSON)  # Excel column to template variable mapping
    transformations = db.Column(db.JSON)  # Data transformation rules
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Validation metadata
    is_validated = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.JSON)
    last_validated_at = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(DataMapping, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'template_id': self.template_id,
            'excel_file_path': self.excel_file_path,
            'sheet_name': self.sheet_name,
            'field_mappings': self.field_mappings,
            'transformations': self.transformations,
            'is_validated': self.is_validated,
            'validation_errors': self.validation_errors,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ReportVersion(db.Model):
    """
    Report Version model for version control and change tracking
    """
    __tablename__ = 'report_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('generated_reports.id'))
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    changes_summary = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Version metadata
    is_current = db.Column(db.Boolean, default=False)
    content_hash = db.Column(db.String(64))  # SHA256 hash of content
    change_type = db.Column(db.String(50))  # auto_save, manual_save, revert
    
    def __init__(self, **kwargs):
        super(ReportVersion, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'version_number': self.version_number,
            'content': self.content,
            'changes_summary': self.changes_summary,
            'is_current': self.is_current,
            'content_hash': self.content_hash,
            'change_type': self.change_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ReportEditSession(db.Model):
    """
    Report Edit Session model for tracking active report editing sessions
    """
    __tablename__ = 'report_edit_sessions'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('generated_reports.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_token = db.Column(db.String(255), unique=True, nullable=False)

    # Session metadata
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Edit state
    current_content = db.Column(db.Text)
    changes_count = db.Column(db.Integer, default=0)
    auto_save_enabled = db.Column(db.Boolean, default=True)
    last_auto_save = db.Column(db.DateTime)

    # Browser/client info
    client_info = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))

    def __init__(self, **kwargs):
        super(ReportEditSession, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'changes_count': self.changes_count,
            'auto_save_enabled': self.auto_save_enabled,
            'last_auto_save': self.last_auto_save.isoformat() if self.last_auto_save else None,
            'client_info': self.client_info
        }

class ExcelUpload(db.Model):
    """
    Excel Upload model for tracking uploaded Excel files
    """
    __tablename__ = 'excel_uploads'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Excel metadata
    sheet_names = db.Column(db.JSON)  # List of sheet names
    column_headers = db.Column(db.JSON)  # Column headers per sheet
    row_count = db.Column(db.Integer)
    processed = db.Column(db.Boolean, default=False)
    processing_errors = db.Column(db.JSON)

    # Relationships
    data_mappings = db.relationship('DataMapping',
                                  primaryjoin='ExcelUpload.file_path == DataMapping.excel_file_path',
                                  foreign_keys='DataMapping.excel_file_path',
                                  lazy=True)

    def __init__(self, **kwargs):
        super(ExcelUpload, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'sheet_names': self.sheet_names,
            'column_headers': self.column_headers,
            'row_count': self.row_count,
            'processed': self.processed,
            'processing_errors': self.processing_errors,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }