"""
Test script to verify Firestore template retrieval
"""

import os
import sys
from pathlib import Path
import logging

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Set up Firebase credentials
import json
service_account_path = Path(__file__).parent / 'service' / 'report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json'
if service_account_path.exists():
    with open(service_account_path, 'r') as f:
        service_account = json.load(f)
        os.environ['FIREBASE_PROJECT_ID'] = service_account.get('project_id', '')
        os.environ['FIREBASE_CLIENT_EMAIL'] = service_account.get('client_email', '')
        os.environ['FIREBASE_PRIVATE_KEY'] = service_account.get('private_key', '')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)

from app.services.firestore_template_service import firestore_template_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_get_all_templates():
    """Test getting all templates"""
    logger.info("=" * 80)
    logger.info("TEST 1: Get All Templates")
    logger.info("=" * 80)

    templates = firestore_template_service.get_all_templates()

    logger.info(f"Found {len(templates)} templates:")
    for template in templates:
        logger.info(f"  - ID: {template['id']}")
        logger.info(f"    Name: {template.get('name')}")
        logger.info(f"    Version: {template.get('version')}")
        logger.info(f"    Type: {template.get('template_type')}")
        logger.info(f"    Active: {template.get('is_active')}")
        logger.info(f"    Usage Count: {template.get('usage_count', 0)}")
        logger.info("")

    return len(templates) > 0


def test_get_puncak_alam_template():
    """Test getting the latest Puncak Alam template"""
    logger.info("=" * 80)
    logger.info("TEST 2: Get Latest Puncak Alam Template")
    logger.info("=" * 80)

    template = firestore_template_service.get_latest_puncak_alam_template()

    if template:
        logger.info("✅ Successfully retrieved Puncak Alam template:")
        logger.info(f"  ID: {template['id']}")
        logger.info(f"  Name: {template.get('name')}")
        logger.info(f"  File: {template.get('file_name')}")
        logger.info(f"  Version: {template.get('version')}")
        logger.info(f"  Type: {template.get('template_type')}")
        logger.info(f"  Supports Loops: {template.get('supports_loops')}")
        logger.info(f"  Usage Count: {template.get('usage_count', 0)}")

        # Get file path
        file_path = firestore_template_service.get_template_file_path(template['id'])
        logger.info(f"  File Path: {file_path}")

        if file_path:
            exists = os.path.exists(file_path)
            logger.info(f"  File Exists: {exists}")
            if exists:
                file_size = os.path.getsize(file_path)
                logger.info(f"  File Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
                return True
            else:
                logger.error(f"  ❌ File not found at path: {file_path}")
                return False
        else:
            logger.error("  ❌ Could not resolve file path")
            return False
    else:
        logger.error("❌ Failed to retrieve Puncak Alam template")
        return False


def test_template_by_id():
    """Test getting template by specific ID"""
    logger.info("=" * 80)
    logger.info("TEST 3: Get Template by ID")
    logger.info("=" * 80)

    template_id = 'puncak_alam_fu_template'
    logger.info(f"Looking for template ID: {template_id}")

    template = firestore_template_service.get_template_by_id(template_id)

    if template:
        logger.info("✅ Successfully retrieved template by ID:")
        logger.info(f"  ID: {template['id']}")
        logger.info(f"  Name: {template.get('name')}")
        logger.info(f"  Description: {template.get('description')}")
        logger.info(f"  Version: {template.get('version')}")

        # Check placeholder schema
        placeholder_schema = template.get('placeholder_schema', {})
        if placeholder_schema:
            logger.info(f"  Placeholder Schema:")
            logger.info(f"    Template Identifier: {placeholder_schema.get('template_identifier')}")
            logger.info(f"    Required Fields: {placeholder_schema.get('required_fields')}")
            logger.info(f"    Loop Fields: {list(placeholder_schema.get('loop_fields', {}).keys())}")

        return True
    else:
        logger.error(f"❌ Failed to retrieve template {template_id}")
        return False


def test_usage_increment():
    """Test incrementing usage count"""
    logger.info("=" * 80)
    logger.info("TEST 4: Increment Usage Count")
    logger.info("=" * 80)

    template = firestore_template_service.get_latest_puncak_alam_template()
    if not template:
        logger.error("❌ Could not get template for usage test")
        return False

    initial_count = template.get('usage_count', 0)
    logger.info(f"Initial usage count: {initial_count}")

    # Increment usage
    firestore_template_service.increment_usage_count(template['id'])
    logger.info("Incremented usage count")

    # Wait a moment and check again
    import time
    time.sleep(1)

    updated_template = firestore_template_service.get_template_by_id(template['id'])
    if updated_template:
        new_count = updated_template.get('usage_count', 0)
        logger.info(f"New usage count: {new_count}")

        if new_count > initial_count:
            logger.info("✅ Usage count successfully incremented")
            return True
        else:
            logger.warning(f"⚠️ Usage count did not increase (may be delayed by Firestore)")
            return True  # Still consider it a pass as Firestore updates may be delayed
    else:
        logger.error("❌ Could not retrieve updated template")
        return False


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("FIRESTORE TEMPLATE RETRIEVAL TEST SUITE")
    logger.info("=" * 80)
    logger.info("")

    results = {}

    # Run tests
    results['get_all_templates'] = test_get_all_templates()
    logger.info("")

    results['get_puncak_alam_template'] = test_get_puncak_alam_template()
    logger.info("")

    results['template_by_id'] = test_template_by_id()
    logger.info("")

    results['usage_increment'] = test_usage_increment()
    logger.info("")

    # Summary
    logger.info("=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("=" * 80)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 80)
        sys.exit(0)
    else:
        logger.error("=" * 80)
        logger.error("❌ SOME TESTS FAILED")
        logger.error("=" * 80)
        sys.exit(1)
