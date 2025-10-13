# Data Transformation Service

The Data Transformation Service handles converting Google Forms responses into Google Sheets format with comprehensive support for different field types, custom formatting, and security validation.

## Features

- **Multi-field Type Support**: Text, multiple choice, checkboxes, dates, times, file uploads, numbers, linear scales, emails, URLs, and phone numbers
- **Custom Header Generation**: Automatic header generation from form schema with custom override support
- **Data Formatting Rules**: Configurable formatting for dates, times, numbers, lists, and null values
- **Security Validation**: Formula escaping, HTML sanitization, and input validation
- **Flexible Configuration**: Custom transformation rules with field-specific settings

## Usage

### Basic Usage

```python
from app.services.data_transformation_service import DataTransformationService

# Initialize the service
service = DataTransformationService()

# Transform form responses to sheet format
transformed_data = service.transform_form_responses(
    responses=form_responses,  # List of Google Forms responses
    form_schema=form_schema,   # Form schema with question definitions
)

# Generate headers for the sheet
headers = service.generate_headers(
    form_schema=form_schema,
    include_metadata=True  # Include Response ID, Timestamp, Email columns
)
```

### Custom Transformation Rules

```python
from app.services.data_transformation_service import TransformationRule, FieldType

# Define custom transformation rules
custom_rules = [
    TransformationRule(
        field_id='q1',
        field_type=FieldType.TEXT,
        custom_header='Customer Name',
        validation_rules={'required': True, 'max_length': 100},
        sanitization_enabled=True
    ),
    TransformationRule(
        field_id='q2',
        field_type=FieldType.EMAIL,
        custom_header='Email Address',
        validation_rules={'required': True}
    )
]

# Use custom rules
transformed_data = service.transform_form_responses(
    responses=form_responses,
    form_schema=form_schema,
    transformation_rules=custom_rules
)
```

### Custom Formatting Rules

```python
from app.services.data_transformation_service import FormattingRules

# Define custom formatting
custom_formatting = FormattingRules(
    date_format="%B %d, %Y",        # January 15, 2024
    time_format="%I:%M %p",         # 2:30 PM
    datetime_format="%B %d, %Y %I:%M %p",
    number_decimal_places=3,
    list_separator=" | ",
    null_value_replacement="N/A",
    escape_formulas=True,
    max_cell_length=1000
)

# Apply custom formatting
transformed_data = service.transform_form_responses(
    responses=form_responses,
    form_schema=form_schema,
    formatting_rules=custom_formatting
)
```

### Data Validation and Sanitization

```python
# Validate and sanitize data for security
sanitized_data, validation_results = service.validate_and_sanitize_data(
    data=transformed_data,
    transformation_rules=custom_rules
)

# Check validation results
for i, result in enumerate(validation_results):
    if not result.is_valid:
        print(f"Row {i} validation errors: {result.errors}")
    if result.warnings:
        print(f"Row {i} warnings: {result.warnings}")
```

### Special Field Handling

```python
# Handle specific field types
formatted_date = service.handle_special_fields(
    field_value="2024-01-15",
    field_type=FieldType.DATE
)

formatted_files = service.handle_special_fields(
    field_value=["file_123", "file_456"],
    field_type=FieldType.FILE_UPLOAD
)

formatted_choices = service.handle_special_fields(
    field_value=["Option A", "Option B"],
    field_type=FieldType.CHECKBOX
)
```

## Field Types Supported

| Field Type | Description | Example Input | Example Output |
|------------|-------------|---------------|----------------|
| `TEXT` | Single-line text | "Hello World" | "Hello World" |
| `PARAGRAPH` | Multi-line text | "Long text..." | "Long text..." |
| `MULTIPLE_CHOICE` | Single selection | "Option A" | "Option A" |
| `CHECKBOX` | Multiple selections | ["A", "B"] | "A, B" |
| `DROPDOWN` | Dropdown selection | "Selected" | "Selected" |
| `LINEAR_SCALE` | Rating scale | "4" | 4 |
| `DATE` | Date field | "2024-01-15" | "2024-01-15" |
| `TIME` | Time field | "14:30:00" | "14:30:00" |
| `DATETIME` | Date and time | "2024-01-15T14:30:00Z" | "2024-01-15 14:30:00" |
| `FILE_UPLOAD` | File attachments | ["file_123"] | "https://drive.google.com/file/d/file_123/view" |
| `EMAIL` | Email address | "test@example.com" | "test@example.com" |
| `URL` | Web URL | "https://example.com" | "https://example.com" |
| `NUMBER` | Numeric value | "123.456" | 123.46 |
| `PHONE` | Phone number | "+1234567890" | "+1234567890" |

## Security Features

### Formula Escaping
Automatically escapes potential spreadsheet formulas by prefixing with single quote:
- `=SUM(A1:A10)` → `'=SUM(A1:A10)`
- `@SUM(A1:A10)` → `'@SUM(A1:A10)`
- `+SUM(A1:A10)` → `'+SUM(A1:A10)`

### HTML Sanitization
Escapes HTML entities to prevent XSS:
- `<script>alert('xss')</script>` → `&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;`

### Input Validation
- Required field validation
- Maximum length validation
- Pattern matching validation
- Email format validation
- URL format validation

## Configuration Options

### TransformationRule Properties
- `field_id`: Unique identifier for the form field
- `field_type`: Type of field (FieldType enum)
- `custom_header`: Custom column header (optional)
- `format_pattern`: Custom format pattern (optional)
- `validation_rules`: Validation configuration (optional)
- `sanitization_enabled`: Enable/disable sanitization (default: True)
- `include_in_export`: Include field in export (default: True)

### FormattingRules Properties
- `date_format`: Date format string (default: "%Y-%m-%d")
- `time_format`: Time format string (default: "%H:%M:%S")
- `datetime_format`: DateTime format string (default: "%Y-%m-%d %H:%M:%S")
- `number_decimal_places`: Decimal places for numbers (default: 2)
- `boolean_true_value`: Text for true values (default: "Yes")
- `boolean_false_value`: Text for false values (default: "No")
- `null_value_replacement`: Text for null values (default: "")
- `list_separator`: Separator for list values (default: ", ")
- `escape_formulas`: Enable formula escaping (default: True)
- `max_cell_length`: Maximum cell length (default: 32767)

## Error Handling

The service includes comprehensive error handling:
- Graceful handling of malformed response data
- Logging of validation warnings and errors
- Fallback to default values for missing data
- Continuation of processing even when individual responses fail

## Integration with Google Forms Service

The service is designed to work seamlessly with the existing Google Forms Service:

```python
# Example integration workflow
from app.services.data_sources.google_forms_service import GoogleFormsDataService
from app.services.data_transformation_service import DataTransformationService

# Get form data
forms_service = GoogleFormsDataService()
form_data = forms_service.get_data('gform_123', {'user_id': 'user_456'})

# Get form schema
form_schema = forms_service.get_form_schema('user_456', 'form_123')

# Transform for sheets
transformation_service = DataTransformationService()
sheet_data = transformation_service.transform_form_responses(
    responses=form_data.data['responses'],
    form_schema=form_schema.data
)
```

## Testing

The service includes comprehensive unit tests covering:
- All field type transformations
- Custom formatting rules
- Validation and sanitization
- Error handling scenarios
- Security features
- Edge cases

Run tests with:
```bash
python -m pytest tests/test_data_transformation_service.py -v
```

## Requirements Covered

This implementation satisfies the following requirements from the Google Forms to Sheets integration spec:

- **4.1**: Data transformation and formatting options
- **4.2**: Date/time and numeric response formatting
- **4.3**: Text response encoding and escaping
- **4.4**: Formula sanitization for security
- **4.5**: Custom transformation rule application