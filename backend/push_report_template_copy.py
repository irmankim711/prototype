"""
Script to push report_template_copy.docx to Firestore
This will make your updated template available in the system
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import json

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Set up Firebase credentials from service account file
service_account_path = Path(__file__).parent / 'service' / 'report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json'
if service_account_path.exists():
    with open(service_account_path, 'r') as f:
        service_account = json.load(f)
        os.environ['FIREBASE_PROJECT_ID'] = service_account.get('project_id', '')
        os.environ['FIREBASE_CLIENT_EMAIL'] = service_account.get('client_email', '')
        os.environ['FIREBASE_PRIVATE_KEY'] = service_account.get('private_key', '')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)

from app.middleware.firebase_auth import firebase_auth_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def push_report_template_copy():
    """
    Push report_template_copy.docx to Firestore
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    # Find the template file
    template_file = Path(__file__).parent / 'templates' / 'report_template_copy.docx'

    if not template_file.exists():
        logger.error(f"❌ Template not found: {template_file}")
        return False

    logger.info(f"📄 Found template: {template_file.name}")
    logger.info(f"   Size: {template_file.stat().st_size} bytes")
    logger.info(f"   Modified: {datetime.fromtimestamp(template_file.stat().st_mtime)}")

    # Get relative path from project root
    relative_path = template_file.relative_to(Path(__file__).parent.parent)

    # Create template document
    template_data = {
        'name': 'Report Template Puncak Alam',
        'file_name': template_file.name,
        'file_path': str(relative_path).replace('\\', '/'),
        'absolute_path': str(template_file),
        'template_type': 'docx',
        'category': 'automation',
        'is_active': True,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'file_size': template_file.stat().st_size,
        'supports_charts': True,
        'supports_images': True,
        'supports_loops': True,
        'version': '2.0',
        'usage_count': 0,
        'description': 'Laporan Fiqh Usrah - Puncak Alam Template with participant table loops',
        'placeholder_schema': {
            'template_identifier': 'puncak_alam_fu',
            'required_fields': [
                'peserta_list',  # List of participants
                'program',       # Program details
            ],
            'loop_fields': {
                'peserta_list': [
                    'bil',
                    'nama',
                    'kad_pengenalan',
                    'alamat',
                    'no_telefon',
                    'kehadiran_sabtu',
                    'kehadiran_ahad',
                    'markah_pre',
                    'markah_post',
                    'jantina'
                ]
            },
            'syntax': 'docxtpl',
            'loop_syntax': '{%tr for peserta in peserta_list %} ... {%tr endfor %}'
        }
    }

    # Use document ID
    doc_id = 'report_template_puncak_alam'

    # Create/update template in Firestore
    templates_collection = firestore_db.collection('templates')
    template_ref = templates_collection.document(doc_id)

    try:
        # Check if template already exists
        existing_doc = template_ref.get()

        if existing_doc.exists:
            logger.info(f"🔄 Updating existing template in Firestore...")
            # Keep existing usage_count
            existing_data = existing_doc.to_dict()
            template_data['usage_count'] = existing_data.get('usage_count', 0)
            template_data['created_at'] = existing_data.get('created_at', datetime.utcnow())
        else:
            logger.info(f"✨ Creating new template in Firestore...")

        template_ref.set(template_data)
        logger.info(f"✅ Successfully pushed template to Firestore!")
        logger.info(f"   Document ID: {doc_id}")
        logger.info(f"   File: {template_file.name}")
        logger.info(f"   Size: {template_file.stat().st_size} bytes")
        logger.info(f"   Path: {relative_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Error pushing template: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_upload():
    """
    Verify that the template is in Firestore
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    templates_collection = firestore_db.collection('templates')
    template_ref = templates_collection.document('report_template_puncak_alam')

    doc = template_ref.get()
    if doc.exists:
        template_data = doc.to_dict()
        logger.info("=" * 80)
        logger.info("✅ VERIFICATION: Template Successfully Uploaded")
        logger.info("=" * 80)
        logger.info(f"Document ID: {doc.id}")
        logger.info(f"Name: {template_data.get('name')}")
        logger.info(f"File: {template_data.get('file_name')}")
        logger.info(f"Type: {template_data.get('template_type')}")
        logger.info(f"Version: {template_data.get('version')}")
        logger.info(f"Active: {template_data.get('is_active')}")
        logger.info(f"Supports Loops: {template_data.get('supports_loops')}")
        logger.info(f"File Size: {template_data.get('file_size')} bytes")
        logger.info(f"Updated: {template_data.get('updated_at')}")
        logger.info("=" * 80)
        return True
    else:
        logger.error("❌ Template not found in Firestore after upload!")
        return False

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("PUSH REPORT_TEMPLATE_COPY.DOCX TO FIRESTORE")
    logger.info("=" * 80)

    # Check Firebase initialization
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized!")
        logger.error("Please check your Firebase credentials and configuration.")
        sys.exit(1)

    logger.info("✅ Firebase initialized successfully\n")

    # Push template
    logger.info("Pushing template to Firestore...")
    logger.info("-" * 80)
    if push_report_template_copy():
        logger.info("✅ Template pushed successfully\n")
    else:
        logger.error("❌ Failed to push template\n")
        sys.exit(1)

    # Verify upload
    logger.info("Verifying template upload...")
    logger.info("-" * 80)
    if verify_upload():
        logger.info("\n✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        logger.info("\nYour template is now available in Firebase!")
        logger.info("You can select it from the template list in your application.")
    else:
        logger.error("\n❌ Verification failed!")
        sys.exit(1)

    logger.info("=" * 80)
