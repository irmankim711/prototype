"""
Comprehensive tests for Enhanced Excel Service
Tests all edge cases and functionality
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

from app.services.enhanced_excel_service import (
    EnhancedExcelService, 
    ExcelValidationError, 
    DataProcessingError
)
from app.config.excel_config import get_excel_config, validate_excel_config

class TestEnhancedExcelService:
    """Test suite for Enhanced Excel Service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = self._create_test_data()
        self.service = EnhancedExcelService()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if hasattr(self, 'service'):
            self.service.cleanup()
        
        # Clean up temp files
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
    
    def _create_test_data(self) -> List[Dict[str, Any]]:
        """Create comprehensive test data with various edge cases"""
        test_data = []
        
        # Normal record
        test_data.append({
            'id': 1,
            'submitted_at': datetime.now(),
            'submitter_email': 'test@example.com',
            'submitter_name': 'Test User',
            'status': 'completed',
            'score': 95,
            'feedback': 'Great work!'
        })
        
        # Record with missing fields
        test_data.append({
            'id': 2,
            'submitted_at': datetime.now() - timedelta(hours=1),
            'submitter_email': None,  # Missing email
            'submitter_name': '',     # Empty name
            'status': None,           # None status
            'score': 87,
            'feedback': None          # None feedback
        })
        
        # Record with problematic field names
        test_data.append({
            'id': 3,
            'submitted_at': datetime.now() - timedelta(hours=2),
            'submitter_email': 'user2@example.com',
            'submitter_name': 'User Two',
            'status': 'pending',
            'score': 92,
            'feedback': 'Good job',
            'field/with/slashes': 'value1',
            'field[with]brackets': 'value2',
            'field\nwith\nnewlines': 'value3',
            'field\twith\ttabs': 'value4'
        })
        
        # Record with complex data types
        test_data.append({
            'id': 4,
            'submitted_at': datetime.now() - timedelta(hours=3),
            'submitter_email': 'user3@example.com',
            'submitter_name': 'User Three',
            'status': 'completed',
            'score': 78,
            'feedback': 'Needs improvement',
            'tags': ['tag1', 'tag2', 'tag3'],  # List
            'metadata': {'key1': 'value1', 'key2': 'value2'},  # Dict
            'is_active': True,  # Boolean
            'rating': 4.5  # Float
        })
        
        # Record with very long field names
        test_data.append({
            'id': 5,
            'submitted_at': datetime.now() - timedelta(hours=4),
            'submitter_email': 'user4@example.com',
            'submitter_name': 'User Four',
            'status': 'completed',
            'score': 88,
            'feedback': 'Excellent work',
            'very_long_field_name_that_exceeds_normal_excel_column_width_limits_and_should_be_truncated': 'long value',
            'another_extremely_long_field_name_with_special_characters_and_numbers_123_456_789': 'another long value'
        })
        
        # Record with special characters
        test_data.append({
            'id': 6,
            'submitted_at': datetime.now() - timedelta(hours=5),
            'submitter_email': 'user5@example.com',
            'submitter_name': 'User Five',
            'status': 'completed',
            'score': 91,
            'feedback': 'Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?',
            'unicode_field': 'Unicode: 你好世界 🌍 🚀',
            'html_field': '<p>HTML content</p>',
            'json_field': '{"nested": {"data": "value"}}'
        })
        
        return test_data
    
    def test_service_initialization(self):
        """Test service initialization with different configurations"""
        # Test default configuration
        service = EnhancedExcelService()
        assert service.max_chunk_size == 1000
        assert service.max_memory_mb == 512
        assert service.validation_enabled is True
        
        # Test custom configuration
        custom_config = {
            'max_chunk_size': 500,
            'max_memory_mb': 256,
            'validation_enabled': False
        }
        service = EnhancedExcelService(config=custom_config)
        assert service.max_chunk_size == 500
        assert service.max_memory_mb == 256
        assert service.validation_enabled is False
        
        service.cleanup()
    
    def test_input_validation(self):
        """Test input data validation"""
        # Test valid data
        self.service._validate_input_data(self.test_data)
        
        # Test empty data
        with pytest.raises(DataProcessingError, match="No data provided"):
            self.service._validate_input_data([])
        
        # Test invalid data type
        with pytest.raises(DataProcessingError, match="Data must be a list"):
            self.service._validate_input_data("invalid")
        
        # Test data with non-dict records
        invalid_data = [{'id': 1}, "not_a_dict", {'id': 2}]
        with pytest.raises(DataProcessingError, match="Record 1 is not a dictionary"):
            self.service._validate_input_data(invalid_data)
    
    def test_missing_field_handling(self):
        """Test handling of missing fields"""
        # Test record with missing standard fields
        incomplete_record = {'id': 999}
        processed_record = self.service._handle_missing_fields(incomplete_record)
        
        # Check that missing fields were added with defaults
        assert 'submitted_at' in processed_record
        assert 'submitter_email' in processed_record
        assert 'submitter_name' in processed_record
        assert 'status' in processed_record
        
        # Check that existing fields were preserved
        assert processed_record['id'] == 999
        
        # Test handling of None values
        record_with_nones = {
            'id': 888,
            'submitter_email': None,
            'submitter_name': None,
            'some_date': None
        }
        processed_record = self.service._handle_missing_fields(record_with_nones)
        
        assert processed_record['submitter_email'] == ''
        assert processed_record['submitter_name'] == 'Unknown'
        assert isinstance(processed_record['some_date'], datetime)
    
    def test_field_sanitization(self):
        """Test field name sanitization"""
        # Test problematic characters
        problematic_names = [
            'field/with/slashes',
            'field[with]brackets',
            'field\nwith\nnewlines',
            'field\twith\ttabs',
            'field?with?question?marks',
            'field*with*asterisks'
        ]
        
        for name in problematic_names:
            sanitized = self.service._sanitize_field_name(name)
            assert '/' not in sanitized
            assert '[' not in sanitized
            assert ']' not in sanitized
            assert '\n' not in sanitized
            assert '\t' not in sanitized
            assert '?' not in sanitized
            assert '*' not in sanitized
        
        # Test length limits
        very_long_name = 'a' * 100
        sanitized = self.service._sanitize_field_name(very_long_name)
        assert len(sanitized) <= 50
        assert sanitized.endswith('...')
        
        # Test empty/whitespace names
        empty_names = ['', '   ', '\n\t']
        for name in empty_names:
            sanitized = self.service._sanitize_field_name(name)
            assert sanitized.startswith('field_')
            assert len(sanitized) > 0
    
    def test_field_value_cleaning(self):
        """Test field value cleaning and standardization"""
        # Test None values
        assert self.service._clean_field_value(None) == ''
        
        # Test basic types
        assert self.service._clean_field_value("test") == "test"
        assert self.service._clean_field_value(123) == 123
        assert self.service._clean_field_value(45.67) == 45.67
        assert self.service._clean_field_value(True) is True
        
        # Test datetime
        test_date = datetime.now()
        cleaned_date = self.service._clean_field_value(test_date)
        assert isinstance(cleaned_date, str)
        assert test_date.strftime('%Y-%m-%d %H:%M:%S') == cleaned_date
        
        # Test lists
        test_list = ['item1', 'item2', None, 'item3']
        cleaned_list = self.service._clean_field_value(test_list)
        assert cleaned_list == 'item1, item2, , item3'
        
        # Test dictionaries
        test_dict = {'key1': 'value1', 'key2': 'value2'}
        cleaned_dict = self.service._clean_field_value(test_dict)
        assert isinstance(cleaned_dict, str)
        assert 'key1' in cleaned_dict
        assert 'value1' in cleaned_dict
    
    def test_data_processing_in_chunks(self):
        """Test data processing in memory-efficient chunks"""
        # Create large dataset
        large_dataset = []
        for i in range(2500):  # More than max_chunk_size
            large_dataset.append({
                'id': i,
                'submitted_at': datetime.now(),
                'submitter_email': f'user{i}@example.com',
                'submitter_name': f'User {i}',
                'status': 'completed',
                'score': i % 100
            })
        
        # Process data in chunks
        processed_data = self.service._process_data_in_chunks(large_dataset)
        
        # Verify all records were processed
        assert len(processed_data) == len(large_dataset)
        
        # Verify data integrity
        for i, record in enumerate(processed_data):
            assert record['id'] == i
            assert 'submitted_at' in record
            assert 'submitter_email' in record
            assert 'submitter_name' in record
            assert 'status' in record
            assert 'score' in record
    
    def test_excel_generation(self):
        """Test complete Excel generation process"""
        output_path = os.path.join(self.temp_dir, 'test_export.xlsx')
        
        # Generate Excel file
        result = self.service.generate_excel(
            data=self.test_data,
            output_path=output_path,
            template_config={'name': 'Test Template'}
        )
        
        # Verify success
        assert result['success'] is True
        assert result['file_path'] == output_path
        assert result['total_rows'] == len(self.test_data)
        assert result['processed_rows'] == len(self.test_data)
        assert result['file_size'] > 0
        assert result['duration_seconds'] > 0
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify file size
        assert os.path.getsize(output_path) > 0
    
    def test_excel_validation(self):
        """Test Excel output validation"""
        output_path = os.path.join(self.temp_dir, 'test_validation.xlsx')
        
        # Generate Excel file
        result = self.service.generate_excel(
            data=self.test_data,
            output_path=output_path
        )
        
        # Validate the generated file
        validation_result = self.service._validate_excel_output(output_path, self.test_data)
        
        # Verify validation passed
        assert validation_result['valid'] is True
        assert len(validation_result['errors']) == 0
        assert validation_result['file_size_mb'] > 0
        assert validation_result['row_count'] > 0
        assert validation_result['column_count'] > 0
        
        # Test validation of non-existent file
        non_existent_path = os.path.join(self.temp_dir, 'non_existent.xlsx')
        validation_result = self.service._validate_excel_output(non_existent_path, [])
        assert validation_result['valid'] is False
        assert len(validation_result['errors']) > 0
    
    def test_error_handling(self):
        """Test error handling during processing"""
        # Test with malformed data
        malformed_data = [
            {'id': 1, 'normal_field': 'value'},
            {'id': 2, 'field_with_exception': Exception('Test exception')},  # This will cause an error
            {'id': 3, 'normal_field': 'value'}
        ]
        
        # Process the data - should continue despite errors
        processed_data = self.service._process_data_in_chunks(malformed_data)
        
        # Should have processed all records
        assert len(processed_data) == len(malformed_data)
        
        # Check that error record was created
        error_records = [r for r in processed_data if r.get('status') == 'ERROR']
        assert len(error_records) == 1
        
        error_record = error_records[0]
        assert error_record['id'] == 'ERROR'
        assert 'error_message' in error_record
        assert 'original_data' in error_record
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets"""
        # Create very large dataset
        large_dataset = []
        for i in range(5000):
            large_dataset.append({
                'id': i,
                'field1': f'value1_{i}',
                'field2': f'value2_{i}',
                'field3': f'value3_{i}',
                'field4': f'value4_{i}',
                'field5': f'value5_{i}'
            })
        
        # Configure service for memory efficiency
        memory_efficient_service = EnhancedExcelService(config={
            'max_chunk_size': 200,
            'max_memory_mb': 128
        })
        
        try:
            output_path = os.path.join(self.temp_dir, 'memory_test.xlsx')
            
            # Generate Excel file
            result = memory_efficient_service.generate_excel(
                data=large_dataset,
                output_path=output_path
            )
            
            # Verify success
            assert result['success'] is True
            assert result['processed_rows'] == len(large_dataset)
            
            # Check memory usage
            memory_usage = result.get('memory_usage_mb', 0)
            if memory_usage > 0:
                assert memory_usage < 256  # Should be within configured limit
            
        finally:
            memory_efficient_service.cleanup()
    
    def test_progress_tracking(self):
        """Test progress tracking functionality"""
        progress_updates = []
        
        def progress_callback(percentage, message):
            progress_updates.append({'percentage': percentage, 'message': message})
        
        # Configure service with progress callback
        progress_service = EnhancedExcelService(config={
            'progress_callback': progress_callback
        })
        
        try:
            output_path = os.path.join(self.temp_dir, 'progress_test.xlsx')
            
            # Generate Excel file
            result = progress_service.generate_excel(
                data=self.test_data,
                output_path=output_path
            )
            
            # Verify progress updates were called
            assert len(progress_updates) > 0
            
            # Check that progress went from 0 to 100
            percentages = [update['percentage'] for update in progress_updates]
            assert min(percentages) >= 0
            assert max(percentages) <= 100
            
            # Check that we have meaningful progress messages
            messages = [update['message'] for update in progress_updates]
            assert any('Starting' in msg for msg in messages)
            assert any('completed' in msg for msg in messages)
            
        finally:
            progress_service.cleanup()
    
    def test_configuration_presets(self):
        """Test different configuration presets"""
        # Test large dataset configuration
        large_config = get_excel_config('large_dataset')
        assert large_config['max_chunk_size'] == 500
        assert large_config['max_memory_mb'] == 256
        assert large_config['compression_enabled'] is True
        
        # Test small dataset configuration
        small_config = get_excel_config('small_dataset')
        assert small_config['max_chunk_size'] == 100
        assert small_config['include_charts'] is True
        assert small_config['conditional_formatting'] is True
        
        # Test performance configuration
        perf_config = get_excel_config('performance')
        assert perf_config['max_chunk_size'] == 200
        assert perf_config['max_memory_mb'] == 128
        assert perf_config['validation_enabled'] is False
        
        # Test custom configuration
        custom_config = customize_excel_config(
            base_config='default',
            customizations={'max_chunk_size': 750, 'include_charts': True}
        )
        assert custom_config['max_chunk_size'] == 750
        assert custom_config['include_charts'] is True
        assert custom_config['max_memory_mb'] == 512  # Default value preserved
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test valid configuration
        valid_config = validate_excel_config({
            'max_chunk_size': 500,
            'max_memory_mb': 256
        })
        assert valid_config['max_chunk_size'] == 500
        assert valid_config['max_memory_mb'] == 256
        
        # Test configuration with out-of-bounds values
        invalid_config = validate_excel_config({
            'max_chunk_size': 20000,  # Too high
            'max_memory_mb': 10,      # Too low
            'max_field_name_length': 5  # Too low
        })
        assert invalid_config['max_chunk_size'] == 10000  # Capped
        assert invalid_config['max_memory_mb'] == 64      # Capped
        assert invalid_config['max_field_name_length'] == 10  # Capped
        
        # Test invalid enum values
        invalid_enum_config = validate_excel_config({
            'error_handling': 'invalid_value',
            'image_handling': 'invalid_option',
            'formula_handling': 'invalid_choice'
        })
        assert invalid_enum_config['error_handling'] == 'continue'  # Default
        assert invalid_enum_config['image_handling'] == 'skip'      # Default
        assert invalid_enum_config['formula_handling'] == 'text'    # Default

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
