#!/usr/bin/env python3
"""
Simple test to check if Gemini API key is working
"""

import os
import sys

def test_gemini_api_key():
    """Test if Gemini API key is present and valid"""
    print("🔑 Testing Gemini API Key...")
    
    # Check environment variables
    gemini_key = os.getenv('GEMINI_API_KEY')
    google_ai_key = os.getenv('GOOGLE_AI_API_KEY')
    
    print(f"GEMINI_API_KEY: {'✅ Present' if gemini_key else '❌ Missing'}")
    print(f"GOOGLE_AI_API_KEY: {'✅ Present' if google_ai_key else '❌ Missing'}")
    
    if gemini_key:
        print(f"   Length: {len(gemini_key)} characters")
        print(f"   Starts with: {gemini_key[:8]}...")
    
    if google_ai_key:
        print(f"   Length: {len(google_ai_key)} characters")
        print(f"   Starts with: {google_ai_key[:8]}...")
    
    # Try to import and test Gemini
    try:
        import google.generativeai as genai
        print("✅ google.generativeai package imported successfully")
        
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ Gemini model initialized successfully")
                
                # Test a simple generation
                response = model.generate_content("Say 'Hello, Gemini is working!' in one sentence.")
                if response and response.text:
                    print(f"✅ Gemini response: {response.text}")
                    return True
                else:
                    print("❌ Gemini response was empty")
                    return False
                    
            except Exception as e:
                print(f"❌ Error testing Gemini: {str(e)}")
                return False
        else:
            print("⚠️ No Gemini API key found, cannot test")
            return False
            
    except ImportError:
        print("❌ google.generativeai package not installed")
        print("   Install with: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_ai_service():
    """Test the AI service initialization"""
    print("\n🤖 Testing AI Service...")
    
    try:
        sys.path.insert(0, str(os.path.dirname(__file__)))
        from app.services.ai_service import AIService
        from app.services.gemini_content_service import GeminiContentService
        
        # Test AIService
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
        print(f"❌ Error testing AI service: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GEMINI API KEY TEST")
    print("=" * 60)
    
    # Test 1: Check API key
    api_key_working = test_gemini_api_key()
    
    # Test 2: Check AI service
    service_working = test_ai_service()
    
    print("\n" + "=" * 60)
    if api_key_working and service_working:
        print("🎉 GEMINI IS FULLY FUNCTIONAL!")
        print("Your API key is working and services are ready!")
    elif service_working:
        print("⚠️ GEMINI PARTIALLY WORKING")
        print("Services are available but API key may have issues")
    else:
        print("❌ GEMINI NOT WORKING")
        print("Check your API key and service configuration")
    print("=" * 60)

