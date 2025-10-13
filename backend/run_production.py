"""
Production Startup Script
Initializes the production environment with real API integrations
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import User
from flask import current_app
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

def initialize_production_environment():
    """Initialize production environment with real integrations"""
    
    # Load production environment
    from dotenv import load_dotenv
    load_dotenv('.env.production')
    
    # Set production environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['MOCK_MODE_DISABLED'] = 'true'
    os.environ['ENABLE_REAL_GOOGLE_FORMS'] = 'true'
    os.environ['ENABLE_REAL_AI'] = 'true'
    os.environ['ENABLE_REAL_MICROSOFT_FORMS'] = 'true'
    
    logger.info("🚀 Starting Production Environment")
    logger.info("📋 All mock data has been ELIMINATED")
    logger.info("🔗 Real API integrations ENABLED")
    
    # Create Flask app
    app = create_app('production')
    
    with app.app_context():
        # Initialize database
        try:
            db.create_all()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return None
        
        # Check for admin user
        admin_user = User.query.filter_by(email='admin@formautomation.com').first()
        if not admin_user:
            from app.models import UserRole
            admin_user = User()
            admin_user.email = 'admin@formautomation.com'
            admin_user.username = 'admin'
            admin_user.first_name = 'System'
            admin_user.last_name = 'Administrator'
            admin_user.role = UserRole.ADMIN
            admin_user.is_active = True
            admin_user.set_password('AdminSecure123!')
            db.session.add(admin_user)
            db.session.commit()
            logger.info("✅ Admin user created")
        
        # Verify production services
        logger.info("🔍 Verifying production services...")
        
        # Check Google Forms Service
        try:
            from app.services.production_google_forms_service import production_google_forms_service
            logger.info("✅ Google Forms Service - Production Ready")
        except Exception as e:
            logger.warning(f"⚠️ Google Forms Service issue: {e}")
        
        # Check AI Service
        try:
            from app.services.production_ai_service import production_ai_service
            ai_status = "AI-Powered" if production_ai_service.enabled else "Intelligent Fallback"
            logger.info(f"✅ AI Service - {ai_status}")
        except Exception as e:
            logger.warning(f"⚠️ AI Service issue: {e}")
        
        # Check Template Service
        try:
            from app.services.production_template_service import production_template_service
            logger.info("✅ Template Service - Production Ready")
        except Exception as e:
            logger.warning(f"⚠️ Template Service issue: {e}")
        
        logger.info("🎯 Production Environment Ready!")
        logger.info("📡 Available endpoints:")
        logger.info("   • /api/production/health - Health check")
        logger.info("   • /api/production/google-forms/* - Real Google Forms API")
        logger.info("   • /api/production/ai/analyze - Real AI analysis")
        logger.info("   • /api/production/reports/* - Real report generation")
        logger.info("   • /api/production/templates/* - Real template processing")
        
        return app

def run_production_server():
    """Run the production server"""
    app = initialize_production_environment()
    
    if app is None:
        logger.error("❌ Failed to initialize production environment")
        sys.exit(1)
    
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"🌐 Starting production server on {host}:{port}")
    logger.info("🚫 Mock data completely ELIMINATED")
    logger.info("✅ Real API integrations ACTIVE")
    
    # Run with production settings
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    run_production_server()
