"""
ConvertAPI Service for Document Conversion
Handles DOCX to PDF conversion using ConvertAPI
"""

import os
import logging
import requests
import tempfile
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from flask import current_app

logger = logging.getLogger(__name__)

class ConvertAPIService:
    """Service for converting documents using ConvertAPI"""

    def __init__(self):
        self.api_key = os.getenv('CONVERT_API_SECRET')
        self.base_url = "https://v2.convertapi.com"
        self.timeout = 120  # 2 minutes timeout for conversion

        if not self.api_key:
            logger.warning("ConvertAPI key not found in environment variables (CONVERT_API_SECRET)")

    def convert_docx_to_pdf(self, docx_path: str, output_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Convert DOCX file to PDF using ConvertAPI

        Args:
            docx_path: Path to the DOCX file
            output_path: Optional output path for PDF (if None, auto-generated)

        Returns:
            Tuple of (success, message, pdf_path)
        """
        try:
            if not self.api_key:
                return False, "ConvertAPI key not configured", None

            if not os.path.exists(docx_path):
                return False, f"Source file not found: {docx_path}", None

            # Generate output path if not provided
            if not output_path:
                docx_file = Path(docx_path)
                output_dir = docx_file.parent / 'pdfs'
                output_dir.mkdir(exist_ok=True)
                output_path = str(output_dir / f"{docx_file.stem}.pdf")

            logger.info(f"Converting DOCX to PDF: {docx_path} -> {output_path}")

            # Prepare the API request
            url = f"{self.base_url}/convert/docx/to/pdf"

            # Read the DOCX file
            with open(docx_path, 'rb') as file:
                files = {
                    'File': (os.path.basename(docx_path), file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                }

                data = {
                    'StoreFile': 'true'  # Store file on ConvertAPI servers temporarily
                }

                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }

                # Make the conversion request
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout
                )

            if response.status_code == 200:
                result = response.json()

                if 'Files' in result and len(result['Files']) > 0:
                    # Download the converted PDF
                    pdf_url = result['Files'][0]['Url']
                    download_success = self._download_file(pdf_url, output_path)

                    if download_success:
                        logger.info(f"PDF conversion successful: {output_path}")
                        return True, "Conversion successful", output_path
                    else:
                        return False, "Failed to download converted PDF", None
                else:
                    return False, "No converted files received from ConvertAPI", None
            else:
                error_msg = f"ConvertAPI error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg, None

        except requests.exceptions.Timeout:
            return False, "Conversion timeout - file may be too large", None
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during conversion: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error during conversion: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def _download_file(self, url: str, output_path: str) -> bool:
        """Download file from URL to local path"""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(response.content)

            return True
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            return False

    def convert_docx_to_pdf_async(self, docx_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Start async conversion (for large files)

        Args:
            docx_path: Path to the DOCX file
            output_path: Optional output path for PDF

        Returns:
            Dictionary with task information
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': "ConvertAPI key not configured"}

            url = f"{self.base_url}/convert/docx/to/pdf"

            with open(docx_path, 'rb') as file:
                files = {
                    'File': (os.path.basename(docx_path), file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                }

                data = {
                    'StoreFile': 'true',
                    'Async': 'true'  # Enable async processing
                }

                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }

                response = requests.post(url, files=files, data=data, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'task_id': result.get('TaskId'),
                    'status_url': result.get('StatusUrl'),
                    'output_path': output_path
                }
            else:
                return {
                    'success': False,
                    'error': f"ConvertAPI error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_async_status(self, task_id: str) -> Dict[str, Any]:
        """Check status of async conversion task"""
        try:
            url = f"{self.base_url}/status/{task_id}"
            params = {'Secret': self.api_key}

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'Status': 'error',
                    'Error': f"Status check failed: {response.status_code}"
                }

        except Exception as e:
            return {'Status': 'error', 'Error': str(e)}

    def get_conversion_info(self) -> Dict[str, Any]:
        """Get information about ConvertAPI service"""
        return {
            'service': 'ConvertAPI',
            'configured': bool(self.api_key),
            'base_url': self.base_url,
            'supported_conversions': [
                'DOCX to PDF',
                'DOC to PDF',
                'HTML to PDF'
            ],
            'max_file_size': '50MB',
            'timeout': f"{self.timeout} seconds"
        }

    def convert_docx_to_html_preview(self, docx_path: str, output_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Convert DOCX file to HTML for preview using ConvertAPI

        Args:
            docx_path: Path to the DOCX file
            output_path: Optional output path for HTML (if None, auto-generated)

        Returns:
            Tuple of (success, message, html_path)
        """
        try:
            if not self.api_key:
                return False, "ConvertAPI key not configured", None

            if not os.path.exists(docx_path):
                return False, f"Source file not found: {docx_path}", None

            # Generate output path if not provided
            if not output_path:
                docx_file = Path(docx_path)
                output_dir = docx_file.parent / 'previews'
                output_dir.mkdir(exist_ok=True)
                output_path = str(output_dir / f"{docx_file.stem}_preview.html")

            logger.info(f"Converting DOCX to HTML preview: {docx_path} -> {output_path}")

            # Prepare the API request
            url = f"{self.base_url}/convert/docx/to/html"

            # Read the DOCX file
            with open(docx_path, 'rb') as file:
                files = {
                    'File': (os.path.basename(docx_path), file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                }

                data = {
                    'StoreFile': 'true'  # Store file on ConvertAPI servers temporarily
                }

                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }

                # Make the conversion request
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout
                )

            if response.status_code == 200:
                result = response.json()

                if 'Files' in result and len(result['Files']) > 0:
                    # Download the converted HTML
                    html_url = result['Files'][0]['Url']
                    download_success = self._download_file(html_url, output_path)

                    if download_success:
                        logger.info(f"HTML preview conversion successful: {output_path}")
                        return True, "Preview conversion successful", output_path
                    else:
                        return False, "Failed to download converted HTML preview", None
                else:
                    return False, "No converted files received from ConvertAPI", None
            else:
                error_msg = f"ConvertAPI error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg, None

        except requests.exceptions.Timeout:
            return False, "Preview conversion timeout - file may be too large", None
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during preview conversion: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error during preview conversion: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def test_connection(self) -> Dict[str, Any]:
        """Test ConvertAPI connection and credentials"""
        try:
            if not self.api_key:
                return {'success': False, 'error': "ConvertAPI key not configured"}

            # Use a simple test endpoint to verify credentials
            url = f"{self.base_url}/user"
            params = {'Secret': self.api_key}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                user_info = response.json()
                return {
                    'success': True,
                    'message': "ConvertAPI connection successful",
                    'user_info': user_info
                }
            else:
                return {
                    'success': False,
                    'error': f"Authentication failed: {response.status_code}"
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global service instance
convertapi_service = ConvertAPIService()