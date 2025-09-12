#!/usr/bin/env python3
"""
Test Gemini AI Integration for Next-Gen Report Builder
Tests the AI suggestion functionality with your existing Gemini configuration
"""

import sys
import os
import json
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_ai_services_availability():
    """Test if AI services are properly configured and available"""
    print("🤖 Testing AI Services Availability...")
    
    try:
        from app.services.ai_service import AIService
        from app.services.gemini_content_service import GeminiContentService
        
        # Test AIService with Gemini
        ai_service = AIService()
        print(f"✅ AIService initialized")
        print(f"   - OpenAI API Key: {'✅ Present' if ai_service.openai_api_key else '❌ Missing'}")
        print(f"   - Google AI API Key: {'✅ Present' if ai_service.google_ai_api_key else '❌ Missing'}")
        print(f"   - Gemini Available: {'✅ Yes' if ai_service.gemini_available else '❌ No'}")
        print(f"   - Gemini Model: {ai_service.gemini_model_name}")
        
        # Test GeminiContentService
        gemini_service = GeminiContentService()
        print(f"✅ GeminiContentService initialized")
        print(f"   - Service Available: {'✅ Yes' if gemini_service.is_available() else '❌ No'}")
        
        return ai_service.gemini_available or gemini_service.is_available()
        
    except Exception as e:
        print(f"❌ Error initializing AI services: {str(e)}")
        return False

def test_ai_suggestions_generation():
    """Test AI suggestions generation with mock data"""
    print("\n🧠 Testing AI Suggestions Generation...")
    
    try:
        # Import the suggestion functions
        from app.routes.nextgen_report_builder import (
            _generate_ai_suggestions_with_gemini,
            _get_fallback_suggestions
        )
        
        # Mock data source info
        mock_data_source = {
            'type': 'excel',
            'name': 'Sales Performance Data',
            'fields': [
                {'name': 'Region', 'type': 'categorical'},
                {'name': 'Quarter', 'type': 'temporal'},
                {'name': 'Revenue', 'type': 'numerical'},
                {'name': 'Profit Margin', 'type': 'numerical'},
                {'name': 'Customer Count', 'type': 'numerical'}
            ],
            'recordCount': 150,
            'sampleData': [
                {'Region': 'North', 'Quarter': 'Q1', 'Revenue': 120000},
                {'Region': 'South', 'Quarter': 'Q1', 'Revenue': 98000}
            ]
        }
        
        context = {'existingElements': []}
        
        print(f"📊 Mock Data Source: {mock_data_source['name']}")
        print(f"   - Fields: {len(mock_data_source['fields'])}")
        print(f"   - Record Count: {mock_data_source['recordCount']}")
        
        # Try AI suggestions first
        ai_suggestions = _generate_ai_suggestions_with_gemini(mock_data_source, context)
        
        if ai_suggestions:
            print(f"✅ AI Suggestions Generated: {len(ai_suggestions)} suggestions")
            for i, suggestion in enumerate(ai_suggestions, 1):
                print(f"   {i}. {suggestion.get('title', 'Untitled')}")
                print(f"      - Chart Type: {suggestion.get('chartType', 'unknown')}")
                print(f"      - Confidence: {suggestion.get('confidence', 0):.2f}")
                print(f"      - Preview: {suggestion.get('preview', 'No preview')[:60]}...")
        else:
            print("⚠️ AI suggestions not generated, testing fallback...")
            
            # Test fallback suggestions
            fallback_suggestions = _get_fallback_suggestions(mock_data_source)
            
            if fallback_suggestions:
                print(f"✅ Fallback Suggestions Generated: {len(fallback_suggestions)} suggestions")
                for i, suggestion in enumerate(fallback_suggestions, 1):
                    print(f"   {i}. {suggestion.get('title', 'Untitled')}")
                    print(f"      - Chart Type: {suggestion.get('chartType', 'unknown')}")
                    print(f"      - Confidence: {suggestion.get('confidence', 0):.2f}")
            else:
                print("❌ No suggestions generated")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI suggestions: {str(e)}")
        return False

def test_gemini_direct_integration():
    """Test direct Gemini integration"""
    print("\n🔮 Testing Direct Gemini Integration...")
    
    try:
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        if not ai_service.gemini_available:
            print("⚠️ Gemini not available, skipping direct test")
            return True  # Not a failure, just not available
        
        # Test Gemini JSON generation
        test_prompt = """
        Generate 3 visualization suggestions for a dataset with the following fields:
        - Region (categorical)
        - Quarter (temporal) 
        - Revenue (numerical)
        
        Return suggestions in JSON format with title, chartType, and confidence for each.
        """
        
        result = ai_service._gemini_generate_json(test_prompt)
        
        if result:
            print("✅ Gemini JSON generation successful")
            print(f"   Response keys: {list(result.keys())}")
            
            # Pretty print the result
            print("   Response preview:")
            print(json.dumps(result, indent=2)[:500] + "..." if len(str(result)) > 500 else json.dumps(result, indent=2))
            
            return True
        else:
            print("❌ Gemini JSON generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing direct Gemini integration: {str(e)}")
        return False

def test_environment_configuration():
    """Test environment configuration for AI services"""
    print("\n🔧 Testing Environment Configuration...")
    
    env_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_AI_API_KEY',
        'GEMINI_API_KEY',
        'GOOGLE_GEMINI_MODEL'
    ]
    
    config_status = {}
    
    for var in env_vars:
        value = os.getenv(var)
        config_status[var] = {
            'present': value is not None,
            'length': len(value) if value else 0
        }
        
        status = "✅ Present" if value else "❌ Missing"
        length_info = f" ({len(value)} chars)" if value else ""
        print(f"   {var}: {status}{length_info}")
    
    # Check if at least one AI service is configured
    ai_configured = any([
        config_status['OPENAI_API_KEY']['present'],
        config_status['GOOGLE_AI_API_KEY']['present'],
        config_status['GEMINI_API_KEY']['present']
    ])
    
    if ai_configured:
        print("✅ At least one AI service is configured")
        return True
    else:
        print("❌ No AI services are configured")
        return False

def test_api_endpoint_format():
    """Test that AI suggestions would be properly formatted for the API"""
    print("\n🔌 Testing API Endpoint Format...")
    
    try:
        from app.routes.nextgen_report_builder import _get_fallback_suggestions
        
        # Mock data source
        mock_data_source = {
            'type': 'form',
            'name': 'Customer Survey',
            'fields': [
                {'name': 'Age Group', 'type': 'categorical'},
                {'name': 'Satisfaction Score', 'type': 'numerical'},
                {'name': 'Purchase Date', 'type': 'temporal'}
            ],
            'recordCount': 250
        }
        
        suggestions = _get_fallback_suggestions(mock_data_source)
        
        # Simulate API response format
        api_response = {
            'success': True,
            'suggestions': suggestions,
            'dataSourceId': 'mock_form_123',
            'generatedAt': '2024-01-01T12:00:00Z',
            'aiGenerated': False  # Fallback suggestions
        }
        
        print("✅ API Response Format:")
        print(json.dumps(api_response, indent=2, default=str))
        
        # Validate required fields
        required_fields = ['id', 'title', 'chartType', 'confidence', 'preview', 'reasoning']
        
        for suggestion in suggestions:
            missing_fields = [field for field in required_fields if field not in suggestion]
            if missing_fields:
                print(f"❌ Suggestion missing fields: {missing_fields}")
                return False
        
        print(f"✅ All {len(suggestions)} suggestions have required fields")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API format: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("GEMINI AI INTEGRATION TEST FOR NEXT-GEN REPORT BUILDER")
    print("=" * 70)
    
    tests = [
        ("Environment Configuration", test_environment_configuration),
        ("AI Services Availability", test_ai_services_availability), 
        ("AI Suggestions Generation", test_ai_suggestions_generation),
        ("Direct Gemini Integration", test_gemini_direct_integration),
        ("API Endpoint Format", test_api_endpoint_format)
    ]
    
    all_passed = True
    ai_available = False
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                if test_name == "AI Services Availability" and result:
                    ai_available = True
            else:
                print(f"❌ {test_name} FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL AI INTEGRATION TESTS PASSED!")
        if ai_available:
            print("🤖 Gemini AI is properly configured and ready for use!")
        else:
            print("⚠️ AI services not fully configured, but fallback system works")
        print("The Next-Gen Report Builder can generate intelligent suggestions!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check your Gemini API configuration and dependencies")
    print("=" * 70)

