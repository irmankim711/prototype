#!/usr/bin/env python3
"""
Test if Gemini is actually working and generating suggestions
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_gemini_actual_generation():
    """Test if Gemini can actually generate content"""
    print("🧠 Testing Actual Gemini Content Generation...")
    
    try:
        from app.services.gemini_content_service import GeminiContentService
        
        service = GeminiContentService()
        
        if not service.is_available():
            print("❌ Gemini service not available")
            return False
        
        print("✅ Gemini service is available")
        
        # Test content generation
        test_data = {
            'data_info': {
                'type': 'excel',
                'name': 'Sales Data',
                'fields': [
                    {'name': 'Region', 'type': 'categorical'},
                    {'name': 'Revenue', 'type': 'numerical'},
                    {'name': 'Quarter', 'type': 'temporal'}
                ]
            },
            'context': {'existingElements': []},
            'prompt': 'Generate 3 visualization suggestions for this data'
        }
        
        print("📊 Testing with sample data...")
        result = service.generate_content_variations(test_data, "data_visualization")
        
        if result:
            print("✅ Content generation successful!")
            print(f"   Result type: {type(result)}")
            print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Show the actual content
            if isinstance(result, dict) and 'content' in result:
                content = result['content']
                print(f"   Content length: {len(str(content))} characters")
                print(f"   Content preview: {str(content)[:200]}...")
            else:
                print(f"   Full result: {result}")
            
            return True
        else:
            print("❌ Content generation failed - no result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini generation: {str(e)}")
        return False

def test_nextgen_ai_suggestions():
    """Test the Next-Gen Report Builder AI suggestions"""
    print("\n🎯 Testing Next-Gen Report Builder AI Suggestions...")
    
    try:
        from app.routes.nextgen_report_builder import (
            _generate_ai_suggestions_with_gemini,
            _get_fallback_suggestions
        )
        
        # Mock data source
        mock_data_source = {
            'type': 'excel',
            'name': 'Customer Analytics',
            'fields': [
                {'name': 'Age Group', 'type': 'categorical'},
                {'name': 'Purchase Amount', 'type': 'numerical'},
                {'name': 'Date', 'type': 'temporal'},
                {'name': 'Region', 'type': 'categorical'}
            ],
            'recordCount': 500
        }
        
        context = {'existingElements': []}
        
        print("📊 Testing AI suggestions generation...")
        ai_suggestions = _generate_ai_suggestions_with_gemini(mock_data_source, context)
        
        if ai_suggestions:
            print(f"✅ AI Suggestions Generated: {len(ai_suggestions)} suggestions")
            for i, suggestion in enumerate(ai_suggestions, 1):
                print(f"   {i}. {suggestion.get('title', 'Untitled')}")
                print(f"      - Chart Type: {suggestion.get('chartType', 'unknown')}")
                print(f"      - Confidence: {suggestion.get('confidence', 0):.2f}")
                print(f"      - Preview: {suggestion.get('preview', 'No preview')[:60]}...")
            
            return True
        else:
            print("⚠️ AI suggestions not generated, testing fallback...")
            
            # Test fallback
            fallback_suggestions = _get_fallback_suggestions(mock_data_source)
            
            if fallback_suggestions:
                print(f"✅ Fallback Suggestions Generated: {len(fallback_suggestions)} suggestions")
                for i, suggestion in enumerate(fallback_suggestions, 1):
                    print(f"   {i}. {suggestion.get('title', 'Untitled')}")
                    print(f"      - Chart Type: {suggestion.get('chartType', 'unknown')}")
                    print(f"      - Confidence: {suggestion.get('confidence', 0):.2f}")
                
                print("\n💡 Note: Fallback suggestions are working, but Gemini AI suggestions are not.")
                print("   This means your Gemini service is available but not generating content.")
                return False
            else:
                print("❌ No suggestions generated at all")
                return False
        
    except Exception as e:
        print(f"❌ Error testing Next-Gen AI suggestions: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("GEMINI ACTUAL FUNCTIONALITY TEST")
    print("=" * 70)
    
    # Test 1: Direct Gemini generation
    gemini_working = test_gemini_actual_generation()
    
    # Test 2: Next-Gen Report Builder integration
    nextgen_working = test_nextgen_ai_suggestions()
    
    print("\n" + "=" * 70)
    if gemini_working and nextgen_working:
        print("🎉 GEMINI IS FULLY FUNCTIONAL!")
        print("Both direct generation and Next-Gen integration are working!")
    elif gemini_working:
        print("⚠️ GEMINI PARTIALLY WORKING")
        print("Direct generation works, but Next-Gen integration has issues")
    else:
        print("❌ GEMINI NOT WORKING")
        print("Check your API key and service configuration")
    print("=" * 70)

