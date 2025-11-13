"""
Routes module initialization
Registers all blueprint modules with the Flask application
"""
import traceback

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

        @api_auth_bp.route('/login', methods=['POST', 'OPTIONS'])
        def api_login():
            """Standard login endpoint - redirects to Firebase login"""
            # Handle OPTIONS request for CORS preflight
            if request.method == 'OPTIONS':
                return jsonify({'status': 'ok'}), 200
            from app.routes.firebase_auth_routes import firebase_sync
            return firebase_sync()

        @api_auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
        def api_logout():
            """Logout endpoint - Always succeeds to ensure users can logout"""
            from datetime import datetime
            from app import db
            from app.middleware.firebase_auth import firebase_auth_manager
            import logging
            import traceback

            logger = logging.getLogger(__name__)

            # Handle OPTIONS request for CORS preflight
            if request.method == 'OPTIONS':
                return jsonify({'status': 'ok'}), 200

            try:
                logger.info("🔄 Logout endpoint called")

                # Try to get user info if token is valid (optional)
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    try:
                        token = auth_header.replace('Bearer ', '')
                        if firebase_auth_manager._initialized:
                            decoded_token = firebase_auth_manager.verify_token(token)
                            if decoded_token:
                                email = decoded_token.get('email')
                                firebase_uid = decoded_token.get('uid')

                                # Try to update user logout time (optional, non-critical)
                                try:
                                    from app.models.production.user_models import User
                                    user = User.query.filter_by(firebase_uid=firebase_uid).first()
                                    if user:
                                        user.updated_at = datetime.utcnow()
                                        db.session.commit()
                                        logger.info(f"✅ User {user.id} ({email}) logged out")
                                except Exception as db_error:
                                    # Don't fail logout if DB update fails
                                    logger.warning(f"⚠️ Could not update user logout time: {str(db_error)}")
                                    try:
                                        db.session.rollback()
                                    except:
                                        pass
                    except Exception as token_error:
                        # Token might be expired or invalid - that's OK for logout
                        logger.info(f"ℹ️ Logout with invalid/expired token: {str(token_error)}")
                        pass

                # Always return success for logout (even with expired/invalid tokens)
                from flask import make_response
                response = make_response(jsonify({
                    'success': True,
                    'message': 'Logout successful'
                }))

                # Clear any cookies that might exist
                response.set_cookie('session', '', expires=0, path='/')
                response.set_cookie('remember_token', '', expires=0, path='/')

                logger.info("✅ Logout completed successfully")
                return response, 200

            except Exception as e:
                # Even if there's an error, return success for logout
                # We don't want to prevent users from logging out
                logger.error(f"⚠️ Logout error (returning success anyway): {str(e)}")
                logger.error(f"📋 Stack trace: {traceback.format_exc()}")

                from flask import make_response
                response = make_response(jsonify({
                    'success': True,
                    'message': 'Logout successful'
                }))

                # Still try to clear cookies even on error
                response.set_cookie('session', '', expires=0, path='/')
                response.set_cookie('remember_token', '', expires=0, path='/')

                return response, 200

        app.register_blueprint(api_auth_bp)
        app.logger.info("✅ API auth routes registered under /api/auth")
    except Exception as e:
        app.logger.warning(f"Could not register API auth routes: {e}")

    # Add /auth/login route without /api prefix for compatibility
    try:
        from flask import Blueprint, request, jsonify
        auth_compat_bp = Blueprint('auth_compat', __name__, url_prefix='/auth')

        @auth_compat_bp.route('/login', methods=['POST', 'OPTIONS'])
        def compat_login():
            """Compatibility login endpoint - works with /auth/login"""
            if request.method == 'OPTIONS':
                return jsonify({'status': 'ok'}), 200
            from app.routes.firebase_auth_routes import firebase_sync
            return firebase_sync()

        app.register_blueprint(auth_compat_bp)
        app.logger.info("✅ Auth compatibility routes registered under /auth")
    except Exception as e:
        app.logger.warning(f"Could not register auth compatibility routes: {e}")

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

    # Health check routes (simple) - REMOVED (now in app/__init__.py for faster startup)
    # The /api/health endpoint is registered directly in the Flask app factory
    # This ensures it's available immediately without waiting for blueprint registration
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

        @simple_health_bp.route('/api/debug/routes', methods=['GET'])
        def debug_routes():
            """Debug endpoint to show all registered routes - restricted to development"""
            import os
            from flask import current_app
            
            # Only allow in development environment
            if current_app.config.get('ENV') != 'development' and os.environ.get('FLASK_ENV') != 'development':
                return jsonify({'error': 'Not Found'}), 404
            
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'path': str(rule)
                })
            return jsonify({
                'total_routes': len(routes),
                'routes': sorted(routes, key=lambda x: x['path']),
                'nextgen_routes': [r for r in routes if 'nextgen' in r['path'].lower()]
            })

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
    nextgen_import_error = None
    try:
        from app.routes.nextgen_report_builder import nextgen_bp
        app.register_blueprint(nextgen_bp, url_prefix='/api/v1/nextgen')
        app.logger.info("✅ NextGen report builder routes registered")

        # Log all nextgen routes for debugging
        import sys
        nextgen_routes = [str(rule) for rule in app.url_map.iter_rules() if 'nextgen' in str(rule)]
        app.logger.info(f"📋 NextGen routes available: {len(nextgen_routes)} routes")
        if app.config.get('DEBUG') or 'RAILWAY' in sys.modules:
            for route in nextgen_routes[:5]:  # Log first 5 routes
                app.logger.info(f"  - {route}")
    except Exception as e:
        nextgen_import_error = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        app.logger.exception("Could not import nextgen_report_builder")

    # Add error endpoint for debugging
    if nextgen_import_error:
        from flask import Blueprint, jsonify
        error_bp = Blueprint('nextgen_error', __name__)

        @error_bp.route('/api/debug/nextgen-error', methods=['GET'])
        def get_nextgen_error():
            return jsonify(nextgen_import_error)

        app.register_blueprint(error_bp)
        app.logger.info("✅ NextGen error debug endpoint registered")

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

    # Debug route for Google Forms (temporary)
    try:
        from app.routes.debug_google_forms import debug_gf_bp
        app.register_blueprint(debug_gf_bp)
        app.logger.info("✅ Debug Google Forms routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import debug_google_forms: {e}")

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

    # Railway diagnostics routes
    try:
        from app.routes.railway_diagnostics import railway_diag_bp
        app.register_blueprint(railway_diag_bp, url_prefix='/api/railway')
        app.logger.info("✅ Railway diagnostics routes registered")
    except Exception as e:
        app.logger.warning(f"Could not import railway_diagnostics: {e}")

    app.logger.info("🎯 Blueprint registration completed - added missing API routes")
