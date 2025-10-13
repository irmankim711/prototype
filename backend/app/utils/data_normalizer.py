"""
Data normalizer utility for processing form submissions from different sources
Standardizes data formats from Google Forms, Microsoft Forms, and custom forms
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List


def normalize_form_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Normalize form data from different sources into a standard format
    
    Args:
        data: Raw form data from submission
        source: Source type (google, microsoft, custom, api)
        
    Returns:
        Normalized data dictionary
    """
    if source == 'google':
        return normalize_google_forms_data(data)
    elif source == 'microsoft':
        return normalize_microsoft_forms_data(data)
    elif source == 'custom':
        return normalize_custom_forms_data(data)
    else:
        return normalize_generic_data(data)


def normalize_google_forms_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Google Forms submission data"""
    normalized = {}
    
    # Handle Google Forms specific structure
    if 'answers' in data:
        for question_id, answer_data in data['answers'].items():
            # Extract question title and value
            question_title = answer_data.get('questionTitle', question_id)
            
            # Handle different answer types
            if 'textAnswer' in answer_data:
                value = answer_data['textAnswer'].get('value', '')
            elif 'choiceAnswer' in answer_data:
                choice_answer = answer_data['choiceAnswer']
                if 'values' in choice_answer:
                    value = choice_answer['values']  # Multiple choice
                else:
                    value = choice_answer.get('value', '')  # Single choice
            elif 'scaleAnswer' in answer_data:
                value = answer_data['scaleAnswer'].get('value', 0)
            elif 'gridAnswer' in answer_data:
                value = answer_data['gridAnswer'].get('answers', {})
            elif 'fileUploadAnswer' in answer_data:
                value = answer_data['fileUploadAnswer'].get('fileId', '')
            else:
                value = str(answer_data)
            
            # Clean and standardize field name
            field_name = clean_field_name(question_title)
            normalized[field_name] = standardize_value(value)
    
    # Add metadata
    normalized['_source'] = 'google_forms'
    normalized['_normalized_at'] = datetime.utcnow().isoformat()
    
    return normalized


def normalize_microsoft_forms_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Microsoft Forms submission data"""
    normalized = {}
    
    # Handle Microsoft Forms structure
    if 'answers' in data:
        for answer in data['answers']:
            question_title = answer.get('questionTitle', '')
            question_id = answer.get('questionId', '')
            
            # Extract value based on question type
            value = None
            if 'value' in answer:
                value = answer['value']
            elif 'values' in answer:
                value = answer['values']  # Multiple values
            elif 'textValue' in answer:
                value = answer['textValue']
            elif 'choiceValue' in answer:
                value = answer['choiceValue']
            elif 'dateValue' in answer:
                value = answer['dateValue']
            elif 'numberValue' in answer:
                value = answer['numberValue']
            
            # Use question title or ID as field name
            field_name = clean_field_name(question_title or question_id)
            if field_name:
                normalized[field_name] = standardize_value(value)
    
    # Add metadata
    normalized['_source'] = 'microsoft_forms'
    normalized['_normalized_at'] = datetime.utcnow().isoformat()
    
    return normalized


def normalize_custom_forms_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize custom form submission data"""
    normalized = {}
    
    # Process each field
    for key, value in data.items():
        if not key.startswith('_'):  # Skip internal fields
            field_name = clean_field_name(key)
            normalized[field_name] = standardize_value(value)
    
    # Preserve any metadata fields
    for key, value in data.items():
        if key.startswith('_'):
            normalized[key] = value
    
    # Add metadata
    normalized['_source'] = 'custom_form'
    normalized['_normalized_at'] = datetime.utcnow().isoformat()
    
    return normalized


def normalize_generic_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize generic form data"""
    normalized = {}
    
    for key, value in data.items():
        field_name = clean_field_name(key)
        normalized[field_name] = standardize_value(value)
    
    # Add metadata
    normalized['_source'] = 'generic'
    normalized['_normalized_at'] = datetime.utcnow().isoformat()
    
    return normalized


def clean_field_name(name: str) -> str:
    """
    Clean and standardize field names
    
    Args:
        name: Original field name
        
    Returns:
        Cleaned field name
    """
    if not name:
        return ''
    
    # Convert to lowercase and replace spaces/special chars with underscores
    cleaned = re.sub(r'[^\w\s]', '', name.lower())
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    # Remove leading/trailing underscores and limit length
    cleaned = cleaned.strip('_')[:50]
    
    # Ensure it doesn't start with a number
    if cleaned and cleaned[0].isdigit():
        cleaned = 'field_' + cleaned
    
    return cleaned or 'unknown_field'


def standardize_value(value: Any) -> Any:
    """
    Standardize field values to consistent types
    
    Args:
        value: Original value
        
    Returns:
        Standardized value
    """
    if value is None:
        return None
    
    # Handle lists/arrays
    if isinstance(value, list):
        return [standardize_value(v) for v in value]
    
    # Handle dictionaries
    if isinstance(value, dict):
        return {k: standardize_value(v) for k, v in value.items()}
    
    # Convert to string and clean
    if not isinstance(value, str):
        value = str(value)
    
    # Trim whitespace
    value = value.strip()
    
    # Try to detect and convert specific types
    if not value:
        return None
    
    # Check for boolean values
    if value.lower() in ['true', 'yes', '1', 'on', 'checked']:
        return True
    elif value.lower() in ['false', 'no', '0', 'off', 'unchecked']:
        return False
    
    # Check for numbers
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # Check for dates
    if is_date_string(value):
        return value  # Keep as string for now, can parse later if needed
    
    # Return as string
    return value


def is_date_string(value: str) -> bool:
    """Check if string appears to be a date"""
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        r'\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, value):
            return True
    
    return False


def extract_email_addresses(data: Dict[str, Any]) -> List[str]:
    """Extract email addresses from form data"""
    emails = []
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    for key, value in data.items():
        if isinstance(value, str):
            found_emails = re.findall(email_pattern, value)
            emails.extend(found_emails)
    
    return list(set(emails))  # Remove duplicates


def extract_phone_numbers(data: Dict[str, Any]) -> List[str]:
    """Extract phone numbers from form data"""
    phones = []
    # Simple phone pattern - can be enhanced
    phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
    
    for key, value in data.items():
        if isinstance(value, str):
            # Look for phone-like patterns
            if re.search(r'phone|tel|mobile|cell', key.lower()):
                found_phones = re.findall(phone_pattern, value)
                phones.extend(found_phones)
    
    return list(set(phones))


def validate_normalized_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate normalized data and return any errors
    
    Args:
        data: Normalized data dictionary
        
    Returns:
        Dictionary of field names and their validation errors
    """
    errors = {}
    
    # Check for required metadata
    if '_source' not in data:
        errors['_source'] = ['Missing source information']
    
    if '_normalized_at' not in data:
        errors['_normalized_at'] = ['Missing normalization timestamp']
    
    # Check for empty data
    data_fields = {k: v for k, v in data.items() if not k.startswith('_')}
    if not data_fields:
        errors['data'] = ['No form data found']
    
    # Validate email fields
    for key, value in data_fields.items():
        if 'email' in key.lower() and isinstance(value, str):
            if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                errors[key] = ['Invalid email format']
    
    return errors


def merge_duplicate_submissions(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge duplicate submissions based on email or other unique identifiers
    
    Args:
        submissions: List of normalized submission data
        
    Returns:
        List of deduplicated submissions
    """
    seen = set()
    unique_submissions = []
    
    for submission in submissions:
        # Create a signature for the submission
        signature_parts = []
        
        # Use email if available
        emails = extract_email_addresses(submission)
        if emails:
            signature_parts.append(emails[0])
        
        # Use other identifying fields
        for key in ['name', 'full_name', 'first_name', 'last_name']:
            if key in submission and submission[key]:
                signature_parts.append(str(submission[key]).lower())
        
        # Create signature
        signature = '|'.join(signature_parts) if signature_parts else str(hash(json.dumps(submission, sort_keys=True)))
        
        if signature not in seen:
            seen.add(signature)
            unique_submissions.append(submission)
    
    return unique_submissions


# Constants for field mapping
COMMON_FIELD_MAPPINGS = {
    'email_address': 'email',
    'e_mail': 'email',
    'electronic_mail': 'email',
    'full_name': 'name',
    'complete_name': 'name',
    'your_name': 'name',
    'first_name': 'first_name',
    'last_name': 'last_name',
    'family_name': 'last_name',
    'given_name': 'first_name',
    'phone_number': 'phone',
    'telephone': 'phone',
    'mobile': 'phone',
    'cell_phone': 'phone',
    'organization': 'company',
    'organisation': 'company',
    'workplace': 'company',
    'employer': 'company',
    'job_title': 'position',
    'position': 'position',
    'title': 'position',
    'role': 'position',
    'message': 'comments',
    'feedback': 'comments',
    'additional_comments': 'comments',
    'notes': 'comments',
    'remarks': 'comments'
}


def apply_field_mappings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply common field name mappings to standardize field names"""
    mapped_data = {}
    
    for key, value in data.items():
        # Check if key should be mapped
        mapped_key = COMMON_FIELD_MAPPINGS.get(key.lower(), key)
        mapped_data[mapped_key] = value
    
    return mapped_data
