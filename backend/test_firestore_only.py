"""
Test script to verify application runs without SQL database errors
when using Firestore only
"""

import os
import sys
import logging

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_app_initialization():
    """Test that the Flask app initializes without SQL errors"""
    try:
        from app import create_app

        logger.info("Creating Flask app...")
        app = create_app()

        with app.app_context():
            logger.info("✅ Flask app created successfully!")
            logger.info(f"   Config: {app.config.get('ENV', 'unknown')}")
            logger.info(f"   SQL DB URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")

            # Check if SQL database was initialized
            from app import db
            try:
                # Try to access database
                db.engine.connect()
                logger.info("   SQL database: ACTIVE")
            except Exception as e:
                logger.info(f"   SQL database: DISABLED (using Firestore only) - {type(e).__name__}")

            logger.info("\n✅ SUCCESS: Application initialized without SQL database errors!")
            return True

    except Exception as e:
        logger.error(f"\n❌ FAILED: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_firestore_connection():
    """Test Firestore connection"""
    try:
        logger.info("\nTesting Firestore connection...")

        import firebase_admin
        from firebase_admin import credentials, firestore

        # Check if already initialized
        try:
            firestore_client = firestore.client()
            logger.info("✅ Firestore already initialized")
        except ValueError:
            # Initialize Firebase
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH',
                'service/report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json')

            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                firestore_client = firestore.client()
                logger.info("✅ Firestore initialized successfully")
            else:
                logger.warning(f"⚠️  Service account file not found: {service_account_path}")
                return False

        # Test a simple query
        collections = list(firestore_client.collections(limit=5))
        logger.info(f"   Found {len(collections)} Firestore collections")
        logger.info("✅ Firestore connection working!")
        return True

    except Exception as e:
        logger.error(f"❌ Firestore connection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_reports_api():
    """Test that reports API can be accessed without SQL errors"""
    try:
        logger.info("\nTesting Reports API endpoints...")
        from app import create_app

        app = create_app()
        client = app.test_client()

        # Test health endpoint
        response = client.get('/api/reports/health')
        logger.info(f"   GET /api/reports/health: {response.status_code}")

        if response.status_code == 200:
            logger.info("✅ Reports API accessible!")
            return True
        else:
            logger.warning(f"⚠️  Reports API returned {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ Reports API test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("FIRESTORE-ONLY CONFIGURATION TEST")
    logger.info("=" * 70)

    # Run tests
    results = []

    logger.info("\n[1/3] Testing Flask app initialization...")
    results.append(test_app_initialization())

    logger.info("\n[2/3] Testing Firestore connection...")
    results.append(test_firestore_connection())

    logger.info("\n[3/3] Testing Reports API...")
    results.append(test_reports_api())

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    passed = sum(results)
    total = len(results)

    if all(results):
        logger.info(f"✅ ALL TESTS PASSED ({passed}/{total})")
        logger.info("\nYour application is properly configured to use Firestore only!")
        logger.info("SQL database errors should be resolved.")
        sys.exit(0)
    else:
        logger.error(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        logger.error("\nPlease check the errors above and fix any issues.")
        sys.exit(1)
