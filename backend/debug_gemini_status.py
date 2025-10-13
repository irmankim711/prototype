#!/usr/bin/env python3
"""
Debug script to show exact Gemini service status
"""

import os
import sys

def debug_gemini_status():
    """Show detailed Gemini service status"""
    print("🔍 DEBUGGING GEMINI SERVICE STATUS")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    gemini_key = os.getenv('GEMINI_API_KEY')
    google_ai_key = os.getenv('GOOGLE_AI_API_KEY')
    
    print(f"   GEMINI_API_KEY: {'✅ Present' if gemini_key else '❌ Missing'}")
    if gemini_key:
        print(f"      Length: {len(gemini_key)} characters")
        print(f"      Starts with: {gemini_key[:8]}...")
        print(f"      Ends with: ...{gemini_key[-4:]}")
    
    print(f"   GOOGLE_AI_API_KEY: {'✅ Present' if google_ai_key else '❌ Missing'}")
    if google_ai_key:
        print(f"      Length: {len(google_ai_key)} characters")
        print(f"      Starts with: {google_ai_key[:8]}...")
        print(f"      Ends with: ...{google_ai_key[-4:]}")
    
    # Check package availability
    print("\n📦 Package Availability:")
    try:
        import google.generativeai as genai
        print("   ✅ google.generativeai package: Available")
        print(f"      Version: {genai.__version__ if hasattr(genai, '__version__') else 'Unknown'}")
    except ImportError as e:
        print(f"   ❌ google.generativeai package: {e}")
        return
    
    # Test GeminiContentService
    print("\n🤖 GeminiContentService Debug:")
    try:
        sys.path.insert(0, str(os.path.dirname(__file__)))
        from app.services.gemini_content_service import GeminiContentService
        
        service = GeminiContentService()
        
        print(f"   Service instance created: ✅")
        print(f"   API Key attribute: {'✅ Present' if service.api_key else '❌ Missing'}")
        print(f"   Model attribute: {'✅ Present' if service.model else '❌ Missing'}")
        print(f"   is_available() result: {'✅ True' if service.is_available() else '❌ False'}")
        
        # Show the actual values
        if hasattr(service, 'api_key'):
            print(f"   Actual API key: {service.api_key[:8] if service.api_key else 'None'}...")
        if hasattr(service, 'model'):
            print(f"   Actual model: {type(service.model).__name__ if service.model else 'None'}")
        
        # Test the logic manually
        print(f"\n   Manual availability check:")
        print(f"      self.model is not None: {'✅ True' if service.model is not None else '❌ False'}")
        print(f"      self.api_key is not None: {'✅ True' if service.api_key is not None else '❌ False'}")
        print(f"      Both conditions: {'✅ True' if (service.model is not None and service.api_key is not None) else '❌ False'}")
        
    except Exception as e:
        print(f"   ❌ Error testing service: {e}")
    
    # Test AIService
    print("\n🤖 AIService Debug:")
    try:
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        print(f"   Service instance created: ✅")
        print(f"   OpenAI API Key: {'✅ Present' if ai_service.openai_api_key else '❌ Missing'}")
        print(f"   Google AI API Key: {'✅ Present' if ai_service.google_ai_api_key else '❌ Missing'}")
        print(f"   Gemini Available: {'✅ Yes' if ai_service.gemini_available else '❌ No'}")
        print(f"   Gemini Model Name: {ai_service.gemini_model_name}")
        
        # Show the actual values
        if hasattr(ai_service, 'google_ai_api_key'):
            print(f"   Actual Google AI key: {ai_service.google_ai_api_key[:8] if ai_service.google_ai_api_key else 'None'}...")
        
    except Exception as e:
        print(f"   ❌ Error testing AIService: {e}")
    
    # Test direct Gemini if API key is available
    print("\n🔮 Direct Gemini Test:")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            print("   ✅ Model initialized successfully")
            
            # Test generation
            response = model.generate_content("Say 'Hello' in one word.")
            if response and response.text:
                print(f"   ✅ Generation successful: {response.text}")
            else:
                print("   ❌ Generation failed - empty response")
                
        except Exception as e:
            print(f"   ❌ Direct Gemini test failed: {e}")
    else:
        print("   ⚠️ Skipping direct test - no API key")
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_gemini_status()

