"""
Script to update the Puncak Alam DOCX template in Firestore
- Deletes the old template
- Uploads the new updated template
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

def delete_old_puncak_alam_templates():
    """
    Delete all old Puncak Alam templates from Firestore
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    templates_collection = firestore_db.collection('templates')

    # Search for Puncak Alam related templates
    search_terms = ['puncak', 'alam', 'PUNCAK', 'ALAM', 'laporan', 'LAPORAN']

    logger.info("🔍 Searching for old Puncak Alam templates...")

    deleted_count = 0
    templates = templates_collection.stream()

    for template in templates:
        template_data = template.to_dict()
        template_name = template_data.get('name', '').lower()
        file_name = template_data.get('file_name', '').lower()

        # Check if this is a Puncak Alam template
        is_puncak_alam = any(term.lower() in template_name or term.lower() in file_name
                             for term in search_terms)

        if is_puncak_alam:
            logger.info(f"🗑️  Deleting old template: {template.id}")
            logger.info(f"   Name: {template_data.get('name')}")
            logger.info(f"   File: {template_data.get('file_name')}")

            # Delete the template
            template.reference.delete()
            deleted_count += 1
            logger.info(f"✅ Deleted template: {template.id}")

    if deleted_count == 0:
        logger.info("ℹ️  No old Puncak Alam templates found to delete")
    else:
        logger.info(f"✅ Deleted {deleted_count} old template(s)")

    return True

def upload_new_puncak_alam_template():
    """
    Upload the new Puncak Alam template to Firestore
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    # Find the Puncak Alam template file
    templates_dir = Path(__file__).parent / 'templates' / 'report_templates'

    # Look for the Puncak Alam template
    puncak_alam_files = list(templates_dir.glob('*PUNCAK*ALAM*.docx'))
    if not puncak_alam_files:
        puncak_alam_files = list(templates_dir.glob('04-*LAPORAN*FU*.docx'))

    if not puncak_alam_files:
        logger.error(f"❌ Puncak Alam template not found in {templates_dir}")
        return False

    template_file = puncak_alam_files[0]
    logger.info(f"📄 Found template: {template_file.name}")

    # Get relative path from templates directory
    relative_path = template_file.relative_to(templates_dir.parent.parent)

    # Create clean template name
    template_name = template_file.stem

    # Create template document
    template_data = {
        'name': template_name,
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
        'supports_loops': True,  # New field to indicate loop support
        'version': '2.0',  # Updated version
        'usage_count': 0,
        'description': 'Laporan Fiqh Usrah - Puncak Alam Template (Updated with proper placeholders)',
        'placeholder_schema': {
            'template_identifier': 'puncak_alam_fu',
            'required_fields': [
                'peserta_list',  # List of participants
                'tarikh',
                'lokasi',
                'perunding',
                'anjuran'
            ],
            'loop_fields': {
                'peserta_list': [
                    'bil', 'nama', 'kad_pengenalan', 'no_telefon',
                    'jantina', 'alamat', 'kehadiran_sabtu', 'kehadiran_ahad',
                    'nama_pre', 'markah_pre', 'nama_post', 'markah_post'
                ]
            }
        }
    }

    # Use clean document ID
    doc_id = 'puncak_alam_fu_template'

    # Create/update template in Firestore
    templates_collection = firestore_db.collection('templates')
    template_ref = templates_collection.document(doc_id)

    try:
        template_ref.set(template_data)
        logger.info(f"✅ Successfully uploaded new template to Firestore")
        logger.info(f"   Document ID: {doc_id}")
        logger.info(f"   File: {template_file.name}")
        logger.info(f"   Size: {template_file.stat().st_size} bytes")
        logger.info(f"   Path: {relative_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error uploading template: {str(e)}")
        return False

def verify_upload():
    """
    Verify that the new template is in Firestore
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    templates_collection = firestore_db.collection('templates')
    template_ref = templates_collection.document('puncak_alam_fu_template')

    doc = template_ref.get()
    if doc.exists:
        template_data = doc.to_dict()
        logger.info("=" * 80)
        logger.info("VERIFICATION: Template Successfully Uploaded")
        logger.info("=" * 80)
        logger.info(f"Document ID: {doc.id}")
        logger.info(f"Name: {template_data.get('name')}")
        logger.info(f"File: {template_data.get('file_name')}")
        logger.info(f"Type: {template_data.get('template_type')}")
        logger.info(f"Version: {template_data.get('version')}")
        logger.info(f"Active: {template_data.get('is_active')}")
        logger.info(f"Supports Loops: {template_data.get('supports_loops')}")
        logger.info(f"Updated: {template_data.get('updated_at')}")
        logger.info("=" * 80)
        return True
    else:
        logger.error("❌ Template not found in Firestore after upload!")
        return False

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("PUNCAK ALAM TEMPLATE UPDATE SCRIPT")
    logger.info("=" * 80)

    # Check Firebase initialization
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized!")
        logger.error("Please check your Firebase credentials and configuration.")
        sys.exit(1)

    logger.info("✅ Firebase initialized successfully\n")

    # Step 1: Delete old templates
    logger.info("STEP 1: Deleting old Puncak Alam templates...")
    logger.info("-" * 80)
    if delete_old_puncak_alam_templates():
        logger.info("✅ Old templates deleted successfully\n")
    else:
        logger.error("❌ Failed to delete old templates\n")
        sys.exit(1)

    # Step 2: Upload new template
    logger.info("STEP 2: Uploading new Puncak Alam template...")
    logger.info("-" * 80)
    if upload_new_puncak_alam_template():
        logger.info("✅ New template uploaded successfully\n")
    else:
        logger.error("❌ Failed to upload new template\n")
        sys.exit(1)

    # Step 3: Verify upload
    logger.info("STEP 3: Verifying template upload...")
    logger.info("-" * 80)
    if verify_upload():
        logger.info("\n✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!")
    else:
        logger.error("\n❌ Verification failed!")
        sys.exit(1)

    logger.info("=" * 80)
