"""
Configuration for Enhanced Excel Service
Defines various configurations for different Excel generation scenarios
"""

from typing import Dict, Any

# Default configuration for standard Excel generation
DEFAULT_EXCEL_CONFIG = {
    'max_chunk_size': 1000,        # Process 1000 records at a time
    'max_memory_mb': 512,          # Limit memory usage to 512MB
    'validation_enabled': True,     # Enable Excel output validation
    'progress_callback': None,      # Progress callback function
    'include_charts': False,        # Include charts in Excel
    'auto_adjust_columns': True,    # Auto-adjust column widths
    'table_formatting': True,       # Apply table formatting
    'alternate_row_colors': True,   # Use alternating row colors
    'header_styling': True,         # Apply header styling
    'date_formatting': True,        # Format date fields
    'number_formatting': True,      # Format number fields
    'error_handling': 'continue',   # 'continue', 'stop', 'log_only'
    'sanitize_field_names': True,   # Clean field names for Excel
    'max_field_name_length': 50,    # Maximum field name length
    'compression_enabled': False,   # Enable Excel compression
    'password_protection': None,    # Password for Excel file
    'sheet_protection': False,      # Protect sheets from editing
    'freeze_panes': True,           # Freeze header row
    'auto_filter': True,            # Add auto-filter to headers
    'conditional_formatting': False, # Add conditional formatting
    'data_validation': False,       # Add data validation rules
    'hyperlink_detection': True,    # Detect and format hyperlinks
    'image_handling': 'skip',       # 'skip', 'embed', 'link'
    'formula_handling': 'text',     # 'text', 'preserve', 'evaluate'
    'locale': 'en_US',              # Locale for formatting
    'timezone': 'UTC',              # Timezone for date handling
}

# Configuration for large dataset processing (1000+ records)
LARGE_DATASET_CONFIG = {
    **DEFAULT_EXCEL_CONFIG,
    'max_chunk_size': 500,         # Smaller chunks for memory efficiency
    'max_memory_mb': 256,          # Lower memory limit
    'include_charts': False,        # Disable charts for performance
    'conditional_formatting': False, # Disable for performance
    'data_validation': False,       # Disable for performance
    'compression_enabled': True,    # Enable compression for large files
    'auto_filter': False,           # Disable for performance
    'freeze_panes': False,          # Disable for performance
}

# Configuration for small dataset processing (<100 records)
SMALL_DATASET_CONFIG = {
    **DEFAULT_EXCEL_CONFIG,
    'max_chunk_size': 100,         # Process all at once
    'max_memory_mb': 128,          # Lower memory limit
    'include_charts': True,         # Enable charts for small datasets
    'conditional_formatting': True, # Enable for small datasets
    'data_validation': True,        # Enable for small datasets
    'auto_filter': True,            # Enable for small datasets
    'freeze_panes': True,           # Enable for small datasets
}

# Configuration for high-quality reports
HIGH_QUALITY_CONFIG = {
    **DEFAULT_EXCEL_CONFIG,
    'include_charts': True,         # Include charts
    'conditional_formatting': True, # Add conditional formatting
    'data_validation': True,        # Add data validation
    'auto_filter': True,            # Add auto-filter
    'freeze_panes': True,           # Freeze panes
    'header_styling': True,         # Enhanced header styling
    'alternate_row_colors': True,   # Enhanced row colors
    'table_formatting': True,       # Enhanced table formatting
    'compression_enabled': False,   # Disable compression for quality
}

# Configuration for performance-critical scenarios
PERFORMANCE_CONFIG = {
    **DEFAULT_EXCEL_CONFIG,
    'max_chunk_size': 200,         # Very small chunks
    'max_memory_mb': 128,          # Very low memory limit
    'include_charts': False,        # Disable all features
    'conditional_formatting': False,
    'data_validation': False,
    'auto_filter': False,
    'freeze_panes': False,
    'header_styling': False,
    'alternate_row_colors': False,
    'table_formatting': False,
    'compression_enabled': True,    # Enable compression
    'validation_enabled': False,    # Disable validation for speed
}

# Configuration for debugging/development
DEBUG_CONFIG = {
    **DEFAULT_EXCEL_CONFIG,
    'validation_enabled': True,     # Enable validation
    'error_handling': 'stop',       # Stop on errors
    'include_charts': False,        # Disable charts
    'conditional_formatting': False,
    'data_validation': False,
    'compression_enabled': False,   # Disable compression for debugging
}

# Configuration for production use
PRODUCTION_CONFIG = {
    **DEFAULT_EXCEL_CONFIG,
    'validation_enabled': True,     # Always validate in production
    'error_handling': 'continue',   # Continue on errors but log
    'compression_enabled': True,    # Enable compression
    'include_charts': False,        # Disable charts for stability
    'conditional_formatting': False, # Disable for stability
    'data_validation': False,       # Disable for stability
}

def get_excel_config(config_type: str = 'default') -> Dict[str, Any]:
    """
    Get Excel configuration by type
    
    Args:
        config_type: Type of configuration to return
        
    Returns:
        Configuration dictionary
    """
    configs = {
        'default': DEFAULT_EXCEL_CONFIG,
        'large_dataset': LARGE_DATASET_CONFIG,
        'small_dataset': SMALL_DATASET_CONFIG,
        'high_quality': HIGH_QUALITY_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'debug': DEBUG_CONFIG,
        'production': PRODUCTION_CONFIG,
    }
    
    return configs.get(config_type, DEFAULT_EXCEL_CONFIG).copy()

def customize_excel_config(
    base_config: str = 'default',
    customizations: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Customize Excel configuration with specific overrides
    
    Args:
        base_config: Base configuration type
        customizations: Dictionary of customizations to apply
        
    Returns:
        Customized configuration dictionary
    """
    config = get_excel_config(base_config)
    
    if customizations:
        config.update(customizations)
    
    return config

def validate_excel_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Excel configuration and set sensible defaults
    
    Args:
        config: Configuration to validate
        
    Returns:
        Validated configuration
    """
    validated = DEFAULT_EXCEL_CONFIG.copy()
    validated.update(config)
    
    # Ensure numeric values are within reasonable bounds
    validated['max_chunk_size'] = max(1, min(10000, validated['max_chunk_size']))
    validated['max_memory_mb'] = max(64, min(2048, validated['max_memory_mb']))
    validated['max_field_name_length'] = max(10, min(255, validated['max_field_name_length']))
    
    # Validate error handling
    if validated['error_handling'] not in ['continue', 'stop', 'log_only']:
        validated['error_handling'] = 'continue'
    
    # Validate image handling
    if validated['image_handling'] not in ['skip', 'embed', 'link']:
        validated['image_handling'] = 'skip'
    
    # Validate formula handling
    if validated['formula_handling'] not in ['text', 'preserve', 'evaluate']:
        validated['formula_handling'] = 'text'
    
    return validated
