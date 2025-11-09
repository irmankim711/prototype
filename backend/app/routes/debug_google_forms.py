"""
Temporary debug route to see raw Google Forms structure
"""
from flask import Blueprint, jsonify
from ..decorators import firebase_auth_required, get_current_user_id
from ..services.google_forms_service import google_forms_service
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

debug_gf_bp = Blueprint('debug_google_forms', __name__, url_prefix='/api/debug/google-forms')

@debug_gf_bp.route('/forms/<form_id>/raw-structure', methods=['GET'])
@firebase_auth_required
def get_raw_form_structure(form_id: str):
    """Get RAW form structure from Google API for debugging"""
    try:
        user_id = get_current_user_id()

        if not google_forms_service or not google_forms_service.is_enabled():
            return jsonify({'error': 'Google Forms service not available'}), 503

        credentials = google_forms_service._get_user_credentials(str(user_id))
        if not credentials:
            return jsonify({'error': 'No credentials found'}), 401

        forms_service = build('forms', 'v1', credentials=credentials)
        form = forms_service.forms().get(formId=form_id).execute()

        # Return raw structure
        return jsonify({
            'success': True,
            'form_title': form.get('info', {}).get('title'),
            'total_items': len(form.get('items', [])),
            'items': form.get('items', []),
            'full_form': form
        })

    except Exception as e:
        logger.error(f"Error getting raw form structure: {e}")
        return jsonify({'error': str(e)}), 500
