#!/usr/bin/env python3
"""
Test the DOCX preview service directly
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

try:
    from app.services.docx_preview_service import docx_preview_service
    print("✅ Successfully imported docx_preview_service")

    # Test with the sample DOCX file
    docx_path = 'test_output/test_document.docx'

    if os.path.exists(docx_path):
        print(f"📄 Found DOCX file: {docx_path}")
        print(f"📏 File size: {os.path.getsize(docx_path)} bytes")

        try:
            # Test conversion
            print("🔄 Converting DOCX to HTML...")
            html_file_path, html_content = docx_preview_service.convert_docx_to_html(docx_path)

            print("✅ Conversion successful!"            print(f"📁 HTML file path: {html_file_path}")
            print(f"📏 HTML content length: {len(html_content)} characters")

            # Check if HTML file was created
            if os.path.exists(html_file_path):
                print(f"✅ HTML file exists at: {html_file_path}")
                print(f"📏 HTML file size: {os.path.getsize(html_file_path)} bytes")

                # Test getting preview URL
                try:
                    preview_url = docx_preview_service.get_preview_url(docx_path)
                    print(f"🌐 Preview URL: {preview_url}")
                except Exception as e:
                    print(f"❌ Error getting preview URL: {e}")

            else:
                print(f"❌ HTML file was not created at: {html_file_path}")

        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            import traceback
            traceback.print_exc()

    else:
        print(f"❌ DOCX file not found: {docx_path}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running this from the correct directory")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
