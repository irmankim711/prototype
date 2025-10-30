"""
Routes module initialization
Registers all blueprint modules with the Flask application
"""

def register_blueprints(app):
    """
    Register all blueprint modules with the Flask application
    Conservative registration to avoid application context issues

    Args:
        app: Flask application instance
    """

    # Core authentication routes (essential for login)
    try:
        from app.routes.firebase_auth import firebase_auth_bp
        app.register_blueprint(firebase_auth_bp, url_prefix='/auth/firebase')
        app.logger.info("✅ Firebase auth routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import firebase_auth: {e}")

    try:
        from app.routes.firebase_auth_routes import firebase_auth_bp as firebase_auth_routes_bp
        app.register_blueprint(firebase_auth_routes_bp, name='firebase_auth_routes')
        app.logger.info("✅ Firebase auth routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import firebase_auth_routes: {e}")

    # Register auth routes under /api/auth for frontend compatibility
    try:
        from app.routes.firebase_auth_routes import firebase_auth_bp as firebase_auth_api_bp

        # Create a new blueprint with /api/auth prefix
        from flask import Blueprint, request, jsonify
        api_auth_bp = Blueprint('api_auth', __name__, url_prefix='/api/auth')

        # Copy the routes from firebase_auth_routes_bp to api_auth_bp
        @api_auth_bp.route('/firebase-sync', methods=['POST', 'OPTIONS'])
        @api_auth_bp.route('/firebase-login', methods=['POST', 'OPTIONS'])
        @api_auth_bp.route('/register', methods=['POST', 'OPTIONS'])  # Alias for registration
        def api_firebase_sync():
            # Handle OPTIONS request for CORS preflight
            if request.method == 'OPTIONS':
                return jsonify({'status': 'ok'}), 200
            from app.routes.firebase_auth_routes import firebase_sync
            return firebase_sync()

        @api_auth_bp.route('/verify-token', methods=['POST', 'OPTIONS'])
        def api_verify_token():
            # Handle OPTIONS request for CORS preflight
            if request.method == 'OPTIONS':
                return jsonify({'status': 'ok'}), 200
            from app.routes.firebase_auth_routes import verify_token
            return verify_token()

        @api_auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
        def api_logout():
            # Handle OPTIONS request for CORS preflight
            if request.method == 'OPTIONS':
                return jsonify({'status': 'ok'}), 200
            from app.routes.firebase_auth_routes import logout
            return logout()

        app.register_blueprint(api_auth_bp)
        app.logger.info("✅ API auth routes registered under /api/auth")
    except Exception as e:
        app.logger.warning(f"Could not register API auth routes: {e}")

    try:
        from app.routes.quick_auth import quick_auth_bp
        app.register_blueprint(quick_auth_bp, url_prefix='/auth/quick')
        app.logger.info("✅ Quick auth routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import quick_auth: {e}")

    # Enhanced user profile routes (with proper auth)
    try:
        from app.routes.enhanced_user_routes import enhanced_user_bp
        app.register_blueprint(enhanced_user_bp)  # Already has prefix /api/users
        app.logger.info("✅ Enhanced user routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import enhanced_user_routes: {e}")

    # Basic API routes (admin/manager routes only - profile routes handled by enhanced_user_routes)
    try:
        from app.routes.users import users_bp
        # Note: Only register admin routes, not profile routes (those are in enhanced_user_routes)
        # Register without url_prefix to avoid conflicts with enhanced routes
        # app.register_blueprint(users_bp, url_prefix='/api/users')
        # app.logger.info("✅ Users routes registered")
        app.logger.info("ℹ️ Basic users routes skipped (using enhanced_user_routes instead)")
    except Exception as e:
        app.logger.warning(f"Could not import users: {e}")

    try:
        from app.routes.forms import forms_bp
        app.register_blueprint(forms_bp, url_prefix='/api/forms')
        app.logger.info("✅ Forms routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import forms: {e}")

    try:
        from app.routes.public_forms import public_forms_bp
        app.register_blueprint(public_forms_bp, url_prefix='/public')
        app.logger.info("✅ Public forms routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import public_forms: {e}")

    # Simple reports routes
    try:
        from app.routes.reports_api import reports_bp
        app.register_blueprint(reports_bp)  # Already has prefix
        app.logger.info("✅ Reports API routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import reports_api: {e}")

    # Files and static routes
    try:
        from app.routes.files import files_bp
        app.register_blueprint(files_bp, url_prefix='/api/files')
        app.logger.info("✅ Files routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import files: {e}")

    try:
        from app.routes.static_files import static_bp
        app.register_blueprint(static_bp)  # Already has prefix
        app.logger.info("✅ Static files routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import static_files: {e}")

    # Analytics routes
    try:
        from app.routes.analytics import analytics_bp
        app.register_blueprint(analytics_bp)  # Already has prefix
        app.logger.info("✅ Analytics routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import analytics: {e}")

    # Dashboard routes
    try:
        from app.routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp)  # Already has prefix /api/dashboard
        app.logger.info("✅ Dashboard routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import dashboard: {e}")

    # Health check routes (simple)
    try:
        from flask import Blueprint, jsonify
        simple_health_bp = Blueprint('simple_health', __name__)

        @simple_health_bp.route('/', methods=['GET'])
        def root():
            return jsonify({
                'status': 'ok',
                'message': 'Automated Report Platform API',
                'version': '1.0.0',
                'endpoints': {
                    'health': '/api/health',
                    'docs': '/api/docs',
                    'auth': '/api/auth',
                    'forms': '/api/forms',
                    'reports': '/api/reports'
                }
            })

        @simple_health_bp.route('/api/health', methods=['GET'])
        def simple_health():
            return jsonify({'status': 'ok', 'message': 'Server is running'})

        app.register_blueprint(simple_health_bp)
        app.logger.info("✅ Simple health routes registered")
    except Exception as e:
        app.logger.warning(f"Could not register simple health routes: {e}")

    # Database health (simple one)
    try:
        from app.routes.database_health import db_health_bp
        app.register_blueprint(db_health_bp)  # Already has prefix
        app.logger.info("✅ Database health routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import database_health: {e}")

    # Editor API routes (for nextgen)
    try:
        from app.routes.editor_api import editor_bp
        app.register_blueprint(editor_bp)  # Already has prefix /api/v1/editor
        app.logger.info("✅ Editor API routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import editor_api: {e}")

    # Enhanced report routes
    try:
        from app.routes.enhanced_report_routes import enhanced_report_bp
        app.register_blueprint(enhanced_report_bp)  # Already has prefix
        app.logger.info("✅ Enhanced report routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import enhanced_report_routes: {e}")

    # Excel export routes
    try:
        from app.routes.excel_export_api import excel_export_bp
        app.register_blueprint(excel_export_bp)  # Already has prefix
        app.logger.info("✅ Excel export routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import excel_export_api: {e}")

    # Excel to PDF routes
    try:
        from app.routes.excel_to_pdf_api import excel_to_pdf_bp
        app.register_blueprint(excel_to_pdf_bp)  # Already has prefix /api/excel-to-pdf
        app.logger.info("✅ Excel to PDF routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import excel_to_pdf_api: {e}")

    # NextGen report builder
    try:
        from app.routes.nextgen_report_builder import nextgen_bp
        app.register_blueprint(nextgen_bp, url_prefix='/api/v1/nextgen')
        app.logger.info("✅ NextGen report builder routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import nextgen_report_builder: {e}")

    # Integration API routes (placeholder)
    try:
        from app.routes.integrations_api import integrations_bp
        app.register_blueprint(integrations_bp)  # Already has prefix
        app.logger.info("✅ Integration API routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import integrations_api: {e}")

    # Templates API routes
    try:
        from app.routes.templates_api import templates_api
        app.register_blueprint(templates_api)  # Already has prefix /api/v1/templates
        app.logger.info("✅ Templates API routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import templates_api: {e}")

    # Reports export routes
    try:
        from app.routes.reports_export import reports_export_bp
        app.register_blueprint(reports_export_bp)  # Already has prefix /api/reports/export
        app.logger.info("✅ Reports export routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import reports_export: {e}")

    # Google Forms integration routes
    try:
        from app.routes.google_forms_routes import google_forms_bp
        app.register_blueprint(google_forms_bp)  # Already has prefix /api/google-forms
        app.logger.info("✅ Google Forms routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import google_forms_routes: {e}")

    # Form data export routes (Excel, CSV, Google Sheets export)
    try:
        from app.routes.form_data_export_routes import register_export_blueprints
        register_export_blueprints(app)
        app.logger.info("✅ Form data export routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import form_data_export_routes: {e}")

    # Settings API routes
    try:
        from app.routes.settings_api import settings_api
        app.register_blueprint(settings_api)  # Already has prefix /api/settings
        app.logger.info("✅ Settings API routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import settings_api: {e}")

    # Firebase Reports API routes (NEW - Firebase Storage + Firestore integration)
    try:
        from app.routes.firebase_reports_api import firebase_reports_bp
        app.register_blueprint(firebase_reports_bp)  # Already has prefix /api/firebase-reports
        app.logger.info("✅ Firebase Reports API routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import firebase_reports_api: {e}")

    # AI-Enhanced Excel Generation routes
    try:
        from app.routes.ai_excel_api import ai_excel_bp
        app.register_blueprint(ai_excel_bp)  # Already has prefix /api/ai-excel
        app.logger.info("✅ AI-Enhanced Excel routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import ai_excel_api: {e}")

    app.logger.info("🎯 Blueprint registration completed - added missing API routes")
