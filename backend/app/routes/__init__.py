# Routes package
import logging
from flask import current_app

# Configure logger for this module
logger = logging.getLogger(__name__)

def register_routes():
    """Register all route blueprints with error handling and logging."""
    blueprints = {}
    
    try:
        # Import dashboard routes
        from .dashboard import dashboard_bp
        blueprints['dashboard'] = dashboard_bp
        logger.info("✅ Dashboard routes imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import dashboard routes: {e}")
        raise
    
    try:
        # Import API routes
        from .api import api
        blueprints['api'] = api
        logger.info("✅ API routes imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import API routes: {e}")
        raise
    
    try:
        # Import users routes
        from .users import users_bp
        blueprints['users'] = users_bp
        logger.info("✅ Users routes imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import users routes: {e}")
        raise
    
    try:
        # Import forms routes - UNCOMMENTED AND FIXED
        from .forms import forms_bp
        blueprints['forms'] = forms_bp
        logger.info("✅ Forms routes imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import forms routes: {e}")
        # Don't raise here - forms might not be critical for basic functionality
        logger.warning("⚠️ Forms routes import failed, continuing without forms functionality")
    
    try:
        # Import files routes
        from .files import files_bp
        blueprints['files'] = files_bp
        logger.info("✅ Files routes imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import files routes: {e}")
        raise
    
    try:
        # Import additional route modules if they exist
        from .analytics import analytics_bp
        blueprints['analytics'] = analytics_bp
        logger.info("✅ Analytics routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Analytics routes not available, skipping")
    
    try:
        from .admin_forms import admin_forms_bp
        blueprints['admin_forms'] = admin_forms_bp
        logger.info("✅ Admin forms routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Admin forms routes not available, skipping")
    
    try:
        from .mvp import mvp
        blueprints['mvp'] = mvp
        logger.info("✅ MVP routes imported successfully")
    except ImportError:
        logger.info("ℹ️ MVP routes not available, skipping")
    
    try:
        from .quick_auth import quick_auth_bp
        blueprints['quick_auth'] = quick_auth_bp
        logger.info("✅ Quick auth routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Quick auth routes not available, skipping")
    
    try:
        from .ai_reports import ai_reports_bp
        blueprints['ai_reports'] = ai_reports_bp
        logger.info("✅ AI reports routes imported successfully")
    except ImportError:
        logger.info("ℹ️ AI reports routes not available, skipping")
    
    try:
        from .public_forms import public_forms_bp
        blueprints['public_forms'] = public_forms_bp
        logger.info("✅ Public forms routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Public forms routes not available, skipping")
    
    try:
        from .google_forms_routes import google_forms_bp
        blueprints['google_forms'] = google_forms_bp
        logger.info("✅ Google forms routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Google forms routes not available, skipping")
    
    try:
        from .production_routes import production_bp
        blueprints['production'] = production_bp
        logger.info("✅ Production routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Production routes not available, skipping")
    
    try:
        from .production_api import production_api
        blueprints['production_api'] = production_api
        logger.info("✅ Production API routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Production API routes not available, skipping")
    
    try:
        from .enhanced_report_routes import enhanced_report_bp
        blueprints['enhanced_report'] = enhanced_report_bp
        logger.info("✅ Enhanced report routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Enhanced report routes not available, skipping")
    
    try:
        from .reports_export import reports_export_bp
        blueprints['reports_export'] = reports_export_bp
        logger.info("✅ Reports export routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Reports export routes not available, skipping")
    
    try:
        from .nextgen_report_builder import nextgen_bp
        blueprints['nextgen'] = nextgen_bp
        logger.info("✅ NextGen report builder routes imported successfully")
    except ImportError:
        logger.info("ℹ️ NextGen report builder routes not available, skipping")
    
    try:
        from .reports_api import reports_bp
        blueprints['reports'] = reports_bp
        logger.info("✅ Reports API routes imported successfully")
    except ImportError:
        logger.info("ℹ️ Reports API routes not available, skipping")
    
    logger.info(f"🎯 Successfully imported {len(blueprints)} route modules")
    return blueprints

# Legacy imports for backward compatibility
try:
    from .dashboard import dashboard_bp
    from .api import api
    from .users import users_bp
    from .forms import forms_bp  # UNCOMMENTED
    from .files import files_bp
    
    __all__ = ['dashboard_bp', 'api', 'users_bp', 'forms_bp', 'files_bp']
    logger.info("✅ Legacy imports completed successfully")
except ImportError as e:
    logger.error(f"❌ Legacy import failed: {e}")
    # Provide fallback empty blueprints to prevent crashes
    from flask import Blueprint
    dashboard_bp = Blueprint('dashboard', __name__)
    api = Blueprint('api', __name__)
    users_bp = Blueprint('users', __name__)
    forms_bp = Blueprint('forms', __name__)
    files_bp = Blueprint('files', __name__)
    __all__ = ['dashboard_bp', 'api', 'users_bp', 'forms_bp', 'files_bp']
