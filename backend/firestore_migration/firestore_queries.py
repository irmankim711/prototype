"""
Firestore Query Functions
=========================

This module replaces SQL queries with Firestore queries.
All functions use synchronous Firestore operations and are optimized for
Firestore's query limitations.

IMPORTANT: This module uses the synchronous Firestore client (firestore.Client).
All methods execute synchronously - they do NOT return coroutines.

For async operations, consider migrating to:
    from google.cloud.firestore import AsyncClient

Usage:
    from firestore_queries import FirestoreQueries

    queries = FirestoreQueries(firestore_client)
    user = queries.get_user_by_email('user@example.com')
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter, Query
from google.cloud.firestore_v1.base_query import BaseCompositeFilter
import logging

logger = logging.getLogger(__name__)


class FirestoreQueries:
    """Firestore query functions replacing SQL queries"""

    def __init__(self, db: firestore.Client):
        """
        Initialize with a Firestore client.

        Args:
            db: Synchronous Firestore client instance
        """
        self.db = db

    # =========================================================================
    # USER QUERIES
    # =========================================================================

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        doc = self.db.collection('users').document(user_id).get()
        return doc.to_dict() if doc.exists else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email (for login)"""
        users = self.db.collection('users') \
            .where(filter=FieldFilter('email', '==', email)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .limit(1) \
            .stream()

        for user in users:
            return {'id': user.id, **user.to_dict()}
        return None

    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[Dict]:
        """Get user by Firebase UID"""
        users = self.db.collection('users') \
            .where(filter=FieldFilter('firebaseUid', '==', firebase_uid)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .limit(1) \
            .stream()

        for user in users:
            return {'id': user.id, **user.to_dict()}
        return None

    def create_user(self, user_data: Dict) -> str:
        """Create a new user"""
        user_data['createdAt'] = firestore.SERVER_TIMESTAMP
        user_data['updatedAt'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('users').document()
        user_data['userId'] = doc_ref.id
        doc_ref.set(user_data)

        return doc_ref.id

    def update_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Update user profile"""
        try:
            self.db.collection('users').document(user_id).update({
                'profile': profile_data,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False

    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            self.db.collection('users').document(user_id).update({
                'lastLogin': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
            return False

    def get_users_by_role(self, role: str, limit: int = 50) -> List[Dict]:
        """Get users by role"""
        users = self.db.collection('users') \
            .where(filter=FieldFilter('role', '==', role)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .limit(limit) \
            .stream()

        return [{'id': u.id, **u.to_dict()} for u in users]

    def search_users(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search users by name or email
        Note: Firestore doesn't support LIKE queries, so we use array-contains
        """
        search_term_lower = search_term.lower()

        users = self.db.collection('users') \
            .where(filter=FieldFilter('searchTerms', 'array_contains', search_term_lower)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .limit(limit) \
            .stream()

        return [{'id': u.id, **u.to_dict()} for u in users]

    def get_user_statistics(self) -> Dict:
        """
        Get aggregate user statistics using Firestore aggregation queries.

        This method uses Firestore's count() aggregation to avoid loading
        all users into memory, which is efficient even with large datasets.

        Note: Firestore count() operations have limitations:
        - Each count query counts as 1 document read
        - Maximum accuracy up to 1000 documents (estimates beyond that)

        For best performance with very large user bases (100k+ users),
        consider maintaining a separate 'statistics' document that gets
        updated via Cloud Functions/Firestore triggers on user create/update/delete.

        Returns:
            Dict with user count statistics
        """
        try:
            stats = {}

            # Total users - use count aggregation
            total_query = self.db.collection('users').count()
            total_result = total_query.get()  # type: ignore
            # Access the count value from the aggregation result
            stats['total_users'] = total_result[0][0].value  # type: ignore

            # Active users
            active_query = self.db.collection('users') \
                .where(filter=FieldFilter('isActive', '==', True)) \
                .count()
            active_result = active_query.get()  # type: ignore
            stats['active_users'] = active_result[0][0].value  # type: ignore

            # Inactive users (calculated from total - active)
            stats['inactive_users'] = stats['total_users'] - stats['active_users']

            # Admin users
            admin_query = self.db.collection('users') \
                .where(filter=FieldFilter('role', '==', 'admin')) \
                .count()
            admin_result = admin_query.get()  # type: ignore
            stats['admin_users'] = admin_result[0][0].value  # type: ignore

            # Regular users (calculated from total - admin)
            stats['regular_users'] = stats['total_users'] - stats['admin_users']

            logger.info(f"Retrieved user statistics: {stats}")
            return stats

        except AttributeError as e:
            # Fallback: If count() aggregation is not available or fails,
            # warn and provide a recommendation
            logger.warning(
                f"Firestore count() aggregation failed: {e}. "
                "Consider upgrading google-cloud-firestore to >= 2.7.0 or "
                "maintaining statistics in a separate document."
            )
            return {
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'admin_users': 0,
                'regular_users': 0,
                'error': 'Aggregation not supported. Upgrade firestore library or use maintained stats.'
            }
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'admin_users': 0,
                'regular_users': 0
            }

    # =========================================================================
    # USER SESSION QUERIES
    # =========================================================================

    def create_session(self, user_id: str, session_data: Dict) -> str:
        """Create a new user session"""
        session_data['createdAt'] = firestore.SERVER_TIMESTAMP
        session_data['lastActivity'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('users').document(user_id) \
            .collection('sessions').document()

        session_data['sessionId'] = doc_ref.id
        doc_ref.set(session_data)

        return doc_ref.id

    def get_session_by_token(self, session_token: str) -> Optional[Dict]:
        """Get active session by token"""
        # This requires collection group query
        sessions = self.db.collection_group('sessions') \
            .where(filter=FieldFilter('sessionToken', '==', session_token)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .limit(1) \
            .stream()

        for session in sessions:
            # Get parent user ID from path
            user_id = session.reference.parent.parent.id
            return {'id': session.id, 'userId': user_id, **session.to_dict()}
        return None

    def update_session_activity(self, user_id: str, session_id: str) -> bool:
        """Update session last activity"""
        try:
            self.db.collection('users').document(user_id) \
                .collection('sessions').document(session_id).update({
                    'lastActivity': firestore.SERVER_TIMESTAMP
                })
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False

    def end_session(self, user_id: str, session_id: str) -> bool:
        """End a session (logout)"""
        try:
            self.db.collection('users').document(user_id) \
                .collection('sessions').document(session_id).update({
                    'isActive': False,
                    'endedAt': firestore.SERVER_TIMESTAMP
                })
            return True
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False

    def get_active_sessions(self, user_id: str) -> List[Dict]:
        """Get all active sessions for a user"""
        sessions = self.db.collection('users').document(user_id) \
            .collection('sessions') \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .order_by('lastActivity', direction=firestore.Query.DESCENDING) \
            .stream()

        return [{'id': s.id, **s.to_dict()} for s in sessions]
    def create_form(self, form_data: Dict) -> str:
        """Create a new form"""
        transaction = self.db.transaction()
        
        @firestore.transactional
        def create_in_transaction(transaction):
            form_data['createdAt'] = firestore.SERVER_TIMESTAMP
            form_data['updatedAt'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection('forms').document()
            form_data['formId'] = doc_ref.id
            transaction.set(doc_ref, form_data)
            
            if form_data.get('creator', {}).get('userId'):
                user_ref = self.db.collection('users').document(form_data['creator']['userId'])
                transaction.update(user_ref, {
                    'stats.formsCreated': firestore.Increment(1)
                })
            
            return doc_ref.id
        
        return create_in_transaction(transaction)

    async def get_oauth_token(self, user_id: str, platform: str) -> Optional[Dict]:
        """Get active OAuth token for a platform"""
        doc = self.db.collection('users').document(user_id) \
            .collection('tokens').document(platform).get()

        if doc.exists:
            data = doc.to_dict()
            if data.get('isActive'):
                return data
        return None

    async def update_token_usage(self, user_id: str, platform: str) -> bool:
        """Update token usage statistics"""
        try:
            self.db.collection('users').document(user_id) \
                .collection('tokens').document(platform).update({
                    'lastUsed': firestore.SERVER_TIMESTAMP,
                    'usageCount': firestore.Increment(1)
                })
            return True
        except Exception as e:
            logger.error(f"Failed to update token usage: {e}")
            return False

    async def revoke_oauth_token(self, user_id: str, platform: str, reason: str) -> bool:
        """Revoke an OAuth token"""
        try:
            self.db.collection('users').document(user_id) \
                .collection('tokens').document(platform).update({
                    'isActive': False,
                    'revokedAt': firestore.SERVER_TIMESTAMP,
                    'revokeReason': reason
                })
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    # =========================================================================
    # FORM QUERIES
    # =========================================================================

    async def create_form(self, form_data: Dict) -> str:
        """Create a new form"""
        form_data['createdAt'] = firestore.SERVER_TIMESTAMP
        form_data['updatedAt'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('forms').document()
        form_data['formId'] = doc_ref.id
        doc_ref.set(form_data)

        # Increment user's forms created count
        if form_data.get('creator', {}).get('userId'):
            self.db.collection('users').document(form_data['creator']['userId']).update({
                'stats.formsCreated': firestore.Increment(1)
            })

        return doc_ref.id

    async def get_form_by_id(self, form_id: str) -> Optional[Dict]:
        """Get form by ID"""
        doc = self.db.collection('forms').document(form_id).get()
        return doc.to_dict() if doc.exists else None

    async def update_form(self, form_id: str, form_data: Dict) -> bool:
        """Update a form"""
        try:
            form_data['updatedAt'] = firestore.SERVER_TIMESTAMP
            self.db.collection('forms').document(form_id).update(form_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update form: {e}")
            return False

    async def delete_form(self, form_id: str) -> bool:
        """Soft delete a form"""
        try:
            self.db.collection('forms').document(form_id).update({
                'isActive': False,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Failed to delete form: {e}")
            return False

    async def get_forms_by_creator(self, creator_id: str, limit: int = 50) -> List[Dict]:
        """Get all forms created by a user"""
        forms = self.db.collection('forms') \
            .where(filter=FieldFilter('creator.userId', '==', creator_id)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .order_by('createdAt', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()

        return [{'id': f.id, **f.to_dict()} for f in forms]

    async def get_public_forms(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all public forms"""
        forms = self.db.collection('forms') \
            .where(filter=FieldFilter('isPublic', '==', True)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .order_by('createdAt', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .offset(offset) \
            .stream()

        return [{'id': f.id, **f.to_dict()} for f in forms]

    async def increment_form_view_count(self, form_id: str) -> bool:
        """Increment form view count"""
        try:
            self.db.collection('forms').document(form_id).update({
                'stats.viewCount': firestore.Increment(1)
            })
            return True
        except Exception as e:
            logger.error(f"Failed to increment view count: {e}")
            return False

    async def search_forms(self, search_term: str, creator_id: str, limit: int = 50) -> List[Dict]:
        """Search forms by title or description"""
        search_term_lower = search_term.lower()

        forms = self.db.collection('forms') \
            .where(filter=FieldFilter('creator.userId', '==', creator_id)) \
            .where(filter=FieldFilter('searchTerms', 'array_contains', search_term_lower)) \
            .where(filter=FieldFilter('isActive', '==', True)) \
            .limit(limit) \
            .stream()

        return [{'id': f.id, **f.to_dict()} for f in forms]

    # =========================================================================
    # FORM SUBMISSION QUERIES
    # =========================================================================

    async def create_submission(self, form_id: str, submission_data: Dict) -> str:
        """Create a form submission"""
        submission_data['submittedAt'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('forms').document(form_id) \
            .collection('submissions').document()

        submission_data['submissionId'] = doc_ref.id
        doc_ref.set(submission_data)

        # Update form stats
        self.db.collection('forms').document(form_id).update({
            'stats.submissionCount': firestore.Increment(1),
            'stats.lastSubmissionAt': firestore.SERVER_TIMESTAMP
        })

        # Update user stats if submitter is registered
        if submission_data.get('submitter', {}).get('userId'):
            self.db.collection('users').document(submission_data['submitter']['userId']).update({
                'stats.formsSubmitted': firestore.Increment(1)
            })

        return doc_ref.id

    async def get_submission_by_id(self, form_id: str, submission_id: str) -> Optional[Dict]:
        """Get a submission by ID"""
        doc = self.db.collection('forms').document(form_id) \
            .collection('submissions').document(submission_id).get()

        return doc.to_dict() if doc.exists else None

    async def get_submissions_for_form(self, form_id: str, limit: int = 100) -> List[Dict]:
        """Get all submissions for a form"""
        submissions = self.db.collection('forms').document(form_id) \
            .collection('submissions') \
            .order_by('submittedAt', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()

        return [{'id': s.id, **s.to_dict()} for s in submissions]

    async def get_submissions_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all submissions by a user (across all forms)"""
        submissions = self.db.collection_group('submissions') \
            .where(filter=FieldFilter('submitter.userId', '==', user_id)) \
            .order_by('submittedAt', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()

        results = []
        for submission in submissions:
            # Get form ID from path
            form_id = submission.reference.parent.parent.id
            results.append({
                'id': submission.id,
                'formId': form_id,
                **submission.to_dict()
            })
        return results

    async def update_submission_status(self, form_id: str, submission_id: str,
                                      status: str, notes: str = None) -> bool:
        """Update submission status"""
        try:
            update_data = {'status': status}
            if notes:
                update_data['processingNotes'] = notes
            if status == 'processed':
                update_data['processedAt'] = firestore.SERVER_TIMESTAMP

            self.db.collection('forms').document(form_id) \
                .collection('submissions').document(submission_id).update(update_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update submission status: {e}")
            return False

    async def get_submission_count(self, form_id: str) -> int:
        """Get submission count for a form"""
        # Use aggregation query
        submissions = self.db.collection('forms').document(form_id) \
            .collection('submissions').count().get()

        return submissions[0][0].value

    # =========================================================================
    # FORM ANALYTICS QUERIES
    # =========================================================================

    async def get_form_performance_metrics(self, creator_id: str) -> List[Dict]:
        """Get performance metrics for all forms by creator"""
        forms = await self.get_forms_by_creator(creator_id, limit=100)

        metrics = []
        for form in forms:
            form_id = form['id']

            # Get submission count from stats (denormalized)
            submission_count = form.get('stats', {}).get('submissionCount', 0)
            view_count = form.get('stats', {}).get('viewCount', 0)

            metrics.append({
                'formId': form_id,
                'title': form.get('title'),
                'viewCount': view_count,
                'submissionCount': submission_count,
                'conversionRate': (submission_count / view_count * 100) if view_count > 0 else 0,
                'createdAt': form.get('createdAt')
            })

        return sorted(metrics, key=lambda x: x['submissionCount'], reverse=True)

    async def get_submissions_by_date_range(self, form_id: str,
                                           start_date: datetime,
                                           end_date: datetime) -> List[Dict]:
        """Get submissions within date range"""
        submissions = self.db.collection('forms').document(form_id) \
            .collection('submissions') \
            .where(filter=FieldFilter('submittedAt', '>=', start_date)) \
            .where(filter=FieldFilter('submittedAt', '<=', end_date)) \
            .order_by('submittedAt', direction=firestore.Query.DESCENDING) \
            .stream()

        return [{'id': s.id, **s.to_dict()} for s in submissions]

    # =========================================================================
    # PROGRAM QUERIES
    # =========================================================================

    async def create_program(self, program_data: Dict) -> str:
        """Create a new program"""
        program_data['createdAt'] = firestore.SERVER_TIMESTAMP
        program_data['updatedAt'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('programs').document()
        program_data['programId'] = doc_ref.id
        doc_ref.set(program_data)

        return doc_ref.id

    async def get_program_by_id(self, program_id: str) -> Optional[Dict]:
        """Get program by ID"""
        doc = self.db.collection('programs').document(program_id).get()
        return doc.to_dict() if doc.exists else None

    async def get_programs_by_status(self, status: str, limit: int = 50) -> List[Dict]:
        """Get programs by status"""
        programs = self.db.collection('programs') \
            .where(filter=FieldFilter('status', '==', status)) \
            .order_by('startDate', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()

        return [{'id': p.id, **p.to_dict()} for p in programs]

    async def update_program(self, program_id: str, program_data: Dict) -> bool:
        """Update a program"""
        try:
            program_data['updatedAt'] = firestore.SERVER_TIMESTAMP
            self.db.collection('programs').document(program_id).update(program_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update program: {e}")
            return False

    # =========================================================================
    # PARTICIPANT QUERIES
    # =========================================================================

    async def create_participant(self, program_id: str, participant_data: Dict) -> str:
        """Create a new participant"""
        participant_data['registrationDate'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('programs').document(program_id) \
            .collection('participants').document()

        participant_data['participantId'] = doc_ref.id
        doc_ref.set(participant_data)

        # Update program stats
        self.db.collection('programs').document(program_id).update({
            'stats.totalParticipants': firestore.Increment(1)
        })

        return doc_ref.id

    async def get_participants_for_program(self, program_id: str) -> List[Dict]:
        """Get all participants for a program"""
        participants = self.db.collection('programs').document(program_id) \
            .collection('participants') \
            .order_by('registrationDate', direction=firestore.Query.DESCENDING) \
            .stream()

        return [{'id': p.id, **p.to_dict()} for p in participants]

    async def get_participant_by_email(self, program_id: str, email: str) -> Optional[Dict]:
        """Get participant by email"""
        participants = self.db.collection('programs').document(program_id) \
            .collection('participants') \
            .where(filter=FieldFilter('email', '==', email)) \
            .limit(1) \
            .stream()

        for participant in participants:
            return {'id': participant.id, **participant.to_dict()}
        return None

    # =========================================================================
    # REPORT QUERIES
    # =========================================================================

    async def create_report(self, report_data: Dict) -> str:
        """Create a new report"""
        report_data['createdAt'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('reports').document()
        report_data['reportId'] = doc_ref.id
        doc_ref.set(report_data)

        # Update user stats
        if report_data.get('createdBy', {}).get('userId'):
            self.db.collection('users').document(report_data['createdBy']['userId']).update({
                'stats.reportsGenerated': firestore.Increment(1)
            })

        return doc_ref.id

    async def get_report_by_id(self, report_id: str) -> Optional[Dict]:
        """Get report by ID"""
        doc = self.db.collection('reports').document(report_id).get()
        return doc.to_dict() if doc.exists else None

    async def get_reports_by_program(self, program_id: str) -> List[Dict]:
        """Get all reports for a program"""
        reports = self.db.collection('reports') \
            .where(filter=FieldFilter('programId', '==', program_id)) \
            .order_by('createdAt', direction=firestore.Query.DESCENDING) \
            .stream()

        return [{'id': r.id, **r.to_dict()} for r in reports]

    async def get_reports_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all reports created by a user"""
        reports = self.db.collection('reports') \
            .where(filter=FieldFilter('createdBy.userId', '==', user_id)) \
            .order_by('createdAt', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()

        return [{'id': r.id, **r.to_dict()} for r in reports]

    async def update_report_status(self, report_id: str, status: str,
                                   file_data: Dict = None) -> bool:
        """Update report generation status"""
        try:
            update_data = {'generationStatus': status}

            if status == 'completed' and file_data:
                update_data.update(file_data)
                update_data['generatedAt'] = firestore.SERVER_TIMESTAMP

            self.db.collection('reports').document(report_id).update(update_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update report status: {e}")
            return False

    async def increment_report_download_count(self, report_id: str) -> bool:
        """Increment report download count"""
        try:
            self.db.collection('reports').document(report_id).update({
                'downloadCount': firestore.Increment(1),
                'lastDownloaded': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Failed to increment download count: {e}")
            return False

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    async def batch_update_documents(self, updates: List[Dict]) -> bool:
        """
        Batch update multiple documents

        updates format: [
            {'collection': 'users', 'doc_id': '123', 'data': {...}},
            ...
        ]

        Note: Firestore has a limit of 500 operations per batch.
        If more than 500 updates are provided, this method will raise a ValueError.
        Consider calling this method multiple times for large datasets.

        Returns:
            bool: True if successful

        Raises:
            ValueError: If more than 500 updates are provided
        """
        if len(updates) > 500:
            logger.error(f"Batch update failed: {len(updates)} updates provided, but Firestore limit is 500")
            raise ValueError(
                f"Cannot batch update {len(updates)} documents. "
                f"Firestore limit is 500 operations per batch. "
                f"Please split your updates into multiple batches."
            )

        try:
            batch = self.db.batch()

            for update in updates:
                ref = self.db.collection(update['collection']).document(update['doc_id'])
                batch.update(ref, update['data'])

            batch.commit()
            logger.info(f"Successfully batch updated {len(updates)} documents")
            return True
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
            return False

    async def batch_delete_documents(self, collection: str, doc_ids: List[str]) -> bool:
        """
        Batch delete multiple documents

        Note: Firestore has a limit of 500 operations per batch.
        If more than 500 document IDs are provided, this method will raise a ValueError.
        Consider calling this method multiple times for large datasets.

        Args:
            collection: The collection name
            doc_ids: List of document IDs to delete

        Returns:
            bool: True if successful

        Raises:
            ValueError: If more than 500 document IDs are provided
        """
        if len(doc_ids) > 500:
            logger.error(f"Batch delete failed: {len(doc_ids)} documents provided, but Firestore limit is 500")
            raise ValueError(
                f"Cannot batch delete {len(doc_ids)} documents. "
                f"Firestore limit is 500 operations per batch. "
                f"Please split your deletes into multiple batches."
            )

        try:
            batch = self.db.batch()

            for doc_id in doc_ids:
                ref = self.db.collection(collection).document(doc_id)
                batch.delete(ref)

            batch.commit()
            logger.info(f"Successfully batch deleted {len(doc_ids)} documents from {collection}")
            return True
        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            return False


# =========================================================================
# REAL-TIME LISTENERS
# =========================================================================

class FirestoreRealtimeListeners:
    """Real-time listeners for Firestore collections"""

    def __init__(self, db: firestore.Client):
        self.db = db
        self.listeners = {}

    def listen_to_form_submissions(self, form_id: str, callback):
        """Listen to new form submissions in real-time"""
        def on_snapshot(col_snapshot, changes, read_time):
            for change in changes:
                if change.type.name == 'ADDED':
                    callback({'id': change.document.id, **change.document.to_dict()})

        query = self.db.collection('forms').document(form_id) \
            .collection('submissions') \
            .order_by('submittedAt', direction=firestore.Query.DESCENDING)

        listener = query.on_snapshot(on_snapshot)
        self.listeners[f'form_submissions_{form_id}'] = listener
        return listener

    def listen_to_user_sessions(self, user_id: str, callback):
        """Listen to user session changes in real-time"""
        def on_snapshot(col_snapshot, changes, read_time):
            for change in changes:
                callback({
                    'type': change.type.name,
                    'data': {'id': change.document.id, **change.document.to_dict()}
                })

        query = self.db.collection('users').document(user_id) \
            .collection('sessions') \
            .where(filter=FieldFilter('isActive', '==', True))

        listener = query.on_snapshot(on_snapshot)
        self.listeners[f'user_sessions_{user_id}'] = listener
        return listener

    def stop_listener(self, listener_key: str):
        """Stop a specific listener"""
        if listener_key in self.listeners:
            self.listeners[listener_key].unsubscribe()
            del self.listeners[listener_key]

    def stop_all_listeners(self):
        """Stop all active listeners"""
        for listener in self.listeners.values():
            listener.unsubscribe()
        self.listeners.clear()
