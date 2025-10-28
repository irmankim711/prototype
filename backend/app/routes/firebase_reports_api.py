"""
Firebase Reports API Routes
Demonstrates how to create, upload, and manage reports using Firebase Storage + Firestore
"""

import os
import logging
import tempfile
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from ..decorators import require_auth, get_current_user_id
from ..services.firestore_report_service import firestore_report_service
from ..services.firebase_storage_service import firebase_storage_service

logger = logging.getLogger(__name__)

firebase_reports_bp = Blueprint('firebase_reports', __name__, url_prefix='/api/firebase-reports')

# Allowed file types for reports
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'xlsx', 'txt', 'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@firebase_reports_bp.route('/create', methods=['POST'])
@require_auth
def create_report():
    """
    Create a new report metadata in Firestore

    Request body:
    {
        "title": "Report Title",
        "description": "Report description",
        "reportType": "document",
        "templateId": "optional_template_id",
        "programId": "optional_program_id"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data or not data.get('title'):
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400

        # Create report in Firestore
        report_id = firestore_report_service.create_report(
            user_id=user_id,
            title=data.get('title'),
            description=data.get('description', ''),
            report_type=data.get('reportType', 'document'),
            template_id=data.get('templateId'),
            program_id=data.get('programId'),
            data_source=data.get('dataSource'),
            generation_config=data.get('generationConfig')
        )

        if not report_id:
            return jsonify({
                'success': False,
                'error': 'Failed to create report'
            }), 500

        logger.info(f"✅ Created report: {report_id} for user: {user_id}")

        return jsonify({
            'success': True,
            'reportId': report_id,
            'message': 'Report created successfully'
        })

    except Exception as e:
        logger.error(f"Error creating report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to create report'
        }), 500


@firebase_reports_bp.route('/upload/<report_id>', methods=['POST'])
@require_auth
def upload_report_file(report_id):
    """
    Upload a report file to Firebase Storage

    Multipart form data:
    - file: The report file to upload
    """
    try:
        user_id = get_current_user_id()

        # Verify report exists and belongs to user
        report = firestore_report_service.get_report(report_id)
        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404

        if report.get('userId') != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403

        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400

        # Save file temporarily
        file_extension = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        temp_path = os.path.join(tempfile.gettempdir(), f"report_{report_id}.{file_extension}")

        file.save(temp_path)

        # Update report status to generating
        firestore_report_service.update_report_status(
            report_id=report_id,
            status='generating'
        )

        # Upload to Firebase Storage and update Firestore
        download_url = firestore_report_service.save_report_file(
            report_id=report_id,
            file_path=temp_path,
            file_format=file_extension
        )

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not download_url:
            return jsonify({
                'success': False,
                'error': 'Failed to upload file to storage'
            }), 500

        logger.info(f"✅ Uploaded report file: {report_id}")

        return jsonify({
            'success': True,
            'reportId': report_id,
            'downloadUrl': download_url,
            'message': 'File uploaded successfully'
        })

    except Exception as e:
        logger.error(f"Error uploading report file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to upload file'
        }), 500


@firebase_reports_bp.route('/list', methods=['GET'])
@require_auth
def list_user_reports():
    """
    Get list of reports for current user

    Query params:
    - limit: Number of reports to return (default: 50)
    - status: Filter by status (optional)
    """
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 50, type=int)
        status_filter = request.args.get('status')

        reports = firestore_report_service.get_user_reports(
            user_id=user_id,
            limit=limit,
            status_filter=status_filter
        )

        # Format reports for response
        formatted_reports = []
        for report in reports:
            formatted_reports.append({
                'id': report.get('id'),
                'title': report.get('title'),
                'description': report.get('description'),
                'reportType': report.get('reportType'),
                'status': report.get('generationStatus'),
                'downloadUrl': report.get('downloadUrl'),
                'fileSize': report.get('fileSize'),
                'downloadCount': report.get('downloadCount', 0),
                'createdAt': report.get('createdAt'),
                'generatedAt': report.get('generatedAt')
            })

        return jsonify({
            'success': True,
            'reports': formatted_reports,
            'count': len(formatted_reports)
        })

    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to list reports'
        }), 500


@firebase_reports_bp.route('/<report_id>', methods=['GET'])
@require_auth
def get_report_details(report_id):
    """Get details of a specific report"""
    try:
        user_id = get_current_user_id()

        report = firestore_report_service.get_report(report_id)

        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404

        if report.get('userId') != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403

        # Format report data
        report_data = {
            'id': report.get('id'),
            'title': report.get('title'),
            'description': report.get('description'),
            'reportType': report.get('reportType'),
            'status': report.get('generationStatus'),
            'downloadUrl': report.get('downloadUrl'),
            'fileSize': report.get('fileSize'),
            'storagePath': report.get('storagePath'),
            'downloadCount': report.get('downloadCount', 0),
            'createdAt': report.get('createdAt'),
            'generatedAt': report.get('generatedAt'),
            'errorMessage': report.get('errorMessage')
        }

        return jsonify({
            'success': True,
            'report': report_data
        })

    except Exception as e:
        logger.error(f"Error getting report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get report'
        }), 500


@firebase_reports_bp.route('/<report_id>/download', methods=['GET'])
@require_auth
def download_report(report_id):
    """
    Download a report file
    Returns a redirect to the signed URL
    """
    try:
        user_id = get_current_user_id()

        report = firestore_report_service.get_report(report_id)

        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404

        if report.get('userId') != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403

        if report.get('generationStatus') != 'completed':
            return jsonify({
                'success': False,
                'error': 'Report not ready for download'
            }), 400

        storage_path = report.get('storagePath')
        if not storage_path:
            return jsonify({
                'success': False,
                'error': 'Report file not found'
            }), 404

        # Generate fresh signed URL (valid for 1 hour)
        download_url = firebase_storage_service.get_signed_url(
            storage_path=storage_path,
            expiration_hours=1
        )

        if not download_url:
            return jsonify({
                'success': False,
                'error': 'Failed to generate download URL'
            }), 500

        # Increment download count
        firestore_report_service.increment_download_count(report_id)

        logger.info(f"✅ Report downloaded: {report_id}")

        return jsonify({
            'success': True,
            'downloadUrl': download_url,
            'fileName': f"{report.get('title', 'report')}.{storage_path.split('.')[-1]}"
        })

    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to download report'
        }), 500


@firebase_reports_bp.route('/<report_id>', methods=['DELETE'])
@require_auth
def delete_report(report_id):
    """Delete a report (soft delete)"""
    try:
        user_id = get_current_user_id()

        report = firestore_report_service.get_report(report_id)

        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404

        if report.get('userId') != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403

        # Delete report and file
        success = firestore_report_service.delete_report(
            report_id=report_id,
            delete_file=True
        )

        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to delete report'
            }), 500

        logger.info(f"✅ Report deleted: {report_id}")

        return jsonify({
            'success': True,
            'message': 'Report deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete report'
        }), 500


@firebase_reports_bp.route('/generate-sample', methods=['POST'])
@require_auth
def generate_sample_report():
    """
    Generate a sample report for testing
    Creates a simple text report and uploads it
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}

        # Create report metadata
        report_id = firestore_report_service.create_report(
            user_id=user_id,
            title=data.get('title', f'Sample Report {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
            description='This is a sample report generated for testing Firebase Storage integration',
            report_type='document'
        )

        if not report_id:
            return jsonify({
                'success': False,
                'error': 'Failed to create report'
            }), 500

        # Update status
        firestore_report_service.update_report_status(
            report_id=report_id,
            status='generating'
        )

        # Generate sample content
        content = f"""SAMPLE REPORT
==============

Title: {data.get('title', 'Sample Report')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User ID: {user_id}
Report ID: {report_id}

This is a sample report generated for testing Firebase Storage integration.

Report Details:
- Storage: Firebase Cloud Storage
- Database: Cloud Firestore
- Security: Signed URLs with expiration
- Access: User-based authentication

Features Demonstrated:
✅ Report metadata storage in Firestore
✅ File storage in Firebase Storage
✅ Secure signed URL generation
✅ Download tracking
✅ User-based access control

This sample report confirms that your Firebase Storage integration is working correctly!
"""

        # Save to temp file
        temp_path = os.path.join(tempfile.gettempdir(), f'sample_report_{report_id}.txt')
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Upload to Firebase Storage
        download_url = firestore_report_service.save_report_file(
            report_id=report_id,
            file_path=temp_path,
            file_format='txt'
        )

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not download_url:
            return jsonify({
                'success': False,
                'error': 'Failed to upload sample report'
            }), 500

        logger.info(f"✅ Generated sample report: {report_id}")

        return jsonify({
            'success': True,
            'reportId': report_id,
            'downloadUrl': download_url,
            'message': 'Sample report generated successfully'
        })

    except Exception as e:
        logger.error(f"Error generating sample report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to generate sample report'
        }), 500
