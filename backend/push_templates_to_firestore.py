"""
Script to push templates from filesystem to Firestore
This ensures templates are available in the cloud database for Railway deployment
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
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Loaded Firebase credentials from {service_account_path}")
else:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Service account file not found at {service_account_path}")

from app.middleware.firebase_auth import firebase_auth_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def push_templates_to_firestore():
    """
    Scan the templates directory and push all templates to Firestore
    """

    # Check if Firebase is initialized
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized. Cannot push templates.")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    # Get templates directory
    templates_dir = Path(__file__).parent / 'templates'
    if not templates_dir.exists():
        logger.error(f"❌ Templates directory not found: {templates_dir}")
        return False

    logger.info(f"📂 Scanning templates directory: {templates_dir}")

    # Scan for template files
    template_files = []
    for ext in ['.docx', '.jinja', '.tex', '.html']:
        template_files.extend(list(templates_dir.glob(f'**/*{ext}')))

    logger.info(f"📋 Found {len(template_files)} template files")

    # Push each template to Firestore
    templates_collection = firestore_db.collection('templates')
    success_count = 0
    error_count = 0

    for template_file in template_files:
        try:
            # Get relative path from templates directory
            relative_path = template_file.relative_to(templates_dir.parent)

            # Clean template name (remove extension)
            template_name = template_file.stem

            # Determine template type
            template_type = template_file.suffix.lstrip('.')

            # Create template document
            template_data = {
                'name': template_name,
                'file_name': template_file.name,
                'file_path': str(relative_path).replace('\\', '/'),  # Use forward slashes
                'absolute_path': str(template_file),
                'template_type': template_type,
                'category': 'automation',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'file_size': template_file.stat().st_size,
                'supports_charts': template_type == 'docx',
                'supports_images': template_type == 'docx',
                'version': '1.0',
                'usage_count': 0,
                'description': f'Auto-generated template record for {template_name}'
            }

            # Use template name as document ID (clean it first)
            doc_id = template_name.replace(' ', '_').replace('-', '_')

            # Check if template already exists
            template_ref = templates_collection.document(doc_id)
            existing_doc = template_ref.get()

            if existing_doc.exists:
                # Update existing template
                template_data['updated_at'] = datetime.utcnow()
                # Keep existing usage_count
                existing_data = existing_doc.to_dict()
                template_data['usage_count'] = existing_data.get('usage_count', 0)

                template_ref.update(template_data)
                logger.info(f"✅ Updated template: {template_name}")
            else:
                # Create new template
                template_ref.set(template_data)
                logger.info(f"✅ Created template: {template_name}")

            success_count += 1

        except Exception as e:
            logger.error(f"❌ Error processing {template_file.name}: {str(e)}")
            error_count += 1
            continue

    # Summary
    logger.info("=" * 80)
    logger.info("TEMPLATE SYNC SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total templates found: {len(template_files)}")
    logger.info(f"Successfully synced: {success_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("=" * 80)

    return error_count == 0

def list_firestore_templates():
    """
    List all templates currently in Firestore
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return

    templates_collection = firestore_db.collection('templates')
    templates = templates_collection.stream()

    logger.info("=" * 80)
    logger.info("TEMPLATES IN FIRESTORE")
    logger.info("=" * 80)

    count = 0
    for template in templates:
        template_data = template.to_dict()
        logger.info(f"📄 {template.id}")
        logger.info(f"   Name: {template_data.get('name', 'N/A')}")
        logger.info(f"   Type: {template_data.get('template_type', 'N/A')}")
        logger.info(f"   Path: {template_data.get('file_path', 'N/A')}")
        logger.info(f"   Active: {template_data.get('is_active', False)}")
        logger.info(f"   Usage: {template_data.get('usage_count', 0)}")
        logger.info("")
        count += 1

    logger.info(f"Total templates in Firestore: {count}")
    logger.info("=" * 80)

def verify_template_sync():
    """
    Verify that filesystem templates match Firestore templates
    """
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        logger.error("❌ Firestore database not available")
        return False

    # Get filesystem templates
    templates_dir = Path(__file__).parent / 'templates'
    filesystem_templates = set()

    for ext in ['.docx', '.jinja', '.tex', '.html']:
        for template_file in templates_dir.glob(f'**/*{ext}'):
            filesystem_templates.add(template_file.stem)

    # Get Firestore templates
    templates_collection = firestore_db.collection('templates')
    firestore_templates = set()

    for template in templates_collection.stream():
        template_data = template.to_dict()
        if template_data.get('is_active'):
            firestore_templates.add(template_data.get('name'))

    # Compare
    logger.info("=" * 80)
    logger.info("TEMPLATE SYNC VERIFICATION")
    logger.info("=" * 80)
    logger.info(f"Filesystem templates: {len(filesystem_templates)}")
    logger.info(f"Firestore templates: {len(firestore_templates)}")

    missing_in_firestore = filesystem_templates - firestore_templates
    missing_in_filesystem = firestore_templates - filesystem_templates

    if missing_in_firestore:
        logger.warning(f"⚠️ Templates in filesystem but not in Firestore ({len(missing_in_firestore)}):")
        for name in missing_in_firestore:
            logger.warning(f"   - {name}")

    if missing_in_filesystem:
        logger.warning(f"⚠️ Templates in Firestore but not in filesystem ({len(missing_in_filesystem)}):")
        for name in missing_in_filesystem:
            logger.warning(f"   - {name}")

    if not missing_in_firestore and not missing_in_filesystem:
        logger.info("✅ All templates are in sync!")
        return True

    logger.info("=" * 80)
    return False

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Manage templates in Firestore')
    parser.add_argument('--push', action='store_true', help='Push templates to Firestore')
    parser.add_argument('--list', action='store_true', help='List templates in Firestore')
    parser.add_argument('--verify', action='store_true', help='Verify template sync')
    parser.add_argument('--all', action='store_true', help='Do all operations (push, list, verify)')

    args = parser.parse_args()

    # Check Firebase initialization
    if not firebase_auth_manager._initialized:
        logger.error("❌ Firebase is not initialized!")
        logger.error("Please check your Firebase credentials and configuration.")
        sys.exit(1)

    logger.info("✅ Firebase initialized successfully")

    # Default to --all if no arguments
    if not any([args.push, args.list, args.verify, args.all]):
        args.all = True

    if args.all or args.push:
        logger.info("\n" + "=" * 80)
        logger.info("PUSHING TEMPLATES TO FIRESTORE")
        logger.info("=" * 80)
        success = push_templates_to_firestore()
        if not success:
            logger.error("❌ Failed to push all templates")

    if args.all or args.list:
        logger.info("\n" + "=" * 80)
        logger.info("LISTING FIRESTORE TEMPLATES")
        logger.info("=" * 80)
        list_firestore_templates()

    if args.all or args.verify:
        logger.info("\n" + "=" * 80)
        logger.info("VERIFYING TEMPLATE SYNC")
        logger.info("=" * 80)
        verify_template_sync()

    logger.info("\n✅ Template management operations completed!")
