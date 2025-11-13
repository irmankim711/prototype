"""
Firebase Storage Service
Handles file uploads and downloads from Firebase Storage
"""

import os
import logging
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import mimetypes

from firebase_admin import storage

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """Service for managing files in Firebase Storage"""

    def __init__(self):
        """Initialize Firebase Storage service"""
        self._bucket = None
        self._initialized = False
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize Firebase Storage bucket"""
        try:
            # Get bucket name from environment or use default
            bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET', 'report-automation-57f6e.firebasestorage.app')

            # Get the bucket
            self._bucket = storage.bucket(bucket_name)
            self._initialized = True
            logger.info(f"✅ Firebase Storage initialized successfully: {bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Storage: {e}")
            self._initialized = False

    def upload_file(
        self,
        file_path: str,
        destination_path: str,
        metadata: Optional[Dict[str, str]] = None,
        make_public: bool = False
    ) -> Optional[str]:
        """
        Upload a file to Firebase Storage

        Args:
            file_path: Local path to the file to upload
            destination_path: Path in Firebase Storage (e.g., 'reports/report_123.docx')
            metadata: Optional metadata to attach to the file
            make_public: Whether to make the file publicly accessible

        Returns:
            Public URL if successful, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase Storage not initialized")
            return None

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None

            # Get content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'

            # Create blob
            blob = self._bucket.blob(destination_path)

            # Set metadata
            if metadata:
                blob.metadata = metadata

            # Upload file
            blob.upload_from_filename(
                file_path,
                content_type=content_type
            )

            # Make public if requested
            if make_public:
                blob.make_public()
                public_url = blob.public_url
            else:
                # Generate signed URL (valid for 7 days)
                public_url = blob.generate_signed_url(
                    expiration=timedelta(days=7),
                    version='v4'
                )

            logger.info(f"✅ Uploaded file to Firebase Storage: {destination_path}")
            return public_url

        except Exception as e:
            logger.error(f"❌ Error uploading file to Firebase Storage: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def upload_file_object(
        self,
        file_obj: BinaryIO,
        destination_path: str,
        content_type: str = 'application/octet-stream',
        metadata: Optional[Dict[str, str]] = None,
        make_public: bool = False
    ) -> Optional[str]:
        """
        Upload a file object to Firebase Storage

        Args:
            file_obj: File-like object to upload
            destination_path: Path in Firebase Storage
            content_type: MIME type of the file
            metadata: Optional metadata to attach
            make_public: Whether to make the file publicly accessible

        Returns:
            Public URL if successful, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase Storage not initialized")
            return None

        try:
            # Create blob
            blob = self._bucket.blob(destination_path)

            # Set metadata
            if metadata:
                blob.metadata = metadata

            # Upload from file object
            file_obj.seek(0)  # Ensure we're at the start
            blob.upload_from_file(
                file_obj,
                content_type=content_type
            )

            # Make public if requested
            if make_public:
                blob.make_public()
                public_url = blob.public_url
            else:
                # Generate signed URL (valid for 7 days)
                public_url = blob.generate_signed_url(
                    expiration=timedelta(days=7),
                    version='v4'
                )

            logger.info(f"✅ Uploaded file object to Firebase Storage: {destination_path}")
            return public_url

        except Exception as e:
            logger.error(f"❌ Error uploading file object to Firebase Storage: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def download_file(
        self,
        storage_path: str,
        destination_path: str
    ) -> bool:
        """
        Download a file from Firebase Storage

        Args:
            storage_path: Path in Firebase Storage
            destination_path: Local path to save the file

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firebase Storage not initialized")
            return False

        try:
            blob = self._bucket.blob(storage_path)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # Download file
            blob.download_to_filename(destination_path)

            logger.info(f"✅ Downloaded file from Firebase Storage: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error downloading file from Firebase Storage: {e}")
            return False

    def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from Firebase Storage

        Args:
            storage_path: Path in Firebase Storage

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firebase Storage not initialized")
            return False

        try:
            blob = self._bucket.blob(storage_path)

            # Check if blob exists before attempting deletion
            if not blob.exists():
                logger.warning(f"⚠️ File does not exist in Firebase Storage: {storage_path}")
                # Return True since the end state is correct (file doesn't exist)
                return True

            blob.delete()

            logger.info(f"✅ Deleted file from Firebase Storage: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting file from Firebase Storage: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def get_signed_url(
        self,
        storage_path: str,
        expiration_hours: int = 168  # 7 days default
    ) -> Optional[str]:
        """
        Generate a signed URL for a file in Firebase Storage

        Args:
            storage_path: Path in Firebase Storage
            expiration_hours: Hours until the URL expires

        Returns:
            Signed URL if successful, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase Storage not initialized")
            return None

        try:
            blob = self._bucket.blob(storage_path)

            url = blob.generate_signed_url(
                expiration=timedelta(hours=expiration_hours),
                version='v4'
            )

            return url

        except Exception as e:
            logger.error(f"❌ Error generating signed URL: {e}")
            return None

    def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in Firebase Storage

        Args:
            storage_path: Path in Firebase Storage

        Returns:
            True if file exists, False otherwise
        """
        if not self._initialized:
            return False

        try:
            blob = self._bucket.blob(storage_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False

    def list_files(self, prefix: str = '') -> list:
        """
        List files in Firebase Storage with optional prefix filter

        Args:
            prefix: Prefix to filter files (e.g., 'reports/')

        Returns:
            List of file paths
        """
        if not self._initialized:
            logger.error("Firebase Storage not initialized")
            return []

        try:
            blobs = self._bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]

        except Exception as e:
            logger.error(f"❌ Error listing files: {e}")
            return []


# Global instance
firebase_storage_service = FirebaseStorageService()
