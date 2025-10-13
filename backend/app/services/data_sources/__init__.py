"""
NextGen Data Sources Services Package

This package provides a unified interface for accessing data from multiple sources
including Excel uploads, Google Forms, custom forms, and external APIs.
"""

from .base_service import BaseDataSourceService
from .manager import DataSourceManager
from .excel_service import ExcelDataService
from .forms_service import FormsDataService
from .google_forms_service import GoogleFormsDataService

__all__ = [
    'BaseDataSourceService',
    'DataSourceManager', 
    'ExcelDataService',
    'FormsDataService',
    'GoogleFormsDataService'
]