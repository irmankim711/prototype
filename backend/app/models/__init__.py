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

# Import template models (renamed to avoid conflicts)
from .template_models import (
    Template as TemplateModel,
    GeneratedReport,
    DataMapping,
    ReportVersion,
    ReportEditSession,
    ExcelUpload
)

# Import Excel file tracking models (for multi-file support)
# These are defined in the parent models.py file
try:
    import importlib
    import sys
    from pathlib import Path

    # Get the models.py file path
    models_file = Path(__file__).parent.parent / 'models.py'

    if models_file.exists():
        # Load the models module dynamically
        spec = importlib.util.spec_from_file_location("excel_models", models_file)
        excel_models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(excel_models)

        # Get the model classes
        ParsedExcelFile = excel_models.ParsedExcelFile
        ExcelTable = excel_models.ExcelTable
    else:
        # Models not found, create placeholder
        ParsedExcelFile = None
        ExcelTable = None
except Exception as e:
    print(f"Warning: Could not import ParsedExcelFile and ExcelTable: {e}")
    ParsedExcelFile = None
    ExcelTable = None

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
