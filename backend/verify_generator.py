import sys
import os
import logging

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.report_generator import create_word_report, create_pdf_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_structured_generation():
    print("Testing structured report generation...")
    
    # Sample data mimicking the EditorState structure
    data = {
        "title": "Structured Report Test",
        "content": {
            "sections": [
                {"type": "heading", "content": "1. Introduction", "level": 1},
                {"type": "text", "content": "This report demonstrates the new structured content generation capabilities. It should handle various element types correctly."},
                
                {"type": "heading", "content": "2. Key Features", "level": 2},
                {"type": "list", "content": "Rich Text Support\nStructured Data Handling\nPDF and DOCX Output"},
                
                {"type": "heading", "content": "3. Analysis", "level": 2},
                {"type": "text", "content": "The system now parses the JSON structure directly instead of treating it as a flat string."},
                {"type": "quote", "content": "Innovation distinguishes between a leader and a follower."},
                
                {"type": "heading", "content": "4. Conclusion", "level": 1},
                {"type": "text", "content": "Verification complete."}
            ]
        }
    }
    
    # Test DOCX Generation
    try:
        docx_path = create_word_report('generic', data, output_path='test_structured.docx')
        print(f"✅ DOCX generated successfully: {docx_path}")
    except Exception as e:
        print(f"❌ DOCX generation failed: {e}")
        import traceback
        traceback.print_exc()

    # Test PDF Generation
    try:
        pdf_path = create_pdf_report('generic', data, output_path='test_structured.pdf')
        print(f"✅ PDF generated successfully: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_structured_generation()
