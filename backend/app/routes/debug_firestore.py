"""
Debug endpoint to check Firestore connection and templates
"""
import logging
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

debug_firestore_bp = Blueprint('debug_firestore', __name__)

@debug_firestore_bp.route('/api/debug/firestore', methods=['GET'])
def debug_firestore():
    """Debug Firestore connection and templates"""
    try:
        from ..middleware.firebase_auth import firebase_auth_manager
        from ..services.firestore_template_service import FirestoreTemplateService

        result = {
            'firebase_initialized': firebase_auth_manager._initialized,
            'firestore_available': False,
            'templates_count': 0,
            'templates': [],
            'error': None
        }

        if not firebase_auth_manager._initialized:
            result['error'] = 'Firebase not initialized'
            return jsonify(result), 500

        # Try to get Firestore DB
        try:
            firestore_db = firebase_auth_manager._firestore_db
            result['firestore_available'] = firestore_db is not None

            if firestore_db:
                # Try to list templates directly
                templates_ref = firestore_db.collection('templates')
                templates = list(templates_ref.stream())

                result['templates_count'] = len(templates)
                result['templates'] = [
                    {
                        'id': t.id,
                        'name': t.to_dict().get('name'),
                        'active': t.to_dict().get('is_active'),
                        'type': t.to_dict().get('template_type')
                    }
                    for t in templates
                ]

                logger.info(f"✅ Direct Firestore query found {len(templates)} templates")
            else:
                result['error'] = 'Firestore DB is None'

        except Exception as e:
            result['error'] = f'Firestore access error: {str(e)}'
            logger.error(f"Firestore access error: {e}")
            import traceback
            result['traceback'] = traceback.format_exc()

        # Also try through service
        try:
            service = FirestoreTemplateService()
            service_templates = service.get_all_templates(active_only=False)
            result['service_templates_count'] = len(service_templates)
            result['service_initialized'] = service._initialized
        except Exception as e:
            result['service_error'] = str(e)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
