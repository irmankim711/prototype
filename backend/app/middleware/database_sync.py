"""
Database Schema Validator & Synchronization
Ensures Firestore and SQLAlchemy databases maintain consistent user schemas
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import inspect

from .. import db
from ..models.production.user_models import User
from .firebase_auth import firebase_auth_manager

logger = logging.getLogger(__name__)


class DatabaseSchemaValidator:
    """
    Validates and synchronizes user data between Firestore and SQLAlchemy.

    Critical for preventing data inconsistencies that could lead to authorization bypass.
    """

    def __init__(self):
        self.inconsistencies_found = []
        self.auto_fix_enabled = True

    def validate_user_schemas(self) -> Dict[str, Any]:
        """
        Validate user schema consistency between Firestore and SQLAlchemy.

        Returns:
            Dict with validation results and any inconsistencies found
        """
        logger.info("🔍 Starting database schema validation...")

        validation_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'firestore_available': firebase_auth_manager._firestore_db is not None,
            'sqlalchemy_available': True,
            'total_mismatches': 0,
            'critical_mismatches': 0,
            'mismatches': [],
            'validation_passed': True
        }

        if not firebase_auth_manager._firestore_db:
            logger.warning("⚠️ Firestore not available - skipping cross-database validation")
            return validation_result

        try:
            # Get users from both databases
            firestore_users = self._get_firestore_users()
            sql_users = self._get_sqlalchemy_users()

            logger.info(f"📊 Found {len(firestore_users)} Firestore users, {len(sql_users)} SQL users")

            # Find schema mismatches
            mismatches = self._find_schema_mismatches(firestore_users, sql_users)

            validation_result['total_mismatches'] = len(mismatches)
            validation_result['mismatches'] = mismatches
            validation_result['critical_mismatches'] = len([m for m in mismatches if m['severity'] == 'critical'])
            validation_result['validation_passed'] = len(mismatches) == 0

            if mismatches:
                logger.critical(f"❌ SCHEMA MISMATCH DETECTED: {len(mismatches)} inconsistencies found")

                # Log critical mismatches
                for mismatch in mismatches:
                    if mismatch['severity'] == 'critical':
                        logger.critical(f"🔴 {mismatch['type']}: {mismatch['description']}")

                # Auto-fix if enabled
                if self.auto_fix_enabled:
                    self._auto_fix_schema_mismatches(mismatches)
            else:
                logger.info("✅ Schema validation passed - no inconsistencies found")

            return validation_result

        except Exception as e:
            logger.error(f"❌ Schema validation failed: {str(e)}")
            validation_result['validation_passed'] = False
            validation_result['error'] = str(e)
            return validation_result

    def _get_firestore_users(self) -> Dict[str, Dict[str, Any]]:
        """Get all active users from Firestore"""
        users = {}

        try:
            users_ref = firebase_auth_manager._firestore_db.collection('users')
            query = users_ref.where('isActive', '==', True)

            for doc in query.stream():
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                firebase_uid = user_data.get('firebaseUid')

                if firebase_uid:
                    users[firebase_uid] = user_data

            logger.debug(f"📊 Retrieved {len(users)} users from Firestore")
            return users

        except Exception as e:
            logger.error(f"❌ Failed to retrieve Firestore users: {str(e)}")
            return {}

    def _get_sqlalchemy_users(self) -> Dict[str, User]:
        """Get all active users from SQLAlchemy"""
        users = {}

        try:
            sql_users = User.query.filter_by(is_active=True).all()

            for user in sql_users:
                if user.firebase_uid:
                    users[user.firebase_uid] = user

            logger.debug(f"📊 Retrieved {len(users)} users from SQLAlchemy")
            return users

        except Exception as e:
            logger.error(f"❌ Failed to retrieve SQLAlchemy users: {str(e)}")
            return {}

    def _find_schema_mismatches(self, firestore_users: Dict, sql_users: Dict) -> List[Dict[str, Any]]:
        """
        Find mismatches between Firestore and SQLAlchemy user data.

        Critical mismatches:
        - User exists in one database but not the other
        - Email mismatch (could allow unauthorized access)
        - Active status mismatch

        Warning mismatches:
        - Name differences
        - Profile data differences
        """
        mismatches = []

        # Check for users in Firestore but not SQL
        for firebase_uid, firestore_user in firestore_users.items():
            if firebase_uid not in sql_users:
                mismatches.append({
                    'type': 'MISSING_IN_SQL',
                    'severity': 'critical',
                    'firebase_uid': firebase_uid,
                    'email': firestore_user.get('email'),
                    'description': f"User {firestore_user.get('email')} exists in Firestore but not in SQL database",
                    'firestore_data': firestore_user,
                    'sql_data': None
                })

        # Check for users in SQL but not Firestore
        for firebase_uid, sql_user in sql_users.items():
            if firebase_uid not in firestore_users:
                mismatches.append({
                    'type': 'MISSING_IN_FIRESTORE',
                    'severity': 'critical',
                    'firebase_uid': firebase_uid,
                    'email': sql_user.email,
                    'description': f"User {sql_user.email} exists in SQL but not in Firestore database",
                    'firestore_data': None,
                    'sql_data': self._user_to_dict(sql_user)
                })

        # Check for data inconsistencies in users present in both
        for firebase_uid in set(firestore_users.keys()) & set(sql_users.keys()):
            firestore_user = firestore_users[firebase_uid]
            sql_user = sql_users[firebase_uid]

            # Check email mismatch (CRITICAL)
            if firestore_user.get('email') != sql_user.email:
                mismatches.append({
                    'type': 'EMAIL_MISMATCH',
                    'severity': 'critical',
                    'firebase_uid': firebase_uid,
                    'description': f"Email mismatch for user {firebase_uid}",
                    'firestore_email': firestore_user.get('email'),
                    'sql_email': sql_user.email
                })

            # Check active status mismatch (CRITICAL)
            if firestore_user.get('isActive', True) != sql_user.is_active:
                mismatches.append({
                    'type': 'ACTIVE_STATUS_MISMATCH',
                    'severity': 'critical',
                    'firebase_uid': firebase_uid,
                    'email': sql_user.email,
                    'description': f"Active status mismatch for user {sql_user.email}",
                    'firestore_active': firestore_user.get('isActive'),
                    'sql_active': sql_user.is_active
                })

            # Check name mismatches (WARNING)
            profile = firestore_user.get('profile', {})
            if profile.get('firstName') != sql_user.first_name:
                mismatches.append({
                    'type': 'NAME_MISMATCH',
                    'severity': 'warning',
                    'firebase_uid': firebase_uid,
                    'email': sql_user.email,
                    'description': f"First name mismatch for user {sql_user.email}",
                    'firestore_first_name': profile.get('firstName'),
                    'sql_first_name': sql_user.first_name
                })

        return mismatches

    def _auto_fix_schema_mismatches(self, mismatches: List[Dict[str, Any]]):
        """
        Automatically fix schema mismatches where possible.

        Strategy:
        - For MISSING_IN_SQL: Create SQL user from Firestore data
        - For MISSING_IN_FIRESTORE: Create Firestore user from SQL data
        - For EMAIL_MISMATCH: Use Firestore as source of truth (it's from Firebase Auth)
        - For ACTIVE_STATUS_MISMATCH: Sync to match stricter policy (if inactive in either, make inactive in both)
        """
        logger.info(f"🔧 Auto-fixing {len(mismatches)} schema mismatches...")

        fixed_count = 0
        failed_count = 0

        for mismatch in mismatches:
            try:
                if mismatch['type'] == 'MISSING_IN_SQL':
                    self._create_sql_user_from_firestore(mismatch['firestore_data'])
                    fixed_count += 1

                elif mismatch['type'] == 'MISSING_IN_FIRESTORE':
                    self._create_firestore_user_from_sql(mismatch['sql_data'])
                    fixed_count += 1

                elif mismatch['type'] == 'EMAIL_MISMATCH':
                    self._sync_email_from_firestore(mismatch)
                    fixed_count += 1

                elif mismatch['type'] == 'ACTIVE_STATUS_MISMATCH':
                    self._sync_active_status(mismatch)
                    fixed_count += 1

                elif mismatch['type'] == 'NAME_MISMATCH':
                    self._sync_name_from_firestore(mismatch)
                    fixed_count += 1

            except Exception as e:
                logger.error(f"❌ Failed to fix mismatch {mismatch['type']}: {str(e)}")
                failed_count += 1

        logger.info(f"✅ Auto-fix complete: {fixed_count} fixed, {failed_count} failed")

    def _create_sql_user_from_firestore(self, firestore_data: Dict[str, Any]):
        """Create SQLAlchemy user from Firestore data"""
        logger.info(f"Creating SQL user for {firestore_data.get('email')}")

        profile = firestore_data.get('profile', {})

        user = User(
            firebase_uid=firestore_data.get('firebaseUid'),
            email=firestore_data.get('email'),
            username=firestore_data.get('email', '').split('@')[0],
            first_name=profile.get('firstName', ''),
            last_name=profile.get('lastName', ''),
            avatar_url=profile.get('photoURL', ''),
            is_active=firestore_data.get('isActive', True),
            is_verified=firestore_data.get('isVerified', False),
            last_login=datetime.utcnow()
        )

        db.session.add(user)
        db.session.commit()

        logger.info(f"✅ Created SQL user {user.id} for {user.email}")

    def _create_firestore_user_from_sql(self, sql_data: Dict[str, Any]):
        """Create Firestore user from SQL data"""
        logger.info(f"Creating Firestore user for {sql_data.get('email')}")

        users_ref = firebase_auth_manager._firestore_db.collection('users')

        user_data = {
            'firebaseUid': sql_data['firebase_uid'],
            'email': sql_data['email'],
            'profile': {
                'firstName': sql_data.get('first_name', ''),
                'lastName': sql_data.get('last_name', ''),
                'displayName': f"{sql_data.get('first_name', '')} {sql_data.get('last_name', '')}".strip(),
                'photoURL': sql_data.get('avatar_url', ''),
                'phoneNumber': '',
            },
            'role': 'user',
            'isActive': sql_data.get('is_active', True),
            'isVerified': sql_data.get('is_verified', False),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'lastLogin': datetime.utcnow(),
        }

        doc_ref = users_ref.document()
        doc_ref.set(user_data)

        logger.info(f"✅ Created Firestore user {doc_ref.id} for {sql_data['email']}")

    def _sync_email_from_firestore(self, mismatch: Dict[str, Any]):
        """Sync email from Firestore to SQL (Firestore is source of truth from Firebase Auth)"""
        firebase_uid = mismatch['firebase_uid']
        correct_email = mismatch['firestore_email']

        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if user:
            user.email = correct_email
            db.session.commit()
            logger.info(f"✅ Synced email to {correct_email} for user {firebase_uid}")

    def _sync_active_status(self, mismatch: Dict[str, Any]):
        """Sync active status - if inactive in either, make inactive in both"""
        firebase_uid = mismatch['firebase_uid']
        firestore_active = mismatch.get('firestore_active', True)
        sql_active = mismatch.get('sql_active', True)

        # Use stricter policy - if inactive in either, make inactive in both
        should_be_active = firestore_active and sql_active

        # Update SQL
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if user:
            user.is_active = should_be_active
            db.session.commit()

        # Update Firestore
        users_ref = firebase_auth_manager._firestore_db.collection('users')
        query = users_ref.where('firebaseUid', '==', firebase_uid).limit(1)
        docs = list(query.stream())

        if docs:
            docs[0].reference.update({'isActive': should_be_active})

        logger.info(f"✅ Synced active status to {should_be_active} for user {firebase_uid}")

    def _sync_name_from_firestore(self, mismatch: Dict[str, Any]):
        """Sync name from Firestore to SQL"""
        firebase_uid = mismatch['firebase_uid']
        correct_first_name = mismatch.get('firestore_first_name', '')

        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if user and correct_first_name:
            user.first_name = correct_first_name
            db.session.commit()
            logger.info(f"✅ Synced name for user {firebase_uid}")

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert SQLAlchemy User to dict"""
        return {
            'id': user.id,
            'firebase_uid': user.firebase_uid,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar_url': user.avatar_url,
            'is_active': user.is_active,
            'is_verified': user.is_verified
        }


# Global instance
database_validator = DatabaseSchemaValidator()


def validate_database_schemas() -> Dict[str, Any]:
    """
    Convenience function to validate database schemas.
    Can be called from health check endpoints.
    """
    return database_validator.validate_user_schemas()
