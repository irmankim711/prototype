import os
from backend.app.services.docx_preview_service import docx_preview_service

# Test with a sample DOCX file if it exists
sample_docx = 'test_output/test_document.docx'

if os.path.exists(sample_docx):
    print(f'Found sample DOCX file: {sample_docx}')
    try:
        html_file_path, html_content = docx_preview_service.convert_docx_to_html(sample_docx)
        print(f'Successfully converted to HTML: {html_file_path}')
        print(f'HTML content length: {len(html_content)} characters')
        print('Preview URL:', docx_preview_service.get_preview_url(sample_docx))
    except Exception as e:
        print(f'Error converting DOCX to HTML: {e}')
else:
    print(f'Sample DOCX file not found: {sample_docx}')
    print('Available files in test_output:')
    if os.path.exists('test_output'):
        for file in os.listdir('test_output'):
            print(f'  {file}')
