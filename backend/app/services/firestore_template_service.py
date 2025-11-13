"""
Firestore Template Service
Manages template retrieval from Firestore database
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from ..middleware.firebase_auth import firebase_auth_manager

logger = logging.getLogger(__name__)


class FirestoreTemplateService:
    """Service for managing templates in Firestore"""

    def __init__(self):
        """Initialize Firestore Template service"""
        self._firestore_db = None
        self._initialized = False
        self._initialize_firestore()

    def _initialize_firestore(self):
        """Initialize Firestore client"""
        try:
            if firebase_auth_manager._initialized:
                self._firestore_db = firebase_auth_manager.get_firestore_db()
                self._initialized = True
                logger.info("✅ Firestore Template Service initialized")
            else:
                logger.warning("⚠️ Firebase not initialized, Firestore Template Service unavailable")
                self._initialized = False
        except Exception as e:
            logger.exception("Failed to initialize Firestore Template Service")
            self._initialized = False

    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template from Firestore by document ID

        Args:
            template_id: Firestore document ID

        Returns:
            Template data dictionary or None
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return None

        try:
            doc_ref = self._firestore_db.collection('templates').document(template_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"Template {template_id} not found in Firestore")
                return None

            template_data = doc.to_dict()
            template_data['id'] = doc.id

            logger.info(f"✅ Retrieved template {template_id} from Firestore")
            return template_data

        except Exception as e:
            logger.error(f"❌ Error retrieving template {template_id}: {e}")
            return None

    def get_latest_puncak_alam_template(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest Puncak Alam template from Firestore

        Returns:
            Latest template data or None
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return None

        try:
            # First try to get by specific document ID
            template = self.get_template_by_id('puncak_alam_fu_template')
            if template:
                logger.info("✅ Found Puncak Alam template by document ID")
                return template

            # Fallback: search by name patterns
            templates_ref = self._firestore_db.collection('templates')
            query = templates_ref.where(filter=FieldFilter('is_active', '==', True))

            templates = []
            for doc in query.stream():
                data = doc.to_dict()
                name = data.get('name', '').lower()
                file_name = data.get('file_name', '').lower()

                # Check if this is a Puncak Alam template
                if any(term in name or term in file_name
                      for term in ['puncak', 'alam', 'laporan', 'fu']):
                    data['id'] = doc.id
                    templates.append(data)

            if not templates:
                logger.warning("No Puncak Alam templates found")
                return None

            # Helper function to safely parse version
            def safe_version_float(version_str):
                """Safely convert version string to float, returns 0.0 on error"""
                try:
                    return float(version_str)
                except (ValueError, TypeError):
                    return 0.0

            # Sort by version (descending) and updated_at
            templates.sort(
                key=lambda t: (
                    safe_version_float(t.get('version', '0.0')),
                    t.get('updated_at', datetime.min)
                ),
                reverse=True
            )

            latest = templates[0]
            logger.info(f"✅ Found latest Puncak Alam template: {latest.get('name')} (v{latest.get('version')})")
            return latest

        except Exception as e:
            logger.error(f"❌ Error getting latest Puncak Alam template: {e}")
            return None

    def get_all_templates(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all templates from Firestore

        Args:
            active_only: If True, only return active templates

        Returns:
            List of template dictionaries
        """
        if not self._initialized:
            logger.error("Firestore not initialized")
            return []

        try:
            templates_ref = self._firestore_db.collection('templates')

            if active_only:
                query = templates_ref.where(filter=FieldFilter('is_active', '==', True))
            else:
                query = templates_ref

            templates = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                templates.append(data)

            # Sort by name
            templates.sort(key=lambda t: t.get('name', ''))

            logger.info(f"✅ Retrieved {len(templates)} templates from Firestore")
            return templates

        except Exception as e:
            logger.error(f"❌ Error getting templates from Firestore: {e}")
            return []

    def get_template_file_path(self, template_id: str) -> Optional[str]:
        """
        Get the absolute file path for a template

        Args:
            template_id: Firestore document ID

        Returns:
            Absolute file path or None
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return None

        # Try absolute_path first
        absolute_path = template.get('absolute_path')
        if absolute_path and os.path.exists(absolute_path):
            return absolute_path

        # Try file_path (relative)
        file_path = template.get('file_path')
        if file_path:
            # Construct absolute path from project root
            backend_dir = Path(__file__).parent.parent.parent
            absolute_path = backend_dir / file_path

            if absolute_path.exists():
                return str(absolute_path)

        logger.warning(f"Template file not found for {template_id}")
        return None

    def increment_usage_count(self, template_id: str):
        """
        Increment the usage count for a template

        Args:
            template_id: Firestore document ID
        """
        if not self._initialized:
            return

        try:
            doc_ref = self._firestore_db.collection('templates').document(template_id)
            doc_ref.update({
                'usage_count': firestore.Increment(1),
                'last_used': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"✅ Incremented usage count for template {template_id}")
        except Exception as e:
            logger.error(f"❌ Error incrementing usage count: {e}")


# Global instance
firestore_template_service = FirestoreTemplateService()
