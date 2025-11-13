"""
Firestore Report Service
Manages report metadata in Firestore and files in Firebase Storage
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from .firebase_storage_service import firebase_storage_service

logger = logging.getLogger(__name__)


def serialize_firestore_timestamp(timestamp: Any) -> Optional[str]:
    """
    Safely serialize a Firestore timestamp to ISO format string

    Args:
        timestamp: Firestore timestamp object or None

    Returns:
        ISO format string or None
    """
    if timestamp is None:
        return None

    try:
        # Handle datetime objects
        if hasattr(timestamp, 'isoformat'):
            return timestamp.isoformat()

        # Handle Firestore Timestamp objects
        if hasattr(timestamp, 'timestamp'):
            return datetime.fromtimestamp(timestamp.timestamp()).isoformat()

        # Fallback to string conversion
        return str(timestamp)
    except Exception as e:
        logger.warning(f"Failed to serialize timestamp {timestamp}: {e}")
        return None


class FirestoreReportService:
    """Service for managing reports in Firestore + Firebase Storage"""

    def __init__(self):
        """Initialize Firestore Report service"""
        self._firestore_db = None
        self._initialized = False
        self._initialize_firestore()

    def _initialize_firestore(self):
        """Initialize Firestore client"""
        try:
            self._firestore_db = firestore.client()
            self._initialized = True
            logger.info("✅ Firestore Report Service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore Report Service: {e}")
            self._initialized = False

    def create_report(
        self,
        user_id: str,
        title: str,
        description: str = '',
        report_type: str = 'document',
        template_id: Optional[str] = None,
        program_id: Optional[str] = None,
        data_source: Optional[Dict] = None,
        generation_config: Optional[Dict] = None,
        generated_data: Optional[Dict] = None  # ✅ NEW: Support extracted data
    ) -> Optional[str]:
        """
        Create a new report in Firestore

        Args:
            user_id: ID of the user creating the report
            title: Report title
            description: Report description
            report_type: Type of report (document, pdf, excel, etc.)
            template_id: Optional template ID
            program_id: Optional program ID
            data_source: Optional data source configuration
            generation_config: Optional generation configuration
            generated_data: Optional structured extracted data (program info, participants, etc.)

        Returns:
            Report ID if successful, None otherwise
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return None

        try:
            report_data = {
                'createdBy': {
                    'userId': user_id,
                    'createdAt': firestore.SERVER_TIMESTAMP
                },
                'title': title,
                'description': description,
                'reportType': report_type,
                'generationStatus': 'pending',
                'templateId': template_id,
                'programId': program_id,
                'dataSource': data_source or {},
                'generationConfig': generation_config or {},
                'generatedData': generated_data or {},  # ✅ NEW: Store extracted data
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'downloadCount': 0,
                'isActive': True
            }

            # Create document in Firestore
            doc_ref = self._firestore_db.collection('reports').document()
            doc_ref.set(report_data)

            logger.info(f"✅ Created report in Firestore: {doc_ref.id}")
            return doc_ref.id

        except Exception as e:
            logger.error(f"❌ Error creating report in Firestore: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def update_report_status(
        self,
        report_id: str,
        status: str,
        file_path: Optional[str] = None,
        storage_url: Optional[str] = None,
        error_message: Optional[str] = None,
        file_size: Optional[int] = None,
        generation_time: Optional[int] = None
    ) -> bool:
        """
        Update report generation status

        Args:
            report_id: Report document ID
            status: New status (pending, generating, completed, failed)
            file_path: Path in Firebase Storage
            storage_url: Download URL
            error_message: Error message if failed
            file_size: Size of generated file in bytes
            generation_time: Time taken to generate in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return False

        try:
            doc_ref = self._firestore_db.collection('reports').document(report_id)

            update_data = {
                'generationStatus': status,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }

            if status == 'completed':
                update_data['generatedAt'] = firestore.SERVER_TIMESTAMP

            if file_path:
                update_data['storagePath'] = file_path

            if storage_url:
                update_data['downloadUrl'] = storage_url

            if error_message:
                update_data['errorMessage'] = error_message

            if file_size:
                update_data['fileSize'] = file_size

            if generation_time:
                update_data['generationTimeSeconds'] = generation_time

            doc_ref.update(update_data)

            logger.info(f"✅ Updated report status: {report_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating report status: {e}")
            return False

    def get_report(self, report_id: str) -> Optional[Dict]:
        """
        Get report by ID

        Args:
            report_id: Report document ID

        Returns:
            Report data dict if found, None otherwise
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return None

        try:
            doc_ref = self._firestore_db.collection('reports').document(report_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            report_data = doc.to_dict()
            report_data['id'] = doc.id

            return report_data

        except Exception as e:
            logger.error(f"❌ Error getting report: {e}")
            return None

    def convert_report_to_api_format(self, report: Dict) -> Dict:
        """
        Convert Firestore report data to API format

        Args:
            report: Firestore report dict

        Returns:
            Report dict in API format
        """
        return {
            'id': report.get('id'),
            'uuid': report.get('id'),
            'title': report.get('title', 'Untitled Report'),
            'description': report.get('description', ''),
            'status': report.get('generationStatus', 'unknown'),
            'generation_status': report.get('generationStatus', 'unknown'),
            'report_type': report.get('reportType', 'automated'),
            'file_path': report.get('storagePath'),
            'file_format': self._extract_file_format(report.get('reportType', '')),
            'created_at': serialize_firestore_timestamp(report.get('createdAt')),
            'updated_at': serialize_firestore_timestamp(report.get('updatedAt')),
            'generated_at': serialize_firestore_timestamp(report.get('generatedAt')),
            'download_count': report.get('downloadCount', 0),
            'download_url': report.get('downloadUrl'),
            'file_size': report.get('fileSize'),
            'template_id': report.get('templateId'),
            'program_id': report.get('programId'),
            'data_source': report.get('dataSource'),
            'generation_config': report.get('generationConfig'),
            'error_message': report.get('errorMessage')
        }

    def _extract_file_format(self, report_type: str) -> str:
        """
        Extract file format from report type

        Args:
            report_type: Report type string

        Returns:
            File format string (default: 'docx')
        """
        if '_' in report_type:
            return report_type.split('_')[-1]
        return 'docx'

    def get_user_reports(
        self,
        user_id: str,
        limit: int = 50,
        status_filter: Optional[str] = None,
        report_type_filter: Optional[str] = None,
        start_after_doc: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Get reports for a specific user with proper filtering and cursor-based pagination

        Args:
            user_id: User ID
            limit: Maximum number of reports to return
            status_filter: Optional status filter
            report_type_filter: Optional report type filter
            start_after_doc: Document snapshot to start after (for pagination)

        Returns:
            Dict with 'reports' list and 'last_doc' for pagination
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return {'reports': [], 'last_doc': None, 'has_more': False}

        try:
            # Build base query with required filters
            query = self._firestore_db.collection('reports')\
                .where('createdBy.userId', '==', user_id)\
                .where('isActive', '==', True)

            # Add optional status filter
            if status_filter:
                query = query.where('generationStatus', '==', status_filter)

            # Add optional report type filter
            if report_type_filter:
                query = query.where('reportType', '==', report_type_filter)

            # Order by createdAt descending
            query = query.order_by('createdAt', direction=firestore.Query.DESCENDING)

            # Add cursor for pagination
            if start_after_doc:
                query = query.start_after(start_after_doc)

            # Fetch limit + 1 to check if there are more results
            query = query.limit(limit + 1)

            docs = list(query.stream())

            # Check if there are more results
            has_more = len(docs) > limit
            if has_more:
                docs = docs[:limit]  # Remove the extra document

            reports = []
            last_doc = None

            for doc in docs:
                report_data = doc.to_dict()
                report_data['id'] = doc.id
                reports.append(report_data)
                last_doc = doc  # Keep track of last document for cursor

            return {
                'reports': reports,
                'last_doc': last_doc,
                'has_more': has_more
            }

        except Exception as e:
            logger.error(f"❌ Error getting user reports: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'reports': [], 'last_doc': None, 'has_more': False}

    def delete_report(self, report_id: str, delete_file: bool = True) -> bool:
        """
        Delete a report (soft delete by default)

        Args:
            report_id: Report document ID
            delete_file: Whether to also delete the file from Storage

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return False

        try:
            doc_ref = self._firestore_db.collection('reports').document(report_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"Report not found: {report_id}")
                return False

            report_data = doc.to_dict()

            # Delete file from storage if requested (atomic operation)
            if delete_file and report_data.get('storagePath'):
                storage_path = report_data['storagePath']
                deletion_success = firebase_storage_service.delete_file(storage_path)

                if not deletion_success:
                    logger.error(f"❌ Failed to delete file from storage: {storage_path}")
                    logger.error(f"❌ Aborting report deletion to maintain consistency")
                    return False

            # Only soft delete database record if file deletion succeeded (or no file to delete)
            doc_ref.update({
                'isActive': False,
                'deletedAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })

            logger.info(f"✅ Deleted report: {report_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting report: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def increment_download_count(self, report_id: str) -> bool:
        """
        Increment download count for a report

        Args:
            report_id: Report document ID

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            return False

        try:
            doc_ref = self._firestore_db.collection('reports').document(report_id)

            doc_ref.update({
                'downloadCount': firestore.Increment(1),
                'lastDownloadedAt': firestore.SERVER_TIMESTAMP
            })

            return True

        except Exception as e:
            logger.error(f"❌ Error incrementing download count: {e}")
            return False

    def save_report_file(
        self,
        report_id: str,
        file_path: str,
        file_format: str = 'docx'
    ) -> Optional[str]:
        """
        Upload report file to Firebase Storage and update Firestore metadata

        Args:
            report_id: Report document ID
            file_path: Local path to the file
            file_format: File format (docx, pdf, xlsx, etc.)

        Returns:
            Download URL if successful, None otherwise
        """
        try:
            # Generate storage path
            storage_path = f'reports/{report_id}/report.{file_format}'

            # Get file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            # Upload to Firebase Storage
            download_url = firebase_storage_service.upload_file(
                file_path=file_path,
                destination_path=storage_path,
                metadata={
                    'reportId': report_id,
                    'uploadedAt': datetime.utcnow().isoformat()
                },
                make_public=False  # Use signed URLs for security
            )

            if download_url:
                # Update Firestore with file info
                self.update_report_status(
                    report_id=report_id,
                    status='completed',
                    file_path=storage_path,
                    storage_url=download_url,
                    file_size=file_size
                )

            return download_url

        except Exception as e:
            logger.error(f"❌ Error saving report file: {e}")
            return None


# Global instance
firestore_report_service = FirestoreReportService()
