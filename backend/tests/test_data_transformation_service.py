"""
Unit tests for Data Transformation Service

Tests all transformation scenarios including:
- Different field types (text, multiple choice, file uploads, dates)
- Custom header generation and data formatting rules
- Data validation and sanitization for security
- Edge cases and error handling
"""

import pytest
from datetime import datetime, date, time
from unittest.mock import Mock, patch

from app.services.data_transformation_service import (
    DataTransformationService,
    FieldType,
    TransformationRule,
    FormattingRules,
    ValidationResult
)


class TestDataTransformationService:
    """Test suite for DataTransformationService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = DataTransformationService()
        
        # Sample form schema
        self.sample_form_schema = {
            'form_id': 'test_form_123',
            'title': 'Test Form',
            'questions': [
                {
                    'item_id': 'q1',
                    'title': 'Name',
                    'question_type': 'text',
                    'required': True
                },
                {
                    'item_id': 'q2',
                    'title': 'Email',
                    'question_type': 'text',
                    'required': True
                },
                {
                    'item_id': 'q3',
                    'title': 'Favorite Color',
                    'question_type': 'choice',
                    'choice_type': 'RADIO',
                    'options': ['Red', 'Blue', 'Green']
                },
                {
                    'item_id': 'q4',
                    'title': 'Hobbies',
                    'question_type': 'choice',
                    'choice_type': 'CHECKBOX',
                    'options': ['Reading', 'Sports', 'Music']
                },
                {
                    'item_id': 'q5',
                    'title': 'Birth Date',
                    'question_type': 'date'
                },
                {
                    'item_id': 'q6',
                    'title': 'Rating',
                    'question_type': 'scale',
                    'low': 1,
                    'high': 5
                },
                {
                    'item_id': 'q7',
                    'title': 'Resume',
                    'question_type': 'file_upload'
                }
            ]
        }
        
        # Sample form responses
        self.sample_responses = [
            {
                'responseId': 'resp_001',
                'createTime': '2024-01-15T10:30:00Z',
                'respondentEmail': 'john@example.com',
                'answers': {
                    'q1': {
                        'textAnswers': {
                            'answers': [{'value': 'John Doe'}]
                        }
                    },
                    'q2': {
                        'textAnswers': {
                            'answers': [{'value': 'john@example.com'}]
                        }
                    },
                    'q3': {
                        'textAnswers': {
                            'answers': [{'value': 'Blue'}]
                        }
                    },
                    'q4': {
                        'textAnswers': {
                            'answers': [
                                {'value': 'Reading'},
                                {'value': 'Music'}
                            ]
                        }
                    },
                    'q5': {
                        'textAnswers': {
                            'answers': [{'value': '1990-05-15'}]
                        }
                    },
                    'q6': {
                        'textAnswers': {
                            'answers': [{'value': '4'}]
                        }
                    },
                    'q7': {
                        'fileUploadAnswers': {
                            'answers': [{'fileId': 'file_123'}]
                        }
                    }
                }
            },
            {
                'responseId': 'resp_002',
                'createTime': '2024-01-15T11:00:00Z',
                'respondentEmail': 'jane@example.com',
                'answers': {
                    'q1': {
                        'textAnswers': {
                            'answers': [{'value': 'Jane Smith'}]
                        }
                    },
                    'q2': {
                        'textAnswers': {
                            'answers': [{'value': 'jane@example.com'}]
                        }
                    },
                    'q3': {
                        'textAnswers': {
                            'answers': [{'value': 'Red'}]
                        }
                    },
                    'q4': {
                        'textAnswers': {
                            'answers': [{'value': 'Sports'}]
                        }
                    },
                    'q5': {
                        'textAnswers': {
                            'answers': [{'value': '1985-12-20'}]
                        }
                    },
                    'q6': {
                        'textAnswers': {
                            'answers': [{'value': '5'}]
                        }
                    }
                    # No file upload answer
                }
            }
        ]

    def test_transform_form_responses_basic(self):
        """Test basic form response transformation"""
        result = self.service.transform_form_responses(
            self.sample_responses,
            self.sample_form_schema
        )
        
        assert len(result) == 2  # Two responses
        assert len(result[0]) == 10  # 3 metadata + 7 questions
        
        # Check first response
        first_row = result[0]
        assert first_row[0] == 'resp_001'  # Response ID
        assert 'john@example.com' in first_row[2]  # Email
        assert first_row[3] == 'John Doe'  # Name
        assert first_row[4] == 'john@example.com'  # Email answer
        assert first_row[5] == 'Blue'  # Favorite color
        assert 'Reading' in first_row[6] and 'Music' in first_row[6]  # Hobbies
        assert first_row[7] == '1990-05-15'  # Birth date
        assert first_row[8] == 4  # Rating
        assert 'drive.google.com' in first_row[9]  # File upload

    def test_transform_form_responses_empty_list(self):
        """Test transformation with empty response list"""
        result = self.service.transform_form_responses([], self.sample_form_schema)
        assert result == []

    def test_generate_headers_with_metadata(self):
        """Test header generation with metadata columns"""
        headers = self.service.generate_headers(
            self.sample_form_schema,
            include_metadata=True
        )
        
        expected_headers = [
            "Response ID",
            "Timestamp", 
            "Email Address",
            "Name",
            "Email",
            "Favorite Color",
            "Hobbies",
            "Birth Date",
            "Rating",
            "Resume"
        ]
        
        assert headers == expected_headers

    def test_generate_headers_without_metadata(self):
        """Test header generation without metadata columns"""
        headers = self.service.generate_headers(
            self.sample_form_schema,
            include_metadata=False
        )
        
        expected_headers = [
            "Name",
            "Email", 
            "Favorite Color",
            "Hobbies",
            "Birth Date",
            "Rating",
            "Resume"
        ]
        
        assert headers == expected_headers

    def test_generate_headers_with_custom_rules(self):
        """Test header generation with custom transformation rules"""
        custom_rules = [
            TransformationRule(
                field_id='q1',
                field_type=FieldType.TEXT,
                custom_header='Full Name'
            ),
            TransformationRule(
                field_id='q2',
                field_type=FieldType.EMAIL,
                custom_header='Email Address'
            ),
            TransformationRule(
                field_id='q3',
                field_type=FieldType.MULTIPLE_CHOICE,
                include_in_export=False  # Exclude from export
            )
        ]
        
        headers = self.service.generate_headers(
            self.sample_form_schema,
            transformation_rules=custom_rules,
            include_metadata=False
        )
        
        assert headers == ['Full Name', 'Email Address']

    def test_handle_special_fields_text(self):
        """Test handling of text fields"""
        result = self.service.handle_special_fields(
            "Hello World",
            FieldType.TEXT
        )
        assert result == "Hello World"
        
        # Test null value
        result = self.service.handle_special_fields(
            None,
            FieldType.TEXT
        )
        assert result == ""

    def test_handle_special_fields_date(self):
        """Test handling of date fields"""
        # Test string date
        result = self.service.handle_special_fields(
            "2024-01-15",
            FieldType.DATE
        )
        assert result == "2024-01-15"
        
        # Test datetime object
        test_date = date(2024, 1, 15)
        result = self.service.handle_special_fields(
            test_date,
            FieldType.DATE
        )
        assert result == "2024-01-15"

    def test_handle_special_fields_time(self):
        """Test handling of time fields"""
        # Test string time
        result = self.service.handle_special_fields(
            "14:30:00",
            FieldType.TIME
        )
        assert result == "14:30:00"
        
        # Test time object
        test_time = time(14, 30, 0)
        result = self.service.handle_special_fields(
            test_time,
            FieldType.TIME
        )
        assert result == "14:30:00"

    def test_handle_special_fields_datetime(self):
        """Test handling of datetime fields"""
        # Test ISO string
        result = self.service.handle_special_fields(
            "2024-01-15T14:30:00Z",
            FieldType.DATETIME
        )
        assert "2024-01-15 14:30:00" in result
        
        # Test datetime object
        test_datetime = datetime(2024, 1, 15, 14, 30, 0)
        result = self.service.handle_special_fields(
            test_datetime,
            FieldType.DATETIME
        )
        assert result == "2024-01-15 14:30:00"

    def test_handle_special_fields_multiple_choice(self):
        """Test handling of multiple choice fields"""
        # Single choice
        result = self.service.handle_special_fields(
            "Option A",
            FieldType.MULTIPLE_CHOICE
        )
        assert result == "Option A"
        
        # Multiple choices (checkbox)
        result = self.service.handle_special_fields(
            ["Option A", "Option B"],
            FieldType.CHECKBOX
        )
        assert result == "Option A, Option B"

    def test_handle_special_fields_file_upload(self):
        """Test handling of file upload fields"""
        # Single file
        result = self.service.handle_special_fields(
            "file_123",
            FieldType.FILE_UPLOAD
        )
        assert "drive.google.com/file/d/file_123/view" in result
        
        # Multiple files
        result = self.service.handle_special_fields(
            ["file_123", "file_456"],
            FieldType.FILE_UPLOAD
        )
        assert "file_123" in result and "file_456" in result

    def test_handle_special_fields_number(self):
        """Test handling of number fields"""
        # Integer
        result = self.service.handle_special_fields(
            42,
            FieldType.NUMBER
        )
        assert result == 42
        
        # Float
        result = self.service.handle_special_fields(
            3.14159,
            FieldType.NUMBER
        )
        assert result == 3.14  # Default 2 decimal places
        
        # String number
        result = self.service.handle_special_fields(
            "123.456",
            FieldType.NUMBER
        )
        assert result == 123.46

    def test_handle_special_fields_linear_scale(self):
        """Test handling of linear scale fields"""
        result = self.service.handle_special_fields(
            "4",
            FieldType.LINEAR_SCALE
        )
        assert result == 4
        
        result = self.service.handle_special_fields(
            5,
            FieldType.LINEAR_SCALE
        )
        assert result == 5

    def test_handle_special_fields_email(self):
        """Test handling of email fields"""
        result = self.service.handle_special_fields(
            "test@example.com",
            FieldType.EMAIL
        )
        assert result == "test@example.com"

    def test_handle_special_fields_url(self):
        """Test handling of URL fields"""
        result = self.service.handle_special_fields(
            "https://example.com",
            FieldType.URL
        )
        assert result == "https://example.com"

    def test_apply_formatting_rules(self):
        """Test applying formatting rules to data"""
        data = [
            ["Text", 123.456, None, "=SUM(A1:A2)"],
            ["More text", 789.123, "", "Normal text"]
        ]
        
        formatting_rules = FormattingRules(
            number_decimal_places=1,
            null_value_replacement="N/A",
            escape_formulas=True
        )
        
        result = self.service.apply_formatting_rules(data, formatting_rules)
        
        assert result[0][0] == "Text"
        assert result[0][1] == 123.456  # Numbers not formatted here
        assert result[0][2] == "N/A"
        assert result[1][3] == "Normal text"

    def test_validate_and_sanitize_data(self):
        """Test data validation and sanitization"""
        data = [
            ["John Doe", "=SUM(A1:A2)", "<script>alert('xss')</script>"],
            ["Jane Smith", "Normal text", "Safe content"]
        ]
        
        transformation_rules = [
            TransformationRule(
                field_id='q1',
                field_type=FieldType.TEXT,
                validation_rules={'required': True},
                sanitization_enabled=True
            ),
            TransformationRule(
                field_id='q2',
                field_type=FieldType.TEXT,
                sanitization_enabled=True
            ),
            TransformationRule(
                field_id='q3',
                field_type=FieldType.TEXT,
                sanitization_enabled=True
            )
        ]
        
        sanitized_data, validation_results = self.service.validate_and_sanitize_data(
            data, transformation_rules
        )
        
        # Check sanitization
        assert sanitized_data[0][1].startswith("'=")  # Formula escaped
        assert "&lt;script&gt;" in sanitized_data[0][2]  # HTML escaped
        
        # Check validation results
        assert len(validation_results) == 2
        assert validation_results[0].is_valid
        assert validation_results[1].is_valid

    def test_validate_and_sanitize_data_with_errors(self):
        """Test validation with errors"""
        data = [
            ["", "Valid text"],  # Empty required field
            ["Valid name", ""]
        ]
        
        transformation_rules = [
            TransformationRule(
                field_id='q1',
                field_type=FieldType.TEXT,
                validation_rules={'required': True},
                sanitization_enabled=True
            ),
            TransformationRule(
                field_id='q2',
                field_type=FieldType.TEXT,
                sanitization_enabled=True
            )
        ]
        
        sanitized_data, validation_results = self.service.validate_and_sanitize_data(
            data, transformation_rules
        )
        
        # First row should have validation error
        assert not validation_results[0].is_valid
        assert len(validation_results[0].errors) > 0
        assert "Required field is empty" in validation_results[0].errors[0]
        
        # Second row should be valid
        assert validation_results[1].is_valid

    def test_custom_formatting_rules(self):
        """Test custom formatting rules"""
        custom_formatting = FormattingRules(
            date_format="%d/%m/%Y",
            time_format="%I:%M %p",
            datetime_format="%d/%m/%Y %I:%M %p",
            number_decimal_places=3,
            boolean_true_value="TRUE",
            boolean_false_value="FALSE",
            null_value_replacement="NULL",
            list_separator=" | ",
            max_cell_length=50
        )
        
        # Test date formatting
        result = self.service.handle_special_fields(
            "2024-01-15",
            FieldType.DATE,
            custom_formatting
        )
        assert result == "15/01/2024"
        
        # Test list separator
        result = self.service.handle_special_fields(
            ["A", "B", "C"],
            FieldType.CHECKBOX,
            custom_formatting
        )
        assert result == "A | B | C"

    def test_field_type_mapping(self):
        """Test mapping of Google Forms question types to field types"""
        # Test text question
        question_data = {'paragraph': False}
        field_type = self.service._map_question_type_to_field_type('text', question_data)
        assert field_type == FieldType.TEXT
        
        # Test paragraph question
        question_data = {'paragraph': True}
        field_type = self.service._map_question_type_to_field_type('text', question_data)
        assert field_type == FieldType.PARAGRAPH
        
        # Test checkbox question
        question_data = {'choice_type': 'CHECKBOX'}
        field_type = self.service._map_question_type_to_field_type('choice', question_data)
        assert field_type == FieldType.CHECKBOX
        
        # Test dropdown question
        question_data = {'choice_type': 'DROP_DOWN'}
        field_type = self.service._map_question_type_to_field_type('choice', question_data)
        assert field_type == FieldType.DROPDOWN
        
        # Test datetime question
        question_data = {'include_time': True}
        field_type = self.service._map_question_type_to_field_type('date', question_data)
        assert field_type == FieldType.DATETIME

    def test_extract_answer_value_different_types(self):
        """Test extracting answer values for different field types"""
        # Text answer
        answer_data = {
            'textAnswers': {
                'answers': [{'value': 'Test answer'}]
            }
        }
        result = self.service._extract_answer_value(answer_data, FieldType.TEXT)
        assert result == 'Test answer'
        
        # Checkbox answer (multiple values)
        answer_data = {
            'textAnswers': {
                'answers': [
                    {'value': 'Option 1'},
                    {'value': 'Option 2'}
                ]
            }
        }
        result = self.service._extract_answer_value(answer_data, FieldType.CHECKBOX)
        assert result == ['Option 1', 'Option 2']
        
        # File upload answer
        answer_data = {
            'fileUploadAnswers': {
                'answers': [
                    {'fileId': 'file_123'},
                    {'fileId': 'file_456'}
                ]
            }
        }
        result = self.service._extract_answer_value(answer_data, FieldType.FILE_UPLOAD)
        assert result == ['file_123', 'file_456']
        
        # Scale answer
        answer_data = {
            'textAnswers': {
                'answers': [{'value': '4'}]
            }
        }
        result = self.service._extract_answer_value(answer_data, FieldType.LINEAR_SCALE)
        assert result == 4

    def test_sanitization_security(self):
        """Test security-focused sanitization"""
        formatting = FormattingRules(escape_formulas=True)
        
        # Test formula escaping
        dangerous_values = [
            "=SUM(A1:A10)",
            "@SUM(A1:A10)",
            "+SUM(A1:A10)",
            "-SUM(A1:A10)",
            " =SUM(A1:A10)"  # With leading space
        ]
        
        for value in dangerous_values:
            sanitized = self.service._sanitize_value(value, formatting)
            assert sanitized.startswith("'"), f"Formula not escaped: {value} -> {sanitized}"
        
        # Test HTML escaping
        html_value = "<script>alert('xss')</script>"
        sanitized = self.service._sanitize_value(html_value, formatting)
        assert "&lt;script&gt;" in sanitized
        assert "&lt;/script&gt;" in sanitized

    def test_error_handling(self):
        """Test error handling in transformation"""
        # Test with malformed response data
        malformed_responses = [
            {
                'responseId': 'resp_001',
                # Missing createTime and other required fields
                'answers': {
                    'q1': {
                        'textAnswers': {
                            'answers': [{'value': 'Test'}]
                        }
                    }
                }
            }
        ]
        
        # Should not raise exception, but handle gracefully
        result = self.service.transform_form_responses(
            malformed_responses,
            self.sample_form_schema
        )
        
        assert len(result) == 1
        assert result[0][0] == 'resp_001'  # Response ID should be present

    def test_large_data_handling(self):
        """Test handling of large data values"""
        formatting = FormattingRules(max_cell_length=100)
        
        # Test long text truncation
        long_text = "A" * 200
        result = self.service._handle_text_field(long_text, formatting)
        assert len(result) == 100
        assert result.endswith("...")

    def test_edge_cases(self):
        """Test various edge cases"""
        # Empty form schema
        empty_schema = {'questions': []}
        result = self.service.transform_form_responses([], empty_schema)
        assert result == []
        
        # Response with no answers
        response_no_answers = {
            'responseId': 'resp_empty',
            'createTime': '2024-01-15T10:30:00Z',
            'respondentEmail': 'test@example.com',
            'answers': {}
        }
        
        result = self.service.transform_form_responses(
            [response_no_answers],
            self.sample_form_schema
        )
        
        assert len(result) == 1
        assert result[0][0] == 'resp_empty'
        # All question answers should be empty/default values
        for i in range(3, len(result[0])):  # Skip metadata columns
            assert result[0][i] in ['', 0, None] or 'N/A' in str(result[0][i])

    def test_logging(self):
        """Test that appropriate logging occurs"""
        with patch.object(self.service.logger, 'warning') as mock_warning:
            # Test with invalid email to trigger warning
            self.service.handle_special_fields(
                "invalid-email",
                FieldType.EMAIL
            )
            
            # Should log warning about invalid email format
            mock_warning.assert_called()
            
            # Test with invalid URL
            self.service.handle_special_fields(
                "not-a-url",
                FieldType.URL
            )
            
            # Should log warning about invalid URL format
            assert mock_warning.call_count >= 2