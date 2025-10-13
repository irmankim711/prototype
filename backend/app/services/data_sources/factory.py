"""
Data Source Service Factory

Factory for creating and configuring the data source manager with all services.
Provides dependency injection and service registration.
"""

from typing import Optional
import logging

from .manager import DataSourceManager
from .excel_service import ExcelDataService
from .forms_service import FormsDataService
from .google_forms_service import GoogleFormsDataService
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global instance
_data_source_manager: Optional[DataSourceManager] = None


def create_data_source_manager() -> DataSourceManager:
    """
    Create and configure a new DataSourceManager instance with all services.
    
    Returns:
        Configured DataSourceManager instance
    """
    manager = DataSourceManager()
    
    # Register all data source services
    try:
        # Excel data service
        excel_service = ExcelDataService()
        manager.register_service(excel_service)
        logger.info("Registered Excel data service")
        
        # Forms data service
        forms_service = FormsDataService()
        manager.register_service(forms_service)
        logger.info("Registered Forms data service")
        
        # Google Forms data service
        google_forms_service = GoogleFormsDataService()
        manager.register_service(google_forms_service)
        logger.info("Registered Google Forms data service")
        
        logger.info(f"Data source manager initialized with {len(manager.get_available_services())} services")
        
    except Exception as e:
        logger.error(f"Error initializing data source services: {str(e)}")
        raise
    
    return manager


def get_data_source_manager() -> DataSourceManager:
    """
    Get the global DataSourceManager instance (singleton pattern).
    Creates the instance if it doesn't exist.
    
    Returns:
        Global DataSourceManager instance
    """
    global _data_source_manager
    
    if _data_source_manager is None:
        _data_source_manager = create_data_source_manager()
        logger.info("Created global data source manager instance")
    
    return _data_source_manager


def reset_data_source_manager() -> None:
    """
    Reset the global DataSourceManager instance.
    Useful for testing or when configuration changes.
    """
    global _data_source_manager
    _data_source_manager = None
    logger.info("Reset global data source manager instance")


def initialize_data_sources() -> DataSourceManager:
    """
    Initialize the data source system.
    This should be called during application startup.
    
    Returns:
        Initialized DataSourceManager instance
    """
    try:
        manager = get_data_source_manager()
        logger.info("Data source system initialized successfully")
        return manager
    except Exception as e:
        logger.error(f"Failed to initialize data source system: {str(e)}")
        raise