"""
Validation utilities for form data pipeline
"""

import hmac
import hashlib
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def validate_webhook_signature(secret: str, payload: bytes, signature_header: Optional[str]) -> bool:
    """
    Validate webhook signature for security
    Supports different signature formats from various providers
    """
    if not signature_header or not secret:
        return False
    
    try:
        # Handle different signature formats
        if signature_header.startswith('sha256='):
            # GitHub/Standard format: sha256=<hash>
            expected_signature = signature_header
            computed_signature = 'sha256=' + hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
        elif signature_header.startswith('sha1='):
            # Legacy format: sha1=<hash>
            expected_signature = signature_header
            computed_signature = 'sha1=' + hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha1
            ).hexdigest()
            
        else:
            # Plain hash (Zoho, Typeform, etc.)
            expected_signature = signature_header
            computed_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
        
        # Use secure comparison
        return hmac.compare_digest(expected_signature, computed_signature)
        
    except Exception as e:
        logger.error(f"Signature validation error: {str(e)}")
        return False

def validate_form_data(data: dict, required_fields: Optional[list] = None) -> tuple[bool, list]:
    """
    Validate form submission data
    Returns (is_valid, errors)
    """
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return False, errors
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Additional validation rules can be added here
    
    return len(errors) == 0, errors

def sanitize_field_name(field_name: str) -> str:
    """
    Sanitize field names for database storage
    """
    if not isinstance(field_name, str):
        field_name = str(field_name)
    
    # Remove special characters and replace with underscores
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
    
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = 'field_' + sanitized
    
    # Limit length
    if len(sanitized) > 64:
        sanitized = sanitized[:64]
    
    return sanitized or 'unknown_field'

def validate_email(email: str) -> bool:
    """
    Simple email validation
    """
    if not isinstance(email, str):
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_export_config(config: dict) -> tuple[bool, list]:
    """
    Validate Excel export configuration
    """
    errors = []
    
    if not isinstance(config, dict):
        errors.append("Configuration must be a dictionary")
        return False, errors
    
    # Check required fields
    required_fields = ['name', 'data_sources']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate data sources
    if 'data_sources' in config:
        data_sources = config['data_sources']
        if not isinstance(data_sources, list):
            errors.append("data_sources must be a list")
        elif not data_sources:
            errors.append("At least one data source must be specified")
        elif not all(isinstance(ds_id, int) for ds_id in data_sources):
            errors.append("All data source IDs must be integers")
    
    # Validate date range if provided
    if 'date_range_start' in config and 'date_range_end' in config:
        try:
            from datetime import datetime
            start = datetime.fromisoformat(config['date_range_start'])
            end = datetime.fromisoformat(config['date_range_end'])
            if start >= end:
                errors.append("Start date must be before end date")
        except ValueError:
            errors.append("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    
    return len(errors) == 0, errors
