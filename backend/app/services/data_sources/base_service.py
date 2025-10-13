"""
Base Data Source Service

Abstract base class that defines the interface for all data source services.
Provides common functionality and ensures consistent behavior across all data sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataSourceRecord:
    """Represents a single data record from any source"""
    id: str
    fields: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DataSourceColumn:
    """Represents a column/field definition from a data source"""
    id: str
    name: str
    type: str  # 'dimension' or 'measure'
    data_type: str  # 'text', 'numerical', 'categorical', 'temporal'
    sample_values: List[Any]
    description: Optional[str] = None
    usage_count: int = 0


@dataclass
class DataSourcePagination:
    """Pagination information for data source results"""
    page: int
    per_page: int
    total: int
    has_next: bool
    has_prev: bool


@dataclass
class DataSourceResponse:
    """Standard response format for all data source operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseDataSourceService(ABC):
    """
    Abstract base class for all data source services.
    
    Defines the standard interface that all data source implementations must follow.
    Provides common functionality for error handling, logging, and response formatting.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

    @abstractmethod
    def get_data(self, source_id: str, params: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """
        Retrieve data records from the data source.
        
        Args:
            source_id: Unique identifier for the specific data source
            params: Optional parameters for filtering, pagination, etc.
            
        Returns:
            DataSourceResponse with records, pagination, and metadata
        """
        pass

    @abstractmethod
    def get_fields(self, source_id: str) -> DataSourceResponse:
        """
        Get field/column definitions for the data source.
        
        Args:
            source_id: Unique identifier for the specific data source
            
        Returns:
            DataSourceResponse with field definitions
        """
        pass

    @abstractmethod
    def get_preview(self, source_id: str, limit: int = 10) -> DataSourceResponse:
        """
        Get a preview sample of data from the source.
        
        Args:
            source_id: Unique identifier for the specific data source
            limit: Maximum number of records to return
            
        Returns:
            DataSourceResponse with sample records
        """
        pass

    @abstractmethod
    def refresh_data(self, source_id: str) -> DataSourceResponse:
        """
        Refresh/reload data from the source.
        
        Args:
            source_id: Unique identifier for the specific data source
            
        Returns:
            DataSourceResponse with refresh status
        """
        pass

    @abstractmethod
    def get_status(self, source_id: str) -> DataSourceResponse:
        """
        Get connection and health status for the data source.
        
        Args:
            source_id: Unique identifier for the specific data source
            
        Returns:
            DataSourceResponse with status information
        """
        pass

    @abstractmethod
    def validate_source(self, source_config: Dict[str, Any]) -> DataSourceResponse:
        """
        Validate data source configuration and connectivity.
        
        Args:
            source_config: Configuration parameters for the data source
            
        Returns:
            DataSourceResponse with validation results
        """
        pass

    def _create_success_response(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """Create a standardized success response"""
        return DataSourceResponse(
            success=True,
            data=data,
            metadata=metadata or {}
        )

    def _create_error_response(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """Create a standardized error response"""
        error_data = {
            'code': error_code,
            'message': message,
            'service': self.service_name
        }
        if details:
            error_data['details'] = details

        self.logger.error(f"Error in {self.service_name}: {error_code} - {message}")
        
        return DataSourceResponse(
            success=False,
            error=error_data
        )

    def _parse_pagination_params(self, params: Optional[Dict[str, Any]]) -> Dict[str, int]:
        """Parse and validate pagination parameters"""
        if not params:
            params = {}
            
        page = max(1, int(params.get('page', 1)))
        per_page = min(1000, max(1, int(params.get('per_page', 100))))
        
        return {
            'page': page,
            'per_page': per_page,
            'offset': (page - 1) * per_page
        }

    def _create_pagination_info(self, page: int, per_page: int, total: int) -> DataSourcePagination:
        """Create pagination information object"""
        return DataSourcePagination(
            page=page,
            per_page=per_page,
            total=total,
            has_next=page * per_page < total,
            has_prev=page > 1
        )

    def _normalize_field_type(self, field_type: str, sample_values: List[Any]) -> tuple[str, str]:
        """
        Normalize field type and data type based on field characteristics.
        
        Returns:
            tuple: (type, data_type) where type is 'dimension'/'measure' and 
                   data_type is 'text'/'numerical'/'categorical'/'temporal'
        """
        field_type = field_type.lower() if field_type else ''
        
        # Determine if it's a dimension or measure
        if field_type in ['select', 'radio', 'checkbox', 'choice']:
            type_category = 'dimension'
            data_type = 'categorical'
        elif field_type in ['number', 'integer', 'float', 'decimal']:
            type_category = 'measure'
            data_type = 'numerical'
        elif field_type in ['date', 'datetime', 'time']:
            type_category = 'dimension'
            data_type = 'temporal'
        else:
            # Analyze sample values to determine type
            if sample_values:
                numeric_count = sum(1 for v in sample_values if isinstance(v, (int, float)))
                if numeric_count > len(sample_values) * 0.8:
                    type_category = 'measure'
                    data_type = 'numerical'
                else:
                    type_category = 'dimension'
                    data_type = 'text'
            else:
                type_category = 'dimension'
                data_type = 'text'
                
        return type_category, data_type

    def supports_source(self, source_id: str) -> bool:
        """
        Check if this service supports the given source ID.
        Should be implemented by subclasses to define their supported source patterns.
        """
        return False