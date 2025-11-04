"""
Railway Deployment Diagnostics Endpoint
Helps identify issues with file paths, permissions, and dependencies on Railway
"""

from flask import Blueprint, jsonify, current_app
from pathlib import Path
import os
import sys
import importlib.util

railway_diag_bp = Blueprint('railway_diagnostics', __name__)


@railway_diag_bp.route('/diagnose', methods=['GET'])
def diagnose_railway_environment():
    """
    Comprehensive diagnostic endpoint for Railway deployment issues
    Checks:
    - File system paths and permissions
    - Required dependencies
    - Environment variables
    - Directory structure
    """
    diagnostics = {
        'status': 'checking',
        'environment': {},
        'file_system': {},
        'dependencies': {},
        'paths': {},
        'errors': []
    }

    try:
        # 1. Environment Information
        diagnostics['environment'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'temp_dir': os.environ.get('TMPDIR', '/tmp'),
            'home_dir': os.environ.get('HOME', 'not set'),
            'railway_environment': os.environ.get('RAILWAY_ENVIRONMENT', 'not set'),
            'flask_env': os.environ.get('FLASK_ENV', 'not set'),
        }

        # 2. Check critical dependencies
        critical_deps = [
            'flask', 'openpyxl', 'pandas', 'docxtpl', 'python-docx',
            'firebase_admin', 'google.cloud.firestore', 'jinja2'
        ]

        for dep in critical_deps:
            # Handle different import names
            import_name = dep.replace('-', '_').replace('.', '_')
            if dep == 'python-docx':
                import_name = 'docx'
            elif dep.startswith('google.'):
                import_name = dep

            try:
                spec = importlib.util.find_spec(import_name)
                if spec:
                    diagnostics['dependencies'][dep] = {
                        'installed': True,
                        'location': spec.origin if spec.origin else 'built-in'
                    }
                else:
                    diagnostics['dependencies'][dep] = {
                        'installed': False,
                        'error': 'Not found'
                    }
            except Exception as e:
                diagnostics['dependencies'][dep] = {
                    'installed': False,
                    'error': str(e)
                }

        # 3. Check file system paths
        app_root = Path(__file__).parent.parent.parent

        paths_to_check = {
            'app_root': app_root,
            'uploads_dir': app_root / 'uploads',
            'reports_dir': app_root / 'uploads' / 'reports',
            'templates_dir': app_root / 'templates',
            'tmp_dir': Path('/tmp'),
            'tmp_uploads': Path('/tmp/uploads'),
            'tmp_reports': Path('/tmp/uploads/reports'),
        }

        for name, path in paths_to_check.items():
            try:
                path_info = {
                    'path': str(path),
                    'exists': path.exists(),
                    'is_dir': path.is_dir() if path.exists() else False,
                    'is_file': path.is_file() if path.exists() else False,
                    'readable': os.access(str(path), os.R_OK) if path.exists() else False,
                    'writable': os.access(str(path), os.W_OK) if path.exists() else False,
                }

                # Try to list contents if directory exists
                if path.exists() and path.is_dir():
                    try:
                        contents = list(path.iterdir())
                        path_info['file_count'] = len(contents)
                        path_info['contents_sample'] = [f.name for f in contents[:5]]
                    except Exception as e:
                        path_info['list_error'] = str(e)

                diagnostics['paths'][name] = path_info

            except Exception as e:
                diagnostics['paths'][name] = {
                    'path': str(path),
                    'error': str(e)
                }

        # 4. Check template files
        templates_dir = app_root / 'templates'
        if templates_dir.exists():
            try:
                template_files = [f.name for f in templates_dir.iterdir() if f.is_file()]
                diagnostics['file_system']['templates'] = {
                    'count': len(template_files),
                    'files': template_files[:10]  # First 10
                }
            except Exception as e:
                diagnostics['file_system']['templates'] = {'error': str(e)}

        # 5. Test write permissions
        try:
            test_file = Path('/tmp/railway_write_test.txt')
            test_file.write_text('test')
            diagnostics['file_system']['tmp_writable'] = True
            test_file.unlink()
        except Exception as e:
            diagnostics['file_system']['tmp_writable'] = False
            diagnostics['errors'].append(f'Cannot write to /tmp: {str(e)}')

        # 6. Check Flask config
        try:
            diagnostics['flask_config'] = {
                'UPLOAD_FOLDER': current_app.config.get('UPLOAD_FOLDER'),
                'MAX_CONTENT_LENGTH': current_app.config.get('MAX_CONTENT_LENGTH'),
                'DEBUG': current_app.config.get('DEBUG'),
            }
        except Exception as e:
            diagnostics['errors'].append(f'Flask config error: {str(e)}')

        # 7. Check if services can be imported
        try:
            from app.services.excel_parser import ExcelParserService
            diagnostics['services'] = diagnostics.get('services', {})
            diagnostics['services']['excel_parser'] = 'OK'
        except Exception as e:
            diagnostics['services'] = diagnostics.get('services', {})
            diagnostics['services']['excel_parser'] = f'ERROR: {str(e)}'

        try:
            from app.services.form_automation import FormAutomationService
            diagnostics['services']['form_automation'] = 'OK'
        except Exception as e:
            diagnostics['services']['form_automation'] = f'ERROR: {str(e)}'

        # Set overall status
        if len(diagnostics['errors']) == 0:
            diagnostics['status'] = 'healthy'
        else:
            diagnostics['status'] = 'issues_found'

    except Exception as e:
        diagnostics['status'] = 'error'
        diagnostics['errors'].append(f'Diagnostic error: {str(e)}')

    return jsonify(diagnostics), 200
