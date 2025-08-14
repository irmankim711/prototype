import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not set in environment.")
    exit(1)

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(["Explain how AI works in a few words"])
    print("✅ Gemini API is working!")
    print("Response:", response.text)
except Exception as e:
    print("❌ Gemini API test failed:", e)
