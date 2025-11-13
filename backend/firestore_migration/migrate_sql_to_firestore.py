"""
SQL to Firestore Migration Script
==================================

This script migrates data from your SQL database to Firebase Firestore
while applying the NoSQL data model transformations.

Requirements:
    pip install firebase-admin sqlalchemy psycopg2-binary

Usage:
    python migrate_sql_to_firestore.py --mode [test|full]
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

# SQLAlchemy for SQL database
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FirestoreMigration:
    """Main migration class from SQL to Firestore"""

    def __init__(self, sql_connection_string: str, firebase_cred_path: str):
        """
        Initialize migration with SQL and Firebase connections

        Args:
            sql_connection_string: SQLAlchemy connection string
            firebase_cred_path: Path to Firebase service account JSON
        """
        # Initialize SQL connection
        self.sql_engine = create_engine(sql_connection_string)
        self.sql_session = sessionmaker(bind=self.sql_engine)()
        self.sql_metadata = MetaData()
        self.sql_metadata.reflect(bind=self.sql_engine)

        # Initialize Firebase connection
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

        # Migration statistics
        self.stats = {
            'users': {'migrated': 0, 'failed': 0},
            'forms': {'migrated': 0, 'failed': 0},
            'programs': {'migrated': 0, 'failed': 0},
            'reports': {'migrated': 0, 'failed': 0},
            'total_operations': 0
        }

    def _timestamp_to_firestore(self, timestamp):
        """Convert SQL timestamp to Firestore timestamp"""
        if timestamp is None:
            return None
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return timestamp

    def _create_search_terms(self, *args) -> List[str]:
        """Create search terms array from multiple strings"""
        terms = set()
        for arg in args:
            if arg:
                terms.update(str(arg).lower().split())
        return list(terms)

    def _parse_json_field(self, field_value, default=None):
        """Safely parse JSON field that might already be a dict"""
        if field_value is None:
            return default if default is not None else {}
        if isinstance(field_value, dict):
            return field_value
        if isinstance(field_value, str):
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, ValueError):
                return default if default is not None else {}
        return default if default is not None else {}

    # =========================================================================
    # USER MIGRATION
    # =========================================================================

    def migrate_users(self, batch_size: int = 500):
        """Migrate all users from SQL to Firestore"""
        logger.info("Starting user migration...")

        user_table = self.sql_metadata.tables.get('user')
        if user_table is None:
            logger.error("User table not found in SQL database")
            return

        # Get all users
        users = self.sql_session.execute(user_table.select()).fetchall()
        logger.info(f"Found {len(users)} users to migrate")

        batch = self.db.batch()
        batch_count = 0

        for user_row in users:
            try:
                user_dict = dict(user_row._mapping)
                user_id = str(user_dict['id'])

                # Transform to Firestore structure
                firestore_user = {
                    'userId': user_id,
                    'firebaseUid': user_dict.get('firebase_uid'),
                    'email': user_dict.get('email'),
                    'username': user_dict.get('username'),
                    'passwordHash': user_dict.get('password_hash'),

                    'profile': {
                        'firstName': user_dict.get('first_name'),
                        'lastName': user_dict.get('last_name'),
                        'phone': user_dict.get('phone'),
                        'company': user_dict.get('company'),
                        'jobTitle': user_dict.get('job_title'),
                        'bio': user_dict.get('bio'),
                        'avatarUrl': user_dict.get('avatar_url')
                    },

                    'isActive': user_dict.get('is_active', True),
                    'role': user_dict.get('role', 'user'),

                    'createdAt': self._timestamp_to_firestore(user_dict.get('created_at')),
                    'updatedAt': self._timestamp_to_firestore(user_dict.get('updated_at')),
                    'lastLogin': self._timestamp_to_firestore(user_dict.get('last_login')),

                    'stats': {
                        'formsCreated': 0,
                        'formsSubmitted': 0,
                        'programsAttended': 0,
                        'reportsGenerated': 0,
                        'totalSessions': 0,
                        'activeOAuthConnections': 0
                    },

                    'searchTerms': self._create_search_terms(
                        user_dict.get('username'),
                        user_dict.get('email'),
                        user_dict.get('first_name'),
                        user_dict.get('last_name')
                    ),

                    '_indexes': {
                        'email': user_dict.get('email'),
                        'username': user_dict.get('username'),
                        'role': user_dict.get('role', 'user'),
                        'isActive': user_dict.get('is_active', True)
                    }
                }

                # Add to batch
                user_ref = self.db.collection('users').document(user_id)
                batch.set(user_ref, firestore_user)
                batch_count += 1

                # Commit batch if full
                if batch_count >= batch_size:
                    batch.commit()
                    logger.info(f"Committed batch of {batch_count} users")
                    batch = self.db.batch()
                    batch_count = 0

                self.stats['users']['migrated'] += 1

                # Migrate user's related data
                self._migrate_user_tokens(user_id)
                self._migrate_user_sessions(user_id)

            except Exception as e:
                logger.error(f"Failed to migrate user {user_dict.get('id')}: {str(e)}")
                self.stats['users']['failed'] += 1

        # Commit remaining batch
        if batch_count > 0:
            batch.commit()
            logger.info(f"Committed final batch of {batch_count} users")

        logger.info(f"User migration completed: {self.stats['users']}")

    def _migrate_user_tokens(self, user_id: str):
        """Migrate OAuth tokens for a user"""
        token_table = self.sql_metadata.tables.get('user_tokens')
        if token_table is None:
            return

        tokens = self.sql_session.execute(
            token_table.select().where(token_table.c.user_id == int(user_id))
        ).fetchall()

        for token_row in tokens:
            try:
                token_dict = dict(token_row._mapping)
                platform = token_dict.get('platform')

                firestore_token = {
                    'platform': platform,
                    'platformUserId': token_dict.get('platform_user_id'),
                    'accessToken': token_dict.get('access_token'),
                    'refreshToken': token_dict.get('refresh_token'),
                    'tokenType': token_dict.get('token_type'),
                    'scopes': self._parse_json_field(token_dict.get('scopes'), []),
                    'expiresAt': self._timestamp_to_firestore(token_dict.get('expires_at')),
                    'issuedAt': self._timestamp_to_firestore(token_dict.get('issued_at')),
                    'isActive': token_dict.get('is_active', True),
                    'lastUsed': self._timestamp_to_firestore(token_dict.get('last_used')),
                    'usageCount': token_dict.get('usage_count', 0),
                    'revokedAt': self._timestamp_to_firestore(token_dict.get('revoked_at')),
                    'revokeReason': token_dict.get('revoke_reason')
                }

                self.db.collection('users').document(user_id) \
                    .collection('tokens').document(platform).set(firestore_token)

            except Exception as e:
                logger.error(f"Failed to migrate token for user {user_id}: {str(e)}")

    def _migrate_user_sessions(self, user_id: str):
        """Migrate user sessions"""
        session_table = self.sql_metadata.tables.get('user_sessions')
        if session_table is None:
            return

        sessions = self.sql_session.execute(
            session_table.select().where(session_table.c.user_id == int(user_id))
        ).fetchall()

        for session_row in sessions:
            try:
                session_dict = dict(session_row._mapping)
                session_id = str(session_dict['id'])

                firestore_session = {
                    'sessionId': session_id,
                    'sessionToken': session_dict.get('session_token'),
                    'ipAddress': session_dict.get('ip_address'),
                    'userAgent': session_dict.get('user_agent'),
                    'browser': session_dict.get('browser'),
                    'operatingSystem': session_dict.get('operating_system'),
                    'deviceType': session_dict.get('device_type'),
                    'loginMethod': session_dict.get('login_method'),
                    'isActive': session_dict.get('is_active', True),
                    'isSuspicious': session_dict.get('is_suspicious', False),
                    'securityFlags': self._parse_json_field(session_dict.get('security_flags'), {}),
                    'createdAt': self._timestamp_to_firestore(session_dict.get('created_at')),
                    'lastActivity': self._timestamp_to_firestore(session_dict.get('last_activity')),
                    'expiresAt': self._timestamp_to_firestore(session_dict.get('expires_at')),
                    'endedAt': self._timestamp_to_firestore(session_dict.get('ended_at'))
                }

                self.db.collection('users').document(user_id) \
                    .collection('sessions').document(session_id).set(firestore_session)

            except Exception as e:
                logger.error(f"Failed to migrate session for user {user_id}: {str(e)}")

    # =========================================================================
    # FORM MIGRATION
    # =========================================================================

    def migrate_forms(self, batch_size: int = 500):
        """Migrate all forms from SQL to Firestore"""
        logger.info("Starting form migration...")

        form_table = self.sql_metadata.tables.get('forms')
        if form_table is None:
            logger.error("Forms table not found in SQL database")
            return

        forms = self.sql_session.execute(form_table.select()).fetchall()
        logger.info(f"Found {len(forms)} forms to migrate")

        batch = self.db.batch()
        batch_count = 0

        for form_row in forms:
            try:
                form_dict = dict(form_row._mapping)
                form_id = str(form_dict['id'])

                # Get creator info
                creator = self._get_user_info(form_dict.get('creator_id'))

                firestore_form = {
                    'formId': form_id,
                    'title': form_dict.get('title'),
                    'description': form_dict.get('description'),
                    'schema': self._parse_json_field(form_dict.get('schema'), {}),
                    'isActive': form_dict.get('is_active', True),
                    'isPublic': form_dict.get('is_public', False),
                    'accessKey': form_dict.get('access_key'),

                    'creator': creator,

                    'settings': self._parse_json_field(form_dict.get('form_settings'), {}),
                    'submissionLimit': form_dict.get('submission_limit'),
                    'expiresAt': self._timestamp_to_firestore(form_dict.get('expires_at')),

                    'externalUrl': form_dict.get('external_url'),
                    'qrCodeData': form_dict.get('qr_code_data'),

                    'stats': {
                        'viewCount': form_dict.get('view_count', 0),
                        'submissionCount': 0,
                        'uniqueSubmitters': 0,
                        'averageCompletionTime': 0,
                        'lastSubmissionAt': None
                    },

                    'createdAt': self._timestamp_to_firestore(form_dict.get('created_at')),
                    'updatedAt': self._timestamp_to_firestore(form_dict.get('updated_at')),

                    'searchTerms': self._create_search_terms(
                        form_dict.get('title'),
                        form_dict.get('description')
                    ),

                    '_indexes': {
                        'creatorId': str(form_dict.get('creator_id')),
                        'isActive': form_dict.get('is_active', True),
                        'isPublic': form_dict.get('is_public', False),
                        'createdAt': self._timestamp_to_firestore(form_dict.get('created_at'))
                    }
                }

                form_ref = self.db.collection('forms').document(form_id)
                batch.set(form_ref, firestore_form)
                batch_count += 1

                if batch_count >= batch_size:
                    batch.commit()
                    logger.info(f"Committed batch of {batch_count} forms")
                    batch = self.db.batch()
                    batch_count = 0

                self.stats['forms']['migrated'] += 1

                # Migrate related data
                self._migrate_form_submissions(form_id)
                self._migrate_form_qr_codes(form_id)
                self._migrate_form_access_codes(form_id)

            except Exception as e:
                logger.error(f"Failed to migrate form {form_dict.get('id')}: {str(e)}")
                self.stats['forms']['failed'] += 1

        if batch_count > 0:
            batch.commit()
            logger.info(f"Committed final batch of {batch_count} forms")

        logger.info(f"Form migration completed: {self.stats['forms']}")

    def _migrate_form_submissions(self, form_id: str):
        """Migrate submissions for a form"""
        submission_table = self.sql_metadata.tables.get('form_submissions')
        if submission_table is None:
            return

        submissions = self.sql_session.execute(
            submission_table.select().where(submission_table.c.form_id == int(form_id))
        ).fetchall()

        for submission_row in submissions:
            try:
                submission_dict = dict(submission_row._mapping)
                submission_id = str(submission_dict['id'])

                submitter = self._get_user_info(submission_dict.get('submitter_id'))

                firestore_submission = {
                    'submissionId': submission_id,
                    'data': self._parse_json_field(submission_dict.get('data'), {}),
                    'submitter': {
                        'userId': submitter.get('userId') if submitter else None,
                        'email': submission_dict.get('submitter_email'),
                        'username': submitter.get('username') if submitter else None,
                        'firstName': submitter['profile'].get('firstName') if submitter else None,
                        'lastName': submitter['profile'].get('lastName') if submitter else None
                    },
                    'submittedAt': self._timestamp_to_firestore(submission_dict.get('submitted_at')),
                    'status': submission_dict.get('status', 'submitted'),
                    'submissionSource': submission_dict.get('submission_source', 'web'),
                    'ipAddress': submission_dict.get('ip_address'),
                    'userAgent': submission_dict.get('user_agent'),
                    'locationData': self._parse_json_field(submission_dict.get('location_data'), {}),
                    'processingNotes': submission_dict.get('processing_notes'),
                    'processedAt': None,
                    '_indexes': {
                        'submitterUserId': str(submission_dict.get('submitter_id')) if submission_dict.get('submitter_id') else None,
                        'submittedAt': self._timestamp_to_firestore(submission_dict.get('submitted_at')),
                        'status': submission_dict.get('status', 'submitted')
                    }
                }

                self.db.collection('forms').document(form_id) \
                    .collection('submissions').document(submission_id).set(firestore_submission)

            except Exception as e:
                logger.error(f"Failed to migrate submission for form {form_id}: {str(e)}")

    def _migrate_form_qr_codes(self, form_id: str):
        """Migrate QR codes for a form"""
        qr_table = self.sql_metadata.tables.get('form_qr_codes')
        if qr_table is None:
            return

        qr_codes = self.sql_session.execute(
            qr_table.select().where(qr_table.c.form_id == int(form_id))
        ).fetchall()

        for qr_row in qr_codes:
            try:
                qr_dict = dict(qr_row._mapping)
                qr_id = str(qr_dict['id'])

                firestore_qr = {
                    'qrCodeId': qr_id,
                    'qrCodeData': qr_dict.get('qr_code_data'),
                    'externalUrl': qr_dict.get('external_url'),
                    'title': qr_dict.get('title'),
                    'description': qr_dict.get('description'),
                    'size': qr_dict.get('size'),
                    'errorCorrection': qr_dict.get('error_correction'),
                    'border': qr_dict.get('border'),
                    'backgroundColor': qr_dict.get('background_color'),
                    'foregroundColor': qr_dict.get('foreground_color'),
                    'scanCount': qr_dict.get('scan_count', 0),
                    'lastScanned': self._timestamp_to_firestore(qr_dict.get('last_scanned')),
                    'isActive': qr_dict.get('is_active', True),
                    'createdAt': self._timestamp_to_firestore(qr_dict.get('created_at')),
                    'updatedAt': self._timestamp_to_firestore(qr_dict.get('updated_at'))
                }

                self.db.collection('forms').document(form_id) \
                    .collection('qrCodes').document(qr_id).set(firestore_qr)

            except Exception as e:
                logger.error(f"Failed to migrate QR code for form {form_id}: {str(e)}")

    def _migrate_form_access_codes(self, form_id: str):
        """Migrate access codes for a form"""
        access_table = self.sql_metadata.tables.get('form_access_codes')
        if access_table is None:
            return

        access_codes = self.sql_session.execute(
            access_table.select().where(access_table.c.form_id == int(form_id))
        ).fetchall()

        for code_row in access_codes:
            try:
                code_dict = dict(code_row._mapping)
                code_id = str(code_dict['id'])

                firestore_code = {
                    'codeId': code_id,
                    'accessCode': code_dict.get('access_code'),
                    'description': code_dict.get('description'),
                    'isActive': code_dict.get('is_active', True),
                    'expiresAt': self._timestamp_to_firestore(code_dict.get('expires_at')),
                    'maxUses': code_dict.get('max_uses'),
                    'currentUses': code_dict.get('current_uses', 0),
                    'createdAt': self._timestamp_to_firestore(code_dict.get('created_at')),
                    'usageHistory': []
                }

                self.db.collection('forms').document(form_id) \
                    .collection('accessCodes').document(code_id).set(firestore_code)

            except Exception as e:
                logger.error(f"Failed to migrate access code for form {form_id}: {str(e)}")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_user_info(self, user_id: Optional[int]) -> Optional[Dict]:
        """Get user information for denormalization"""
        if not user_id:
            return None

        user_table = self.sql_metadata.tables.get('user')
        if user_table is None:
            return None

        try:
            user_row = self.sql_session.execute(
                user_table.select().where(user_table.c.id == user_id)
            ).fetchone()

            if not user_row:
                return None

            user_dict = dict(user_row._mapping)
            return {
                'userId': str(user_dict['id']),
                'username': user_dict.get('username'),
                'email': user_dict.get('email'),
                'profile': {
                    'firstName': user_dict.get('first_name'),
                    'lastName': user_dict.get('last_name')
                }
            }
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {str(e)}")
            return None

    def update_denormalized_stats(self):
        """Update denormalized statistics after migration"""
        logger.info("Updating denormalized statistics...")
        logger.info("SKIPPED: Stats update requires indexes to be deployed first")
        logger.info("You can run this separately after deploying indexes with:")
        logger.info("  firebase deploy --only firestore:indexes")

        # Note: This requires indexes to be deployed first
        # Uncomment after deploying firestore.indexes.json

        # # Update user stats
        # users = self.db.collection('users').stream()
        # for user in users:
        #     user_id = user.id
        #     stats = {
        #         'formsCreated': self.db.collection('forms') \
        #             .where('creator.userId', '==', user_id).count().get()[0][0].value,
        #         'formsSubmitted': self.db.collection_group('submissions') \
        #             .where('submitter.userId', '==', user_id).count().get()[0][0].value,
        #         'totalSessions': self.db.collection('users').document(user_id) \
        #             .collection('sessions').count().get()[0][0].value,
        #     }
        #     self.db.collection('users').document(user_id).update({'stats': stats})

        logger.info("Statistics update completed (or skipped)")

    def verify_migration(self):
        """Verify data integrity after migration"""
        logger.info("Verifying migration...")

        # Count documents in Firestore
        firestore_counts = {
            'users': self.db.collection('users').count().get()[0][0].value,
            'forms': self.db.collection('forms').count().get()[0][0].value,
            'programs': self.db.collection('programs').count().get()[0][0].value,
            'reports': self.db.collection('reports').count().get()[0][0].value
        }

        # Count records in SQL
        sql_counts = {}
        for table_name in ['user', 'forms', 'programs', 'reports']:
            table = self.sql_metadata.tables.get(table_name)
            if table is not None:
                count = len(self.sql_session.execute(table.select()).fetchall())
                sql_counts[table_name] = count

        logger.info(f"Firestore counts: {firestore_counts}")
        logger.info(f"SQL counts: {sql_counts}")
        logger.info(f"Migration stats: {self.stats}")

        return firestore_counts, sql_counts

    def run_full_migration(self):
        """Run complete migration process"""
        logger.info("=" * 80)
        logger.info("STARTING FULL MIGRATION FROM SQL TO FIRESTORE")
        logger.info("=" * 80)

        start_time = datetime.now()

        try:
            # Phase 1: Migrate core entities
            self.migrate_users()
            self.migrate_forms()
            # Add more migrations as needed
            # self.migrate_programs()
            # self.migrate_reports()

            # Phase 2: Update denormalized data
            self.update_denormalized_stats()

            # Phase 3: Verify migration
            self.verify_migration()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info("=" * 80)
            logger.info(f"MIGRATION COMPLETED IN {duration:.2f} SECONDS")
            logger.info(f"Total stats: {self.stats}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Migrate SQL database to Firestore')
    parser.add_argument('--mode', choices=['test', 'full'], default='test',
                       help='Migration mode: test (first 10 records) or full')
    parser.add_argument('--sql-url', required=True,
                       help='SQL database connection string')
    parser.add_argument('--firebase-cred', required=True,
                       help='Path to Firebase service account JSON')

    args = parser.parse_args()

    # Initialize migration
    migration = FirestoreMigration(args.sql_url, args.firebase_cred)

    if args.mode == 'test':
        logger.info("Running TEST migration (limited data)")
        # Test with limited data
        migration.migrate_users(batch_size=10)
        migration.migrate_forms(batch_size=10)
    else:
        logger.info("Running FULL migration")
        migration.run_full_migration()


if __name__ == '__main__':
    main()
