"""
Data Transformation Service for Google Forms to Sheets Integration

Handles data transformation between Google Forms responses and Google Sheets format.
Supports different field types, custom header generation, data formatting rules,
and data validation/sanitization for security.

Requirements covered: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import re
import html
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date, time
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Enumeration of supported field types"""
    TEXT = "text"
    PARAGRAPH = "paragraph"
    MULTIPLE_CHOICE = "multiple_choice"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    LINEAR_SCALE = "linear_scale"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    FILE_UPLOAD = "file_upload"
    EMAIL = "email"
    URL = "url"
    NUMBER = "number"
    PHONE = "phone"


@dataclass
class TransformationRule:
    """Configuration for data transformation rules"""
    field_id: str
    field_type: FieldType
    custom_header: Optional[str] = None
    format_pattern: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    sanitization_enabled: bool = True
    include_in_export: bool = True


@dataclass
class FormattingRules:
    """Configuration for data formatting rules"""
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    number_decimal_places: int = 2
    boolean_true_value: str = "Yes"
    boolean_false_value: str = "No"
    null_value_replacement: str = ""
    list_separator: str = ", "
    escape_formulas: bool = True
    max_cell_length: int = 32767  # Excel cell limit


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    sanitized_value: Any
    warnings: List[str]
    errors: List[str]


class DataTransformationService:
    """
    Service for transforming Google Forms responses to Google Sheets format.
    
    Features:
    - Support for different field types (text, multiple choice, file uploads, dates)
    - Custom header generation and data formatting rules
    - Data validation and sanitization for security
    - Flexible transformation rules configuration
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataTransformationService")
        
        # Default formatting rules
        self.default_formatting = FormattingRules()
        
        # Security patterns for sanitization
        self.formula_patterns = [
            re.compile(r'^[=@+\-]', re.IGNORECASE),  # Formula indicators
            re.compile(r'^\s*[=@+\-]', re.IGNORECASE),  # Formula with leading whitespace
        ]
        
        # URL validation pattern
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        # Email validation pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

    def transform_form_responses(
        self, 
        responses: List[Dict[str, Any]], 
        form_schema: Dict[str, Any],
        transformation_rules: Optional[List[TransformationRule]] = None,
        formatting_rules: Optional[FormattingRules] = None
    ) -> List[List[Any]]:
        """
        Transform form responses to sheet format.
        
        Args:
            responses: List of form response dictionaries
            form_schema: Form schema with question definitions
            transformation_rules: Optional custom transformation rules
            formatting_rules: Optional custom formatting rules
            
        Returns:
            List of rows, where each row is a list of cell values
        """
        try:
            if not responses:
                return []
            
            # Use default formatting if not provided
            formatting = formatting_rules or self.default_formatting
            
            # Build transformation rules from schema if not provided
            if not transformation_rules:
                transformation_rules = self._build_default_transformation_rules(form_schema)
            
            # Create rules lookup for efficiency
            rules_lookup = {rule.field_id: rule for rule in transformation_rules}
            
            # Transform each response
            transformed_rows = []
            for response in responses:
                try:
                    row = self._transform_single_response(
                        response, form_schema, rules_lookup, formatting
                    )
                    transformed_rows.append(row)
                except Exception as e:
                    self.logger.error(f"Error transforming response {response.get('responseId', 'unknown')}: {e}")
                    # Continue with other responses
                    continue
            
            return transformed_rows
            
        except Exception as e:
            self.logger.error(f"Error transforming form responses: {e}")
            raise

    def generate_headers(
        self, 
        form_schema: Dict[str, Any], 
        transformation_rules: Optional[List[TransformationRule]] = None,
        include_metadata: bool = True
    ) -> List[str]:
        """
        Generate column headers for the sheet based on form schema.
        
        Args:
            form_schema: Form schema with question definitions
            transformation_rules: Optional custom transformation rules
            include_metadata: Whether to include metadata columns
            
        Returns:
            List of column headers
        """
        try:
            headers = []
            
            # Add metadata headers if requested
            if include_metadata:
                headers.extend([
                    "Response ID",
                    "Timestamp",
                    "Email Address"
                ])
            
            # Build transformation rules if not provided
            if not transformation_rules:
                transformation_rules = self._build_default_transformation_rules(form_schema)
            
            # Add question headers
            for rule in transformation_rules:
                if rule.include_in_export:
                    header = rule.custom_header or self._generate_default_header(
                        rule.field_id, form_schema
                    )
                    headers.append(header)
            
            return headers
            
        except Exception as e:
            self.logger.error(f"Error generating headers: {e}")
            raise

    def apply_formatting_rules(
        self, 
        data: List[List[Any]], 
        formatting_rules: FormattingRules
    ) -> List[List[Any]]:
        """
        Apply formatting rules to transformed data.
        
        Args:
            data: List of rows with cell values
            formatting_rules: Formatting configuration
            
        Returns:
            List of rows with formatted cell values
        """
        try:
            formatted_data = []
            
            for row in data:
                formatted_row = []
                for cell_value in row:
                    formatted_value = self._format_cell_value(cell_value, formatting_rules)
                    formatted_row.append(formatted_value)
                formatted_data.append(formatted_row)
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error applying formatting rules: {e}")
            raise

    def handle_special_fields(
        self, 
        field_value: Any, 
        field_type: FieldType,
        formatting_rules: Optional[FormattingRules] = None
    ) -> Any:
        """
        Handle special field types with specific formatting requirements.
        
        Args:
            field_value: Raw field value
            field_type: Type of the field
            formatting_rules: Optional formatting configuration
            
        Returns:
            Formatted field value
        """
        try:
            formatting = formatting_rules or self.default_formatting
            
            if field_value is None:
                return formatting.null_value_replacement
            
            if field_type == FieldType.DATE:
                return self._handle_date_field(field_value, formatting)
            
            elif field_type == FieldType.TIME:
                return self._handle_time_field(field_value, formatting)
            
            elif field_type == FieldType.DATETIME:
                return self._handle_datetime_field(field_value, formatting)
            
            elif field_type in [FieldType.MULTIPLE_CHOICE, FieldType.CHECKBOX]:
                return self._handle_choice_field(field_value, formatting)
            
            elif field_type == FieldType.FILE_UPLOAD:
                return self._handle_file_upload_field(field_value, formatting)
            
            elif field_type == FieldType.NUMBER:
                return self._handle_number_field(field_value, formatting)
            
            elif field_type == FieldType.LINEAR_SCALE:
                return self._handle_scale_field(field_value, formatting)
            
            elif field_type in [FieldType.EMAIL, FieldType.URL, FieldType.PHONE]:
                return self._handle_contact_field(field_value, field_type, formatting)
            
            else:
                # Default text handling
                return self._handle_text_field(field_value, formatting)
            
        except Exception as e:
            self.logger.error(f"Error handling special field {field_type}: {e}")
            return str(field_value) if field_value is not None else formatting.null_value_replacement

    def validate_and_sanitize_data(
        self, 
        data: List[List[Any]], 
        transformation_rules: List[TransformationRule]
    ) -> Tuple[List[List[Any]], List[ValidationResult]]:
        """
        Validate and sanitize data for security and integrity.
        
        Args:
            data: List of rows with cell values
            transformation_rules: Transformation rules with validation config
            
        Returns:
            Tuple of (sanitized_data, validation_results)
        """
        try:
            sanitized_data = []
            validation_results = []
            
            for row_idx, row in enumerate(data):
                sanitized_row = []
                row_validation = ValidationResult(
                    is_valid=True,
                    sanitized_value=None,
                    warnings=[],
                    errors=[]
                )
                
                for col_idx, cell_value in enumerate(row):
                    # Get transformation rule for this column
                    rule = transformation_rules[col_idx] if col_idx < len(transformation_rules) else None
                    
                    # Validate and sanitize cell
                    cell_validation = self._validate_and_sanitize_cell(cell_value, rule)
                    
                    sanitized_row.append(cell_validation.sanitized_value)
                    
                    # Aggregate validation results
                    if not cell_validation.is_valid:
                        row_validation.is_valid = False
                    
                    row_validation.warnings.extend([
                        f"Col {col_idx}: {warning}" for warning in cell_validation.warnings
                    ])
                    row_validation.errors.extend([
                        f"Col {col_idx}: {error}" for error in cell_validation.errors
                    ])
                
                sanitized_data.append(sanitized_row)
                validation_results.append(row_validation)
            
            return sanitized_data, validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating and sanitizing data: {e}")
            raise

    # Private helper methods

    def _build_default_transformation_rules(
        self, 
        form_schema: Dict[str, Any]
    ) -> List[TransformationRule]:
        """Build default transformation rules from form schema"""
        rules = []
        
        questions = form_schema.get('questions', [])
        for question in questions:
            field_id = question.get('item_id', '')
            question_type = question.get('question_type', 'text')
            
            # Map Google Forms question type to our FieldType
            field_type = self._map_question_type_to_field_type(question_type, question)
            
            rule = TransformationRule(
                field_id=field_id,
                field_type=field_type,
                custom_header=question.get('title', ''),
                sanitization_enabled=True,
                include_in_export=True
            )
            
            rules.append(rule)
        
        return rules

    def _map_question_type_to_field_type(
        self, 
        question_type: str, 
        question_data: Dict[str, Any]
    ) -> FieldType:
        """Map Google Forms question type to our FieldType enum"""
        type_mapping = {
            'text': FieldType.TEXT,
            'choice': FieldType.MULTIPLE_CHOICE,
            'scale': FieldType.LINEAR_SCALE,
            'date': FieldType.DATE,
            'time': FieldType.TIME,
            'file_upload': FieldType.FILE_UPLOAD
        }
        
        # Handle special cases
        if question_type == 'text':
            if question_data.get('paragraph', False):
                return FieldType.PARAGRAPH
        
        elif question_type == 'choice':
            choice_type = question_data.get('choice_type', 'RADIO')
            if choice_type == 'CHECKBOX':
                return FieldType.CHECKBOX
            elif choice_type == 'DROP_DOWN':
                return FieldType.DROPDOWN
        
        elif question_type == 'date':
            if question_data.get('include_time', False):
                return FieldType.DATETIME
        
        return type_mapping.get(question_type, FieldType.TEXT)

    def _transform_single_response(
        self, 
        response: Dict[str, Any], 
        form_schema: Dict[str, Any],
        rules_lookup: Dict[str, TransformationRule],
        formatting: FormattingRules
    ) -> List[Any]:
        """Transform a single form response to a sheet row"""
        row = []
        
        # Add metadata columns
        row.extend([
            response.get('responseId', ''),
            self._format_timestamp(response.get('createTime'), formatting),
            response.get('respondentEmail', '')
        ])
        
        # Add question responses
        answers = response.get('answers', {})
        
        for field_id, rule in rules_lookup.items():
            if not rule.include_in_export:
                continue
            
            # Get answer for this field
            answer_data = answers.get(field_id, {})
            field_value = self._extract_answer_value(answer_data, rule.field_type)
            
            # Handle special fields
            formatted_value = self.handle_special_fields(
                field_value, rule.field_type, formatting
            )
            
            # Apply sanitization if enabled
            if rule.sanitization_enabled:
                formatted_value = self._sanitize_value(formatted_value, formatting)
            
            row.append(formatted_value)
        
        return row

    def _extract_answer_value(
        self, 
        answer_data: Dict[str, Any], 
        field_type: FieldType
    ) -> Any:
        """Extract the actual answer value from Google Forms answer structure"""
        if not answer_data:
            return None
        
        # Handle different answer structures based on field type
        if field_type in [FieldType.TEXT, FieldType.PARAGRAPH, FieldType.EMAIL, FieldType.URL, FieldType.PHONE]:
            text_answers = answer_data.get('textAnswers', {})
            answers = text_answers.get('answers', [])
            return answers[0].get('value', '') if answers else ''
        
        elif field_type in [FieldType.MULTIPLE_CHOICE, FieldType.DROPDOWN]:
            text_answers = answer_data.get('textAnswers', {})
            answers = text_answers.get('answers', [])
            return answers[0].get('value', '') if answers else ''
        
        elif field_type == FieldType.CHECKBOX:
            text_answers = answer_data.get('textAnswers', {})
            answers = text_answers.get('answers', [])
            return [answer.get('value', '') for answer in answers]
        
        elif field_type == FieldType.LINEAR_SCALE:
            text_answers = answer_data.get('textAnswers', {})
            answers = text_answers.get('answers', [])
            value = answers[0].get('value', '') if answers else ''
            try:
                return int(value) if value else None
            except ValueError:
                return value
        
        elif field_type == FieldType.FILE_UPLOAD:
            file_upload_answers = answer_data.get('fileUploadAnswers', {})
            answers = file_upload_answers.get('answers', [])
            return [answer.get('fileId', '') for answer in answers]
        
        else:
            # Default to text extraction
            text_answers = answer_data.get('textAnswers', {})
            answers = text_answers.get('answers', [])
            return answers[0].get('value', '') if answers else ''

    def _generate_default_header(
        self, 
        field_id: str, 
        form_schema: Dict[str, Any]
    ) -> str:
        """Generate default header for a field"""
        questions = form_schema.get('questions', [])
        
        for question in questions:
            if question.get('item_id') == field_id:
                title = question.get('title', '')
                if title:
                    return title
        
        return f"Question {field_id}"

    def _format_cell_value(self, value: Any, formatting: FormattingRules) -> Any:
        """Format a single cell value according to formatting rules"""
        if value is None:
            return formatting.null_value_replacement
        
        # Truncate if too long
        if isinstance(value, str) and len(value) > formatting.max_cell_length:
            return value[:formatting.max_cell_length - 3] + "..."
        
        return value

    def _format_timestamp(self, timestamp_str: str, formatting: FormattingRules) -> str:
        """Format timestamp string"""
        if not timestamp_str:
            return formatting.null_value_replacement
        
        try:
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime(formatting.datetime_format)
        except Exception:
            return timestamp_str

    def _handle_date_field(self, value: Any, formatting: FormattingRules) -> str:
        """Handle date field formatting"""
        if not value:
            return formatting.null_value_replacement
        
        try:
            if isinstance(value, str):
                # Try to parse various date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.strftime(formatting.date_format)
                    except ValueError:
                        continue
                return value  # Return as-is if can't parse
            
            elif isinstance(value, (date, datetime)):
                return value.strftime(formatting.date_format)
            
            else:
                return str(value)
        
        except Exception:
            return str(value) if value else formatting.null_value_replacement

    def _handle_time_field(self, value: Any, formatting: FormattingRules) -> str:
        """Handle time field formatting"""
        if not value:
            return formatting.null_value_replacement
        
        try:
            if isinstance(value, str):
                # Try to parse time formats
                for fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p']:
                    try:
                        t = datetime.strptime(value, fmt).time()
                        return t.strftime(formatting.time_format)
                    except ValueError:
                        continue
                return value  # Return as-is if can't parse
            
            elif isinstance(value, time):
                return value.strftime(formatting.time_format)
            
            else:
                return str(value)
        
        except Exception:
            return str(value) if value else formatting.null_value_replacement

    def _handle_datetime_field(self, value: Any, formatting: FormattingRules) -> str:
        """Handle datetime field formatting"""
        if not value:
            return formatting.null_value_replacement
        
        try:
            if isinstance(value, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime(formatting.datetime_format)
            
            elif isinstance(value, datetime):
                return value.strftime(formatting.datetime_format)
            
            else:
                return str(value)
        
        except Exception:
            return str(value) if value else formatting.null_value_replacement

    def _handle_choice_field(self, value: Any, formatting: FormattingRules) -> str:
        """Handle multiple choice and checkbox fields"""
        if not value:
            return formatting.null_value_replacement
        
        if isinstance(value, list):
            return formatting.list_separator.join(str(v) for v in value)
        else:
            return str(value)

    def _handle_file_upload_field(self, value: Any, formatting: FormattingRules) -> str:
        """Handle file upload fields"""
        if not value:
            return formatting.null_value_replacement
        
        if isinstance(value, list):
            # Return file IDs or URLs
            file_links = []
            for file_id in value:
                if file_id:
                    file_links.append(f"https://drive.google.com/file/d/{file_id}/view")
            return formatting.list_separator.join(file_links)
        else:
            return f"https://drive.google.com/file/d/{value}/view" if value else formatting.null_value_replacement

    def _handle_number_field(self, value: Any, formatting: FormattingRules) -> Union[float, str]:
        """Handle number field formatting"""
        if value is None:
            return formatting.null_value_replacement
        
        try:
            if isinstance(value, str):
                # Try to parse as number
                if '.' in value:
                    num = float(value)
                    return round(num, formatting.number_decimal_places)
                else:
                    return int(value)
            elif isinstance(value, (int, float)):
                if isinstance(value, float):
                    return round(value, formatting.number_decimal_places)
                return value
            else:
                return str(value)
        
        except Exception:
            return str(value) if value else formatting.null_value_replacement

    def _handle_scale_field(self, value: Any, formatting: FormattingRules) -> Union[int, str]:
        """Handle linear scale field formatting"""
        if value is None:
            return formatting.null_value_replacement
        
        try:
            return int(value)
        except Exception:
            return str(value) if value else formatting.null_value_replacement

    def _handle_contact_field(
        self, 
        value: Any, 
        field_type: FieldType, 
        formatting: FormattingRules
    ) -> str:
        """Handle email, URL, and phone fields"""
        if not value:
            return formatting.null_value_replacement
        
        value_str = str(value).strip()
        
        # Basic validation
        if field_type == FieldType.EMAIL:
            if not self.email_pattern.match(value_str):
                self.logger.warning(f"Invalid email format: {value_str}")
        
        elif field_type == FieldType.URL:
            if not self.url_pattern.match(value_str):
                self.logger.warning(f"Invalid URL format: {value_str}")
        
        return value_str

    def _handle_text_field(self, value: Any, formatting: FormattingRules) -> str:
        """Handle text and paragraph fields"""
        if value is None:
            return formatting.null_value_replacement
        
        text_value = str(value)
        
        # Apply length limit
        if len(text_value) > formatting.max_cell_length:
            text_value = text_value[:formatting.max_cell_length - 3] + "..."
        
        return text_value

    def _sanitize_value(self, value: Any, formatting: FormattingRules) -> Any:
        """Sanitize value for security"""
        if value is None:
            return formatting.null_value_replacement
        
        if not isinstance(value, str):
            return value
        
        sanitized = value
        
        # Escape HTML entities
        sanitized = html.escape(sanitized)
        
        # Escape formulas if enabled
        if formatting.escape_formulas:
            for pattern in self.formula_patterns:
                if pattern.match(sanitized):
                    sanitized = "'" + sanitized  # Prefix with single quote to escape
                    break
        
        return sanitized

    def _validate_and_sanitize_cell(
        self, 
        cell_value: Any, 
        rule: Optional[TransformationRule]
    ) -> ValidationResult:
        """Validate and sanitize a single cell value"""
        result = ValidationResult(
            is_valid=True,
            sanitized_value=cell_value,
            warnings=[],
            errors=[]
        )
        
        if not rule:
            return result
        
        # Apply validation rules if specified
        if rule.validation_rules:
            validation_rules = rule.validation_rules
            
            # Check required field
            if validation_rules.get('required', False) and not cell_value:
                result.is_valid = False
                result.errors.append("Required field is empty")
            
            # Check max length
            max_length = validation_rules.get('max_length')
            if max_length and isinstance(cell_value, str) and len(cell_value) > max_length:
                result.warnings.append(f"Value exceeds max length of {max_length}")
                result.sanitized_value = cell_value[:max_length]
            
            # Check pattern matching
            pattern = validation_rules.get('pattern')
            if pattern and isinstance(cell_value, str):
                if not re.match(pattern, cell_value):
                    result.warnings.append(f"Value does not match required pattern")
        
        # Apply sanitization if enabled
        if rule.sanitization_enabled:
            result.sanitized_value = self._sanitize_value(
                result.sanitized_value, 
                self.default_formatting
            )
        
        return result