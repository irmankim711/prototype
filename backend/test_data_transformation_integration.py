"""
Integration test for Data Transformation Service with Google Forms Service

This test demonstrates how the Data Transformation Service integrates with
the existing Google Forms Service to transform form responses into sheet format.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_transformation_service import (
    DataTransformationService,
    TransformationRule,
    FormattingRules,
    FieldType
)


def test_integration_with_google_forms_data():
    """Test integration with realistic Google Forms data"""
    
    # Initialize the transformation service
    transformation_service = DataTransformationService()
    
    # Sample form schema (as would come from Google Forms Service)
    form_schema = {
        'form_id': 'sample_form_123',
        'title': 'Customer Feedback Survey',
        'description': 'Please provide your feedback about our service',
        'questions': [
            {
                'item_id': '1a2b3c4d',
                'title': 'What is your name?',
                'question_type': 'text',
                'required': True
            },
            {
                'item_id': '2b3c4d5e',
                'title': 'Email address',
                'question_type': 'text',
                'required': True
            },
            {
                'item_id': '3c4d5e6f',
                'title': 'How satisfied are you with our service?',
                'question_type': 'scale',
                'low': 1,
                'high': 5,
                'low_label': 'Very Dissatisfied',
                'high_label': 'Very Satisfied'
            },
            {
                'item_id': '4d5e6f7g',
                'title': 'Which features do you use most?',
                'question_type': 'choice',
                'choice_type': 'CHECKBOX',
                'options': ['Feature A', 'Feature B', 'Feature C', 'Feature D']
            },
            {
                'item_id': '5e6f7g8h',
                'title': 'When did you first use our service?',
                'question_type': 'date'
            },
            {
                'item_id': '6f7g8h9i',
                'title': 'Please upload any supporting documents',
                'question_type': 'file_upload'
            },
            {
                'item_id': '7g8h9i0j',
                'title': 'Additional comments',
                'question_type': 'text',
                'paragraph': True
            }
        ]
    }
    
    # Sample form responses (as would come from Google Forms API)
    form_responses = [
        {
            'responseId': 'response_001',
            'createTime': '2024-01-15T10:30:00Z',
            'respondentEmail': 'john.doe@example.com',
            'answers': {
                '1a2b3c4d': {
                    'textAnswers': {
                        'answers': [{'value': 'John Doe'}]
                    }
                },
                '2b3c4d5e': {
                    'textAnswers': {
                        'answers': [{'value': 'john.doe@example.com'}]
                    }
                },
                '3c4d5e6f': {
                    'textAnswers': {
                        'answers': [{'value': '4'}]
                    }
                },
                '4d5e6f7g': {
                    'textAnswers': {
                        'answers': [
                            {'value': 'Feature A'},
                            {'value': 'Feature C'}
                        ]
                    }
                },
                '5e6f7g8h': {
                    'textAnswers': {
                        'answers': [{'value': '2023-06-15'}]
                    }
                },
                '6f7g8h9i': {
                    'fileUploadAnswers': {
                        'answers': [
                            {'fileId': 'file_abc123'},
                            {'fileId': 'file_def456'}
                        ]
                    }
                },
                '7g8h9i0j': {
                    'textAnswers': {
                        'answers': [{'value': 'Great service overall! Very happy with the support team.'}]
                    }
                }
            }
        },
        {
            'responseId': 'response_002',
            'createTime': '2024-01-15T14:45:00Z',
            'respondentEmail': 'jane.smith@example.com',
            'answers': {
                '1a2b3c4d': {
                    'textAnswers': {
                        'answers': [{'value': 'Jane Smith'}]
                    }
                },
                '2b3c4d5e': {
                    'textAnswers': {
                        'answers': [{'value': 'jane.smith@example.com'}]
                    }
                },
                '3c4d5e6f': {
                    'textAnswers': {
                        'answers': [{'value': '5'}]
                    }
                },
                '4d5e6f7g': {
                    'textAnswers': {
                        'answers': [
                            {'value': 'Feature B'},
                            {'value': 'Feature D'}
                        ]
                    }
                },
                '5e6f7g8h': {
                    'textAnswers': {
                        'answers': [{'value': '2023-03-20'}]
                    }
                },
                # No file upload for this response
                '7g8h9i0j': {
                    'textAnswers': {
                        'answers': [{'value': 'Could use some improvements in the mobile app.'}]
                    }
                }
            }
        }
    ]
    
    print("=== Data Transformation Service Integration Test ===\n")
    
    # Step 1: Generate headers
    print("1. Generating headers...")
    headers = transformation_service.generate_headers(
        form_schema,
        include_metadata=True
    )
    
    print(f"Generated headers: {headers}")
    print(f"Number of columns: {len(headers)}\n")
    
    # Step 2: Transform responses
    print("2. Transforming form responses...")
    transformed_data = transformation_service.transform_form_responses(
        form_responses,
        form_schema
    )
    
    print(f"Transformed {len(transformed_data)} responses")
    print(f"Each row has {len(transformed_data[0])} columns\n")
    
    # Step 3: Display the results in a table format
    print("3. Transformed data (first few columns):")
    print("-" * 100)
    
    # Print headers
    header_row = " | ".join(f"{h[:15]:<15}" for h in headers[:6])
    print(f"| {header_row} |")
    print("-" * 100)
    
    # Print data rows
    for i, row in enumerate(transformed_data):
        data_row = " | ".join(f"{str(cell)[:15]:<15}" for cell in row[:6])
        print(f"| {data_row} |")
    
    print("-" * 100)
    print()
    
    # Step 4: Test custom transformation rules
    print("4. Testing custom transformation rules...")
    
    custom_rules = [
        TransformationRule(
            field_id='1a2b3c4d',
            field_type=FieldType.TEXT,
            custom_header='Customer Name',
            validation_rules={'required': True, 'max_length': 100}
        ),
        TransformationRule(
            field_id='2b3c4d5e',
            field_type=FieldType.EMAIL,
            custom_header='Email Address',
            validation_rules={'required': True}
        ),
        TransformationRule(
            field_id='3c4d5e6f',
            field_type=FieldType.LINEAR_SCALE,
            custom_header='Satisfaction Score'
        ),
        TransformationRule(
            field_id='4d5e6f7g',
            field_type=FieldType.CHECKBOX,
            custom_header='Features Used'
        ),
        TransformationRule(
            field_id='5e6f7g8h',
            field_type=FieldType.DATE,
            custom_header='First Use Date'
        ),
        TransformationRule(
            field_id='6f7g8h9i',
            field_type=FieldType.FILE_UPLOAD,
            custom_header='Supporting Documents'
        ),
        TransformationRule(
            field_id='7g8h9i0j',
            field_type=FieldType.PARAGRAPH,
            custom_header='Comments',
            include_in_export=True  # Include long text
        )
    ]
    
    # Generate custom headers
    custom_headers = transformation_service.generate_headers(
        form_schema,
        transformation_rules=custom_rules,
        include_metadata=True
    )
    
    print(f"Custom headers: {custom_headers}\n")
    
    # Step 5: Test custom formatting rules
    print("5. Testing custom formatting rules...")
    
    custom_formatting = FormattingRules(
        date_format="%B %d, %Y",  # January 15, 2024
        list_separator=" | ",
        null_value_replacement="N/A",
        max_cell_length=50
    )
    
    # Transform with custom rules and formatting
    custom_transformed_data = transformation_service.transform_form_responses(
        form_responses,
        form_schema,
        transformation_rules=custom_rules,
        formatting_rules=custom_formatting
    )
    
    print("Custom formatted data (sample):")
    print(f"Date format: {custom_transformed_data[0][7]}")  # First use date
    print(f"Features format: {custom_transformed_data[0][6]}")  # Features used
    print()
    
    # Step 6: Test validation and sanitization
    print("6. Testing validation and sanitization...")
    
    # Create test data with potential security issues
    test_data = [
        ["John Doe", "=SUM(A1:A10)", "<script>alert('xss')</script>"],
        ["Jane Smith", "normal@email.com", "Safe content"]
    ]
    
    test_rules = [
        TransformationRule(
            field_id='name',
            field_type=FieldType.TEXT,
            validation_rules={'required': True},
            sanitization_enabled=True
        ),
        TransformationRule(
            field_id='email',
            field_type=FieldType.EMAIL,
            sanitization_enabled=True
        ),
        TransformationRule(
            field_id='comment',
            field_type=FieldType.TEXT,
            sanitization_enabled=True
        )
    ]
    
    sanitized_data, validation_results = transformation_service.validate_and_sanitize_data(
        test_data, test_rules
    )
    
    print("Original data:", test_data[0])
    print("Sanitized data:", sanitized_data[0])
    print("Validation passed:", validation_results[0].is_valid)
    print("Warnings:", validation_results[0].warnings)
    print()
    
    # Step 7: Test special field handling
    print("7. Testing special field handling...")
    
    # Test different field types
    test_cases = [
        (FieldType.DATE, "2024-01-15", "Date field"),
        (FieldType.TIME, "14:30:00", "Time field"),
        (FieldType.DATETIME, "2024-01-15T14:30:00Z", "DateTime field"),
        (FieldType.NUMBER, "123.456", "Number field"),
        (FieldType.CHECKBOX, ["Option A", "Option B"], "Checkbox field"),
        (FieldType.FILE_UPLOAD, ["file_123", "file_456"], "File upload field"),
        (FieldType.EMAIL, "test@example.com", "Email field"),
        (FieldType.URL, "https://example.com", "URL field")
    ]
    
    for field_type, value, description in test_cases:
        result = transformation_service.handle_special_fields(value, field_type)
        print(f"{description}: {value} -> {result}")
    
    print("\n=== Integration Test Completed Successfully ===")
    
    return {
        'headers': headers,
        'transformed_data': transformed_data,
        'custom_headers': custom_headers,
        'custom_data': custom_transformed_data,
        'validation_results': validation_results
    }


if __name__ == "__main__":
    # Run the integration test
    results = test_integration_with_google_forms_data()
    
    print(f"\nTest Results Summary:")
    print(f"- Headers generated: {len(results['headers'])}")
    print(f"- Responses transformed: {len(results['transformed_data'])}")
    print(f"- Custom headers: {len(results['custom_headers'])}")
    print(f"- Validation checks: {len(results['validation_results'])}")
    print(f"- All validations passed: {all(r.is_valid for r in results['validation_results'])}")