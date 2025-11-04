#!/usr/bin/env python3
"""
Verification script for Excel generation endpoint health check.
This script checks common issues that cause 500 Internal Server Errors.
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_python_dependencies():
    """Check if required Python packages are installed."""
    logger.info("Checking Python dependencies...")
    required_packages = [
        'openpyxl',
        'xlrd',
        'pandas',
        'numpy',
        'python-docx',
        'flask',
        'firebase-admin'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"  ✓ {package}")
        except ImportError:
            logger.error(f"  ✗ {package} - MISSING")
            missing_packages.append(package)

    if missing_packages:
        logger.error(f"\nMissing packages: {', '.join(missing_packages)}")
        logger.error("Install with: pip install " + ' '.join(missing_packages))
        return False

    logger.info("All dependencies installed ✓\n")
    return True


def check_directory_permissions():
    """Check if output directories exist and are writable."""
    logger.info("Checking directory permissions...")

    base_dir = Path(__file__).parent
    directories = [
        base_dir / 'static',
        base_dir / 'static' / 'generated',
        base_dir / 'static' / 'exports',
        base_dir / 'static' / 'previews',
        base_dir / 'static' / 'charts',
        base_dir / 'templates'
    ]

    all_ok = True
    for directory in directories:
        if not directory.exists():
            logger.warning(f"  ⚠ {directory} - does not exist, creating...")
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"    Created {directory} ✓")
            except Exception as e:
                logger.error(f"    Failed to create {directory}: {e}")
                all_ok = False

        # Test write permission
        test_file = directory / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"  ✓ {directory} - writable")
        except Exception as e:
            logger.error(f"  ✗ {directory} - NOT writable: {e}")
            all_ok = False

    if all_ok:
        logger.info("All directories writable ✓\n")
    return all_ok


def check_excel_parser():
    """Test Excel parser with a simple file."""
    logger.info("Testing Excel parser...")

    try:
        from app.services.excel_parser import ExcelParserService

        parser = ExcelParserService()
        logger.info(f"  ✓ ExcelParserService initialized")
        logger.info(f"  - Max file size: {parser.max_file_size / 1024 / 1024:.1f}MB")
        logger.info(f"  - Max processing time: {parser.max_processing_time}s")
        logger.info(f"  - Max rows: {parser.max_rows}")
        logger.info(f"  - Max columns: {parser.max_columns}")

        logger.info("Excel parser configuration OK ✓\n")
        return True
    except Exception as e:
        logger.error(f"  ✗ Excel parser test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def check_firebase_config():
    """Check Firebase configuration."""
    logger.info("Checking Firebase configuration...")

    firebase_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_DATABASE_URL'
    ]

    missing = []
    for var in firebase_vars:
        if not os.environ.get(var):
            missing.append(var)
            logger.warning(f"  ⚠ {var} - not set")
        else:
            # Show partial value for security
            value = os.environ[var]
            display_value = value[:10] + '...' if len(value) > 10 else value
            logger.info(f"  ✓ {var} - set ({display_value})")

    if missing:
        logger.warning(f"Missing Firebase config: {', '.join(missing)}")
        logger.warning("Firebase features may not work properly\n")
        return False

    logger.info("Firebase configuration OK ✓\n")
    return True


def check_memory_limits():
    """Check system memory and limits."""
    logger.info("Checking system memory...")

    try:
        import psutil

        memory = psutil.virtual_memory()
        logger.info(f"  Total memory: {memory.total / 1024 / 1024 / 1024:.2f}GB")
        logger.info(f"  Available memory: {memory.available / 1024 / 1024 / 1024:.2f}GB")
        logger.info(f"  Memory usage: {memory.percent}%")

        if memory.available < 512 * 1024 * 1024:  # Less than 512MB
            logger.warning("  ⚠ Low memory available!")
            logger.warning("    Consider reducing max file size or row limits")
            return False

        logger.info("Memory OK ✓\n")
        return True
    except ImportError:
        logger.warning("  ⚠ psutil not installed, skipping memory check")
        logger.warning("    Install with: pip install psutil\n")
        return True


def test_endpoint_availability():
    """Test if the endpoint is accessible."""
    logger.info("Testing endpoint availability...")

    try:
        # Check if Flask app can be imported
        from app import create_app

        app = create_app()
        with app.app_context():
            logger.info("  ✓ Flask app created successfully")

        # List registered routes
        with app.app_context():
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            if '/api/nextgen/excel/generate-report' in routes:
                logger.info("  ✓ Excel generation endpoint registered")
            else:
                logger.warning("  ⚠ Excel generation endpoint not found in routes")
                logger.info(f"    Available routes: {len(routes)}")

        logger.info("Endpoint availability OK ✓\n")
        return True
    except Exception as e:
        logger.error(f"  ✗ Endpoint test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Excel Generation Endpoint Verification")
    logger.info("=" * 60 + "\n")

    checks = [
        ("Python Dependencies", check_python_dependencies),
        ("Directory Permissions", check_directory_permissions),
        ("Excel Parser", check_excel_parser),
        ("Firebase Config", check_firebase_config),
        ("System Memory", check_memory_limits),
        ("Endpoint Availability", test_endpoint_availability)
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"Check '{name}' crashed: {e}")
            results[name] = False

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{name:.<40} {status}")

    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} checks passed")

    if passed == total:
        logger.info("\n🎉 All checks passed! System ready for Excel generation.")
        return 0
    else:
        logger.warning(f"\n⚠️  {total - passed} check(s) failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
