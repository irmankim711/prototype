#!/usr/bin/env python3
"""
Test script for the Enhanced Excel Pipeline Service
Demonstrates the new Excel generation capabilities
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_enhanced_excel_service():
    """Test the EnhancedExcelService directly"""
    print("🧪 Testing EnhancedExcelService...")
    
    try:
        from app.services.enhanced_excel_service import EnhancedExcelService
        
        # Create sample form data
        sample_data = [
            {
                'id': 1,
                'submitted_at': datetime.now().isoformat(),
                'submitter_email': 'user1@example.com',
                'submitter_name': 'John Doe',
                'status': 'submitted',
                'field_question_1': 'What is your favorite color?',
                'field_answer_1': 'Blue',
                'field_question_2': 'How satisfied are you?',
                'field_answer_2': 'Very satisfied',
                'field_comments': 'Great experience overall!'
            },
            {
                'id': 2,
                'submitted_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'submitter_email': 'user2@example.com',
                'submitter_name': 'Jane Smith',
                'status': 'submitted',
                'field_question_1': 'What is your favorite color?',
                'field_answer_1': 'Red',
                'field_question_2': 'How satisfied are you?',
                'field_answer_2': 'Satisfied',
                'field_comments': 'Good, but could be better'
            },
            {
                'id': 3,
                'submitted_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'submitter_email': 'user3@example.com',
                'submitter_name': 'Bob Johnson',
                'status': 'submitted',
                'field_question_1': 'What is your favorite color?',
                'field_answer_1': 'Green',
                'field_question_2': 'How satisfied are you?',
                'field_answer_2': 'Neutral',
                'field_comments': None  # Test missing field handling
            }
        ]
        
        # Initialize service with production config
        excel_service = EnhancedExcelService({
            'max_chunk_size': 100,
            'max_memory_mb': 128,
            'validation_enabled': True,
            'error_handling': 'continue',
            'compression_enabled': False
        })
        
        # Generate Excel file
        output_path = 'test_enhanced_excel_output.xlsx'
        
        print(f"📊 Generating Excel file with {len(sample_data)} records...")
        result = excel_service.generate_excel(
            data=sample_data,
            output_path=output_path,
            template_config={'name': 'Test Template'}
        )
        
        if result['success']:
            print("✅ Excel generation successful!")
            print(f"   📁 File: {result['file_path']}")
            print(f"   📏 Size: {result['file_size']} bytes")
            print(f"   📊 Rows: {result['total_rows']}")
            print(f"   ⏱️  Duration: {result['duration_seconds']:.2f} seconds")
            print(f"   🧠 Memory: {result['memory_usage_mb']:.1f} MB")
            print(f"   ✅ Validation: {result['validation_passed']}")
            print(f"   📈 Data Quality: {result['data_quality_score']:.1f}%")
            print(f"   🔧 Missing Fields Handled: {result['missing_fields_handled']}")
            
            # Clean up test file
            if os.path.exists(output_path):
                os.remove(output_path)
                print(f"   🗑️  Test file cleaned up")
        else:
            print("❌ Excel generation failed!")
            print(f"   Errors: {result['errors']}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_excel_pipeline_service():
    """Test the ExcelPipelineService"""
    print("\n🧪 Testing ExcelPipelineService...")
    
    try:
        from app.services.excel_pipeline_service import ExcelPipelineService
        
        # Create sample form data
        sample_data = [
            {
                'submission_id': 1,
                'submitted_at': datetime.now().isoformat(),
                'submitter_email': 'user1@example.com',
                'submitter_name': 'John Doe',
                'status': 'submitted',
                'field_question_1': 'What is your favorite color?',
                'field_answer_1': 'Blue',
                'field_question_2': 'How satisfied are you?',
                'field_answer_2': 'Very satisfied',
                'field_comments': 'Great experience overall!'
            },
            {
                'submission_id': 2,
                'submitted_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'submitter_email': 'user2@example.com',
                'submitter_name': 'Jane Smith',
                'status': 'submitted',
                'field_question_1': 'What is your favorite color?',
                'field_answer_1': 'Red',
                'field_question_2': 'How satisfied are you?',
                'field_answer_2': 'Satisfied',
                'field_comments': 'Good, but could be better'
            }
        ]
        
        # Initialize pipeline service
        pipeline_config = {
            'base_config': 'production',
            'excel_customizations': {
                'max_chunk_size': 50,
                'max_memory_mb': 64
            },
            'output_directory': 'test_reports',
            'filename_template': 'test_pipeline_{timestamp}_{uuid}.xlsx'
        }
        
        excel_pipeline = ExcelPipelineService(config=pipeline_config)
        
        # Progress callback
        def progress_callback(percentage, message):
            print(f"   📊 Progress: {percentage}% - {message}")
        
        print(f"📊 Running Excel pipeline with {len(sample_data)} records...")
        pipeline_result = excel_pipeline.generate_excel_pipeline(
            data=sample_data,
            pipeline_config={'filters': {'exclude_empty': True}},
            progress_callback=progress_callback
        )
        
        if pipeline_result['success']:
            print("✅ Excel pipeline successful!")
            print(f"   🆔 Pipeline ID: {pipeline_result['pipeline_id']}")
            print(f"   📁 File: {pipeline_result['excel_file_path']}")
            print(f"   📏 Size: {pipeline_result['excel_file_size']} bytes")
            print(f"   📊 Total Rows: {pipeline_result['total_rows']}")
            print(f"   ⏱️  Duration: {pipeline_result['duration_seconds']:.2f} seconds")
            print(f"   ✅ Validation: {pipeline_result['validation_passed']}")
            print(f"   📈 Data Quality: {pipeline_result['data_quality_score']:.1f}%")
            
            # Clean up test file
            if os.path.exists(pipeline_result['excel_file_path']):
                os.remove(pipeline_result['excel_file_path'])
                print(f"   🗑️  Test file cleaned up")
        else:
            print("❌ Excel pipeline failed!")
            print(f"   Errors: {pipeline_result['errors']}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_excel_config():
    """Test the Excel configuration system"""
    print("\n🧪 Testing Excel Configuration...")
    
    try:
        from app.config.excel_config import get_excel_config, customize_excel_config, validate_excel_config
        
        # Test different config types
        configs = ['default', 'large_dataset', 'small_dataset', 'high_quality', 'performance', 'production']
        
        for config_type in configs:
            config = get_excel_config(config_type)
            print(f"   📋 {config_type.upper()} config:")
            print(f"      Chunk size: {config['max_chunk_size']}")
            print(f"      Memory limit: {config['max_memory_mb']} MB")
            print(f"      Validation: {config['validation_enabled']}")
            print(f"      Error handling: {config['error_handling']}")
        
        # Test customization
        custom_config = customize_excel_config(
            base_config='production',
            customizations={
                'max_chunk_size': 200,
                'max_memory_mb': 128,
                'include_charts': True
            }
        )
        
        print(f"   🔧 Custom config:")
        print(f"      Chunk size: {custom_config['max_chunk_size']}")
        print(f"      Memory limit: {custom_config['max_memory_mb']} MB")
        print(f"      Charts: {custom_config['include_charts']}")
        
        # Test validation
        validated_config = validate_excel_config({
            'max_chunk_size': 9999,  # Should be capped
            'max_memory_mb': 9999,   # Should be capped
            'error_handling': 'invalid_value'  # Should be corrected
        })
        
        print(f"   ✅ Validated config:")
        print(f"      Chunk size: {validated_config['max_chunk_size']}")
        print(f"      Memory limit: {validated_config['max_memory_mb']} MB")
        print(f"      Error handling: {validated_config['error_handling']}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🚀 Enhanced Excel Pipeline Service Test Suite")
    print("=" * 50)
    
    # Test Excel configuration
    test_excel_config()
    
    # Test enhanced Excel service
    test_enhanced_excel_service()
    
    # Test Excel pipeline service
    test_excel_pipeline_service()
    
    print("\n🎉 All tests completed!")
    print("\n📚 Available API Endpoints:")
    print("   POST /api/v1/integrations/excel/enhanced-export")
    print("   GET  /api/v1/integrations/excel/pipeline-status/<pipeline_id>")
    print("\n📖 Usage Example:")
    print("   curl -X POST http://localhost:5000/api/v1/integrations/excel/enhanced-export \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -H 'Authorization: Bearer <your-jwt-token>' \\")
    print("        -d '{\"form_id\": 123, \"excel_config\": \"production\"}'")

if __name__ == "__main__":
    main()
