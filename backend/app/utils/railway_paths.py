"""
Railway-compatible path handling utilities
Fixes file path issues for Railway deployment where only /tmp is writable
"""

import os
from pathlib import Path
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def is_railway_environment():
    """Check if running in Railway environment"""
    return os.environ.get('RAILWAY_ENVIRONMENT') is not None


def get_writable_dir(subdir=''):
    """
    Get a writable directory path that works in Railway

    Args:
        subdir: Optional subdirectory name (e.g., 'reports', 'uploads')

    Returns:
        Path object pointing to writable directory
    """
    if is_railway_environment():
        # Railway: only /tmp is writable
        base_dir = Path('/tmp')
    else:
        # Development: use backend directory
        try:
            backend_dir = Path(current_app.root_path).parent
            base_dir = backend_dir
        except:
            # Fallback if no app context
            base_dir = Path(__file__).parent.parent.parent

    if subdir:
        path = base_dir / subdir
    else:
        path = base_dir

    # Ensure directory exists
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Writable directory: {path}")
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")

    return path


def get_uploads_dir():
    """Get the uploads directory (writable in both dev and Railway)"""
    return get_writable_dir('uploads')


def get_reports_dir():
    """Get the reports output directory (writable in both dev and Railway)"""
    return get_writable_dir('uploads/reports')


def get_templates_dir():
    """
    Get the templates directory (read-only in Railway)
    Templates should be bundled with the deployment
    """
    if is_railway_environment():
        # Railway: templates are in the deployed codebase (read-only)
        try:
            backend_dir = Path(current_app.root_path).parent
            templates_dir = backend_dir / 'templates'
        except:
            # Fallback
            templates_dir = Path(__file__).parent.parent.parent / 'templates'
    else:
        # Development
        try:
            backend_dir = Path(current_app.root_path).parent
            templates_dir = backend_dir / 'templates'
        except:
            templates_dir = Path(__file__).parent.parent.parent / 'templates'

    if not templates_dir.exists():
        logger.warning(f"Templates directory does not exist: {templates_dir}")
        # Try alternative path
        alt_path = Path('/app/backend/templates') if is_railway_environment() else Path('templates')
        if alt_path.exists():
            logger.info(f"Using alternative templates path: {alt_path}")
            templates_dir = alt_path

    return templates_dir


def ensure_writable_paths():
    """
    Ensure all necessary writable paths exist
    Call this during app initialization
    """
    dirs = [
        get_uploads_dir(),
        get_reports_dir(),
        get_writable_dir('exports'),
        get_writable_dir('charts'),
        get_writable_dir('previews'),
    ]

    for dir_path in dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directory ready: {dir_path}")
        except Exception as e:
            logger.error(f"❌ Failed to create directory {dir_path}: {e}")

    return True


def get_temp_file_path(filename):
    """
    Get a temporary file path for intermediate processing

    Args:
        filename: Name of the temporary file

    Returns:
        Path object for temporary file
    """
    temp_dir = get_writable_dir('temp')
    return temp_dir / filename


def validate_excel_path(excel_path_str):
    """
    Validate and resolve Excel file path
    Handles both absolute paths and relative paths

    Args:
        excel_path_str: Path string from request

    Returns:
        Resolved Path object if valid, None otherwise
    """
    try:
        excel_path = Path(excel_path_str)

        # If absolute path exists, use it
        if excel_path.is_absolute() and excel_path.exists():
            return excel_path

        # Try relative to uploads
        uploads_dir = get_uploads_dir()
        relative_path = uploads_dir / excel_path_str.lstrip('/')
        if relative_path.exists():
            return relative_path

        # Try relative to current working directory
        cwd_path = Path.cwd() / excel_path_str
        if cwd_path.exists():
            return cwd_path

        logger.error(f"Excel file not found: {excel_path_str}")
        logger.debug(f"Tried paths: {excel_path}, {relative_path}, {cwd_path}")
        return None

    except Exception as e:
        logger.error(f"Error validating Excel path: {e}")
        return None


def get_static_url(file_path):
    """
    Convert a file system path to a static URL

    Args:
        file_path: Path object or string

    Returns:
        URL string for accessing the file
    """
    try:
        file_path = Path(file_path)

        # Get relative path from uploads directory
        uploads_dir = get_uploads_dir()

        try:
            relative_path = file_path.relative_to(uploads_dir)
            return f"/static/uploads/{relative_path.as_posix()}"
        except ValueError:
            # File is not in uploads directory
            return f"/static/{file_path.name}"

    except Exception as e:
        logger.error(f"Error generating static URL: {e}")
        return None


def log_path_info():
    """Log important path information for debugging"""
    logger.info("=" * 60)
    logger.info("Railway Path Configuration")
    logger.info("=" * 60)
    logger.info(f"Environment: {'Railway' if is_railway_environment() else 'Development'}")
    logger.info(f"CWD: {os.getcwd()}")
    logger.info(f"Uploads dir: {get_uploads_dir()}")
    logger.info(f"Reports dir: {get_reports_dir()}")
    logger.info(f"Templates dir: {get_templates_dir()}")
    logger.info(f"Templates exist: {get_templates_dir().exists()}")

    if get_templates_dir().exists():
        try:
            template_files = list(get_templates_dir().iterdir())
            logger.info(f"Template files: {len(template_files)}")
            for tf in template_files[:5]:  # First 5
                logger.info(f"  - {tf.name}")
        except Exception as e:
            logger.error(f"Error listing templates: {e}")

    logger.info("=" * 60)
