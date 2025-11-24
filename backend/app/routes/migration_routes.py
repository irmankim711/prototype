"""
Migration API routes for fixing data issues
"""

from flask import Blueprint, jsonify
from ..decorators import firebase_auth_required, get_firebase_uid
from ..models import User, UserRole
from ..services.firestore_report_service import firestore_report_service
import logging

logger = logging.getLogger(__name__)

migration_bp = Blueprint('migration', __name__, url_prefix='/api/migration')

@migration_bp.route('/fix-report-ownership', methods=['POST'])
@firebase_auth_required
def fix_report_ownership():
    """
    Admin-only endpoint to migrate existing reports from SQL user IDs to Firebase UIDs

    This fixes the 403 error when downloading old reports that were created
    with SQL user IDs instead of Firebase UIDs.
    """
    try:
        # Check if user is admin
        firebase_uid = get_firebase_uid()
        if not firebase_uid:
            return jsonify({'error': 'Authentication required'}), 401

        user = User.get_by_firebase_uid(firebase_uid)
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403

        logger.info(f"Admin {firebase_uid} starting report ownership migration")

        # Get all reports from Firestore
        if not firestore_report_service._firestore_db:
            return jsonify({
                'success': False,
                'error': 'Firestore not initialized'
            }), 503

        reports = firestore_report_service._firestore_db.collection('reports').stream()

        updated_count = 0
        skipped_count = 0
        error_count = 0
        details = []

        for doc in reports:
            report_id = doc.id
            report_data = doc.to_dict()

            created_by = report_data.get('createdBy', {})
            current_user_id = created_by.get('userId')

            if not current_user_id:
                details.append(f"Report {report_id}: No userId found, skipping")
                skipped_count += 1
                continue

            # Check if it's already a Firebase UID (contains letters) or SQL ID (only digits)
            if not str(current_user_id).isdigit():
                details.append(f"Report {report_id}: Already using Firebase UID, skipping")
                skipped_count += 1
                continue

            # It's a SQL user ID, need to convert to Firebase UID
            try:
                # Query User table to get Firebase UID
                sql_user = User.query.get(int(current_user_id))

                if not sql_user:
                    details.append(f"Report {report_id}: User {current_user_id} not found")
                    error_count += 1
                    continue

                if not sql_user.firebase_uid:
                    details.append(f"Report {report_id}: User {current_user_id} has no Firebase UID")
                    error_count += 1
                    continue

                # Update the report with Firebase UID
                doc_ref = firestore_report_service._firestore_db.collection('reports').document(report_id)
                doc_ref.update({
                    'createdBy.userId': sql_user.firebase_uid
                })

                details.append(f"Report {report_id}: Updated from '{current_user_id}' to '{sql_user.firebase_uid}'")
                updated_count += 1

            except Exception as e:
                details.append(f"Report {report_id}: Error - {str(e)}")
                error_count += 1

        logger.info(f"Migration completed: {updated_count} updated, {skipped_count} skipped, {error_count} errors")

        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'details': details
        })

    except Exception as e:
        logger.error(f"Error in migration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
