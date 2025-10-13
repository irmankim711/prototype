#!/usr/bin/env python3
"""
Test Preview Endpoint
Simple script to test the ConvertAPI preview functionality
"""

import os
import sys
import requests

def test_preview_endpoint():
    """Test the preview endpoint directly"""

    # Set environment variable
    os.environ['CONVERT_API_SECRET'] = 'iQMCycsKxTXbJVsrWZgt27v5qIBYerYY'

    try:
        # Test the ConvertAPI service directly
        from app.services.convertapi_service import convertapi_service

        print("🔧 Testing ConvertAPI service...")

        # Find test DOCX file
        test_file = os.path.join(os.getcwd(), 'templates', 'Temp1.docx')

        if not os.path.exists(test_file):
            print("❌ Test file not found")
            return False

        print(f"📄 Using test file: {test_file}")

        # Generate preview
        success, message, html_path = convertapi_service.convert_docx_to_html_preview(test_file)

        if success and html_path:
            print(f"✅ Preview generated: {html_path}")

            # Check file size
            file_size = os.path.getsize(html_path)
            print(f"📏 HTML file size: {file_size} bytes")

            # Try to serve the file through the API
            import requests

            try:
                # Test if server is running
                response = requests.get('http://127.0.0.1:5000/api/excel-to-pdf/supported-formats', timeout=5)
                if response.status_code == 200:
                    print("✅ Backend server is running")

                    # Test the static file serving
                    preview_filename = os.path.basename(html_path)
                    preview_url = f"http://127.0.0.1:5000/static/previews/{preview_filename}"

                    preview_response = requests.get(preview_url, timeout=5)
                    if preview_response.status_code == 200:
                        print(f"✅ Preview file accessible at: {preview_url}")
                        print(f"📏 Served content length: {len(preview_response.text)} characters")
                        return True
                    else:
                        print(f"❌ Preview file not accessible: {preview_response.status_code}")

                        # Copy the file to the static directory
                        import shutil
                        static_preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
                        os.makedirs(static_preview_dir, exist_ok=True)

                        static_preview_path = os.path.join(static_preview_dir, preview_filename)
                        shutil.copy2(html_path, static_preview_path)
                        print(f"📁 Copied preview to: {static_preview_path}")

                        # Test again
                        preview_response = requests.get(preview_url, timeout=5)
                        if preview_response.status_code == 200:
                            print(f"✅ Preview file now accessible at: {preview_url}")
                            return True
                        else:
                            print(f"❌ Still can't access preview: {preview_response.status_code}")
                else:
                    print("❌ Backend server not running")

            except requests.exceptions.ConnectionError:
                print("❌ Backend server not accessible")

        else:
            print(f"❌ Preview generation failed: {message}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    return False

if __name__ == "__main__":
    print("🧪 Testing Preview Endpoint")
    print("=" * 40)

    if test_preview_endpoint():
        print("\n🎉 Preview functionality is working!")
        print("You can now access report previews at: http://127.0.0.1:5000/api/excel-to-pdf/preview/40")
    else:
        print("\n❌ Preview functionality needs more work")