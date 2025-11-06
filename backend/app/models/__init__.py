"""
Main Models Package - Imports all models from production subdirectory
"""

# Import db from main app
from .. import db

# Import all models from production subdirectory
from .production.user_models import User, UserToken, UserSession
from .production.program_models import Program, Participant, AttendanceRecord
from .production.form_integration_models import FormIntegration, FormResponse
# Temporarily commented out to fix relationship errors
from .production.forms import Form, FormSubmission, FormQRCode, FormAccessCode, QuickAccessToken
from .production.files import File
from .production.report_models import Report, ReportTemplate
from .production.permissions import UserRole, Permission
from .production.excel_file_models import ParsedExcelFile, ExcelTable

# Import template models (renamed to avoid conflicts)
from .template_models import (
    Template as TemplateModel,
    GeneratedReport,
    DataMapping,
    ReportVersion,
    ReportEditSession,
    ExcelUpload
)

__all__ = [
    'db',
    'User', 'UserToken', 'UserSession',
    'Program', 'Participant', 'AttendanceRecord',
    'FormIntegration', 'FormResponse',
    'Form', 'FormSubmission', 'FormQRCode', 'FormAccessCode', 'QuickAccessToken',
    'File',
    'Report', 'ReportTemplate',
    'UserRole', 'Permission',
    'TemplateModel', 'GeneratedReport', 'DataMapping', 'ReportVersion',
    'ReportEditSession', 'ExcelUpload',
    'ParsedExcelFile', 'ExcelTable'
]
