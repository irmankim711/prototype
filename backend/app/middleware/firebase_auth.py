"""
Firebase Authentication Middleware
Handles Firebase token verification and user management
"""

import os
import json
import logging
import traceback
import time
from typing import Optional, Dict, Any, List
from functools import wraps
from datetime import datetime
from pathlib import Path

from flask import request, jsonify, g, current_app
import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models.production.user_models import User
from ..models.production.permissions import UserRole

logger = logging.getLogger(__name__)

class FirebaseAuthManager:
    """Firebase Authentication Manager with robust initialization and error handling"""
    
    def __init__(self, skip_startup_retry=True):
        self._initialized = False
        self._initialization_error = None
        self._initialization_attempts = 0
        self._max_attempts = 3
        self._app = None
        self._firestore_db = None  # Firestore client
        self._skip_startup_retry = skip_startup_retry  # Skip retries during initial load

        # Circuit breaker pattern variables
        self._circuit_breaker_open = False
        self._circuit_breaker_failures = 0
        self._circuit_breaker_failure_threshold = 5
        self._circuit_breaker_reset_timeout = 300  # 5 minutes
        self._circuit_breaker_last_failure_time = None

        # Initialization status tracking
        self._initialization_history = []
        self._last_successful_init = None
        self._consecutive_failures = 0

        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with comprehensive error handling, retry logic, and circuit breaker"""
        if self._initialized:
            return True
        
        # Check circuit breaker status
        if self._is_circuit_breaker_open():
            logger.warning(f"⚡ Circuit breaker is open - skipping Firebase initialization attempt")
            return False
            
        self._initialization_attempts += 1
        attempt_start_time = datetime.utcnow()
        logger.info(f"🔄 Firebase initialization attempt {self._initialization_attempts}/{self._max_attempts}")
        
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logger.info("✅ Firebase Admin SDK already initialized")
                self._initialized = True
                self._app = firebase_admin.get_app()
                self._record_successful_initialization(attempt_start_time)
                return True
            
            # Method 1: Initialize from service account key file (preferred)
            if self._try_service_account_file():
                self._record_successful_initialization(attempt_start_time)
                return True
            
            # Method 2: Initialize from environment variables (fallback)
            if self._try_environment_variables():
                self._record_successful_initialization(attempt_start_time)
                return True
            
            # If we get here, no valid configuration was found
            error_msg = "No valid Firebase configuration found"
            logger.error(f"❌ {error_msg}")
            self._log_configuration_status()
            self._initialization_error = error_msg
            self._record_failed_initialization(attempt_start_time, error_msg)

            # Skip retries during startup to allow app to start quickly
            if self._skip_startup_retry:
                logger.warning("⚠️ Skipping retry during startup - app will start without Firebase")
                self._initialization_attempts = 0  # Reset for later retry attempts
                return False

            # Retry logic for transient failures (only when not during startup)
            if self._initialization_attempts < self._max_attempts:
                retry_delay = 2 ** self._initialization_attempts  # Exponential backoff
                logger.info(f"🔄 Retrying Firebase initialization in {retry_delay} seconds...")
                time.sleep(retry_delay)
                return self._initialize_firebase()

            # Max attempts reached - trigger circuit breaker
            self._trigger_circuit_breaker()
            return False
                
        except Exception as e:
            error_msg = f"Firebase initialization failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            self._initialization_error = error_msg
            self._record_failed_initialization(attempt_start_time, error_msg)

            # Skip retries during startup to allow app to start quickly
            if self._skip_startup_retry:
                logger.warning("⚠️ Skipping retry during startup - app will start without Firebase")
                self._initialization_attempts = 0  # Reset for later retry attempts
                self._initialized = False
                return False

            # Retry logic for transient failures (only when not during startup)
            if self._initialization_attempts < self._max_attempts and self._is_retryable_error(e):
                retry_delay = 2 ** self._initialization_attempts  # Exponential backoff
                logger.info(f"🔄 Retrying Firebase initialization in {retry_delay} seconds...")
                time.sleep(retry_delay)
                return self._initialize_firebase()

            # Max attempts reached or non-retryable error - trigger circuit breaker
            self._trigger_circuit_breaker()
            self._initialized = False
            return False
    
    def _try_service_account_file(self) -> bool:
        """Try to initialize Firebase using service account file"""
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if not service_account_path:
            logger.debug("🔍 FIREBASE_SERVICE_ACCOUNT_PATH not set, skipping file-based initialization")
            return False
        
        logger.info(f"🔍 Attempting Firebase initialization from service account file: {service_account_path}")
        
        # Handle relative paths from backend directory
        if not os.path.isabs(service_account_path):
            # Get the backend directory path (3 levels up from this file)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            service_account_path = os.path.join(backend_dir, service_account_path)
            logger.debug(f"🔍 Resolved relative path to: {service_account_path}")
        
        # Validate file existence and readability
        if not os.path.exists(service_account_path):
            logger.warning(f"⚠️ Service account file not found: {service_account_path}")
            return False
        
        if not os.access(service_account_path, os.R_OK):
            logger.error(f"❌ Service account file not readable: {service_account_path}")
            return False
        
        try:
            # Validate JSON format
            with open(service_account_path, 'r') as f:
                service_account_data = json.load(f)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in service_account_data]
            if missing_fields:
                logger.error(f"❌ Service account file missing required fields: {missing_fields}")
                return False
            
            # Initialize Firebase
            cred = credentials.Certificate(service_account_path)
            self._app = firebase_admin.initialize_app(cred)

            # Initialize Firestore client
            try:
                self._firestore_db = firestore.client()
                logger.info("✅ Firestore client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Firestore client: {e}")

            logger.info(f"✅ Firebase Admin initialized from service account file: {service_account_path}")
            logger.info(f"📋 Project ID: {service_account_data.get('project_id')}")
            logger.info(f"📋 Client Email: {service_account_data.get('client_email')}")

            self._initialized = True
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in service account file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize from service account file: {str(e)}")
            return False
    
    def _try_environment_variables(self) -> bool:
        """Try to initialize Firebase using environment variables"""
        logger.info("🔍 Attempting Firebase initialization from environment variables")
        
        # Check for required environment variables
        required_env_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"⚠️ Missing required environment variables: {missing_vars}")
            return False
        
        try:
            service_account_info = {
                "type": "service_account",
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
            }
            
            # Validate private key format
            private_key = service_account_info['private_key']
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                logger.error("❌ Invalid private key format in environment variables")
                return False
            
            cred = credentials.Certificate(service_account_info)
            self._app = firebase_admin.initialize_app(cred)

            # Initialize Firestore client
            try:
                self._firestore_db = firestore.client()
                logger.info("✅ Firestore client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Firestore client: {e}")

            logger.info("✅ Firebase Admin initialized from environment variables")
            logger.info(f"📋 Project ID: {service_account_info.get('project_id')}")
            logger.info(f"📋 Client Email: {service_account_info.get('client_email')}")

            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize from environment variables: {str(e)}")
            return False
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable"""
        retryable_errors = [
            'ConnectionError',
            'TimeoutError',
            'HTTPError',
            'URLError',
            'RequestException',
            'ConnectTimeout',
            'ReadTimeout'
        ]
        error_type = type(error).__name__
        return error_type in retryable_errors
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self._circuit_breaker_open:
            return False
        
        # Check if reset timeout has passed
        if self._circuit_breaker_last_failure_time:
            time_since_failure = (datetime.utcnow() - self._circuit_breaker_last_failure_time).total_seconds()
            if time_since_failure >= self._circuit_breaker_reset_timeout:
                logger.info("🔄 Circuit breaker reset timeout reached - attempting to close circuit breaker")
                self._reset_circuit_breaker()
                return False
        
        return True
    
    def _trigger_circuit_breaker(self):
        """Trigger circuit breaker after repeated failures"""
        self._circuit_breaker_failures += 1
        self._consecutive_failures += 1
        
        if self._circuit_breaker_failures >= self._circuit_breaker_failure_threshold:
            self._circuit_breaker_open = True
            self._circuit_breaker_last_failure_time = datetime.utcnow()
            logger.error(f"⚡ Circuit breaker OPENED after {self._circuit_breaker_failures} failures")
            logger.error(f"⚡ Firebase initialization will be blocked for {self._circuit_breaker_reset_timeout} seconds")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker to allow initialization attempts"""
        self._circuit_breaker_open = False
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure_time = None
        logger.info("✅ Circuit breaker CLOSED - Firebase initialization attempts resumed")
    
    def _record_successful_initialization(self, start_time: datetime):
        """Record successful initialization for status tracking"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        self._initialization_history.append({
            'timestamp': end_time.isoformat(),
            'success': True,
            'duration_seconds': duration,
            'attempt_number': self._initialization_attempts,
            'method': 'service_account_file' if os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH') else 'environment_variables'
        })
        
        self._last_successful_init = end_time
        self._consecutive_failures = 0
        self._reset_circuit_breaker()  # Reset circuit breaker on success
        
        logger.info(f"✅ Firebase initialization successful in {duration:.2f} seconds")
    
    def _record_failed_initialization(self, start_time: datetime, error_message: str):
        """Record failed initialization for status tracking"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        self._initialization_history.append({
            'timestamp': end_time.isoformat(),
            'success': False,
            'duration_seconds': duration,
            'attempt_number': self._initialization_attempts,
            'error_message': error_message,
            'method_attempted': 'service_account_file' if os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH') else 'environment_variables'
        })
        
        self._consecutive_failures += 1
        
        logger.error(f"❌ Firebase initialization failed after {duration:.2f} seconds")
        logger.error(f"📋 Consecutive failures: {self._consecutive_failures}")
    
    def _log_configuration_status(self):
        """Log detailed configuration status for debugging"""
        logger.info("📋 Firebase Configuration Status:")
        logger.info(f"   FIREBASE_SERVICE_ACCOUNT_PATH: {os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')}")
        logger.info(f"   FIREBASE_PROJECT_ID: {os.getenv('FIREBASE_PROJECT_ID')}")
        logger.info(f"   FIREBASE_CLIENT_EMAIL: {os.getenv('FIREBASE_CLIENT_EMAIL')}")
        logger.info(f"   FIREBASE_PRIVATE_KEY exists: {bool(os.getenv('FIREBASE_PRIVATE_KEY'))}")
        logger.info(f"   FIREBASE_PRIVATE_KEY_ID: {os.getenv('FIREBASE_PRIVATE_KEY_ID')}")
        
        # Check service account file if path is provided
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if service_account_path:
            if not os.path.isabs(service_account_path):
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                service_account_path = os.path.join(backend_dir, service_account_path)
            
            logger.info(f"   Service account file exists: {os.path.exists(service_account_path)}")
            if os.path.exists(service_account_path):
                logger.info(f"   Service account file readable: {os.access(service_account_path, os.R_OK)}")
                logger.info(f"   Service account file size: {os.path.getsize(service_account_path)} bytes")
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """Get detailed initialization status for health checks"""
        return {
            'initialized': self._initialized,
            'initialization_error': self._initialization_error,
            'initialization_attempts': self._initialization_attempts,
            'max_attempts': self._max_attempts,
            'app_name': self._app.name if self._app else None,
            'project_id': os.getenv('FIREBASE_PROJECT_ID'),
            'has_service_account_path': bool(os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')),
            'has_private_key': bool(os.getenv('FIREBASE_PRIVATE_KEY')),
            
            # Circuit breaker status
            'circuit_breaker_open': self._circuit_breaker_open,
            'circuit_breaker_failures': self._circuit_breaker_failures,
            'circuit_breaker_failure_threshold': self._circuit_breaker_failure_threshold,
            'circuit_breaker_reset_timeout': self._circuit_breaker_reset_timeout,
            'circuit_breaker_last_failure_time': self._circuit_breaker_last_failure_time.isoformat() if self._circuit_breaker_last_failure_time else None,
            
            # Status tracking
            'last_successful_init': self._last_successful_init.isoformat() if self._last_successful_init else None,
            'consecutive_failures': self._consecutive_failures,
            'initialization_history_count': len(self._initialization_history),
            'recent_attempts': self._initialization_history[-5:] if self._initialization_history else []  # Last 5 attempts
        }
    
    def force_reinitialize(self) -> bool:
        """Force reinitialize Firebase (useful for testing or recovery)"""
        logger.info("🔄 Forcing Firebase reinitialization...")
        self._initialized = False
        self._initialization_error = None
        self._initialization_attempts = 0
        
        # Reset circuit breaker to allow reinitialization
        self._reset_circuit_breaker()
        
        # Delete existing app if it exists
        try:
            if self._app:
                firebase_admin.delete_app(self._app)
                self._app = None
        except Exception as e:
            logger.warning(f"⚠️ Error deleting existing Firebase app: {str(e)}")
        
        return self._initialize_firebase()
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get detailed circuit breaker status"""
        return {
            'open': self._circuit_breaker_open,
            'failures': self._circuit_breaker_failures,
            'failure_threshold': self._circuit_breaker_failure_threshold,
            'reset_timeout_seconds': self._circuit_breaker_reset_timeout,
            'last_failure_time': self._circuit_breaker_last_failure_time.isoformat() if self._circuit_breaker_last_failure_time else None,
            'time_until_reset': max(0, self._circuit_breaker_reset_timeout - (datetime.utcnow() - self._circuit_breaker_last_failure_time).total_seconds()) if self._circuit_breaker_last_failure_time else 0,
            'consecutive_failures': self._consecutive_failures
        }
    
    def get_initialization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get initialization attempt history"""
        return self._initialization_history[-limit:] if self._initialization_history else []
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate Firebase configuration and return detailed status"""
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'service_account_file': {},
            'environment_variables': {},
            'recommendations': []
        }
        
        # Check service account file configuration
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if service_account_path:
            file_validation = self._validate_service_account_file(service_account_path)
            validation_result['service_account_file'] = file_validation
            
            if file_validation['valid']:
                validation_result['valid'] = True
            else:
                validation_result['errors'].extend(file_validation['errors'])
        else:
            validation_result['warnings'].append("FIREBASE_SERVICE_ACCOUNT_PATH not set")
        
        # Check environment variables configuration
        env_validation = self._validate_environment_variables()
        validation_result['environment_variables'] = env_validation
        
        if not validation_result['valid'] and env_validation['valid']:
            validation_result['valid'] = True
        
        if not env_validation['valid']:
            validation_result['warnings'].extend(env_validation['warnings'])
        
        # Add recommendations
        if not validation_result['valid']:
            validation_result['recommendations'].extend([
                "Ensure either FIREBASE_SERVICE_ACCOUNT_PATH points to a valid service account file",
                "Or set all required environment variables: FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL",
                "Check the Firebase Console for correct service account credentials",
                "Verify file permissions if using service account file"
            ])
        
        return validation_result
    
    def _validate_service_account_file(self, service_account_path: str) -> Dict[str, Any]:
        """Validate service account file configuration"""
        result = {
            'valid': False,
            'errors': [],
            'file_path': service_account_path,
            'resolved_path': None,
            'file_exists': False,
            'file_readable': False,
            'valid_json': False,
            'required_fields_present': False,
            'project_id': None
        }
        
        try:
            # Resolve relative paths
            if not os.path.isabs(service_account_path):
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                resolved_path = os.path.join(backend_dir, service_account_path)
            else:
                resolved_path = service_account_path
            
            result['resolved_path'] = resolved_path
            
            # Check file existence
            if not os.path.exists(resolved_path):
                result['errors'].append(f"Service account file not found: {resolved_path}")
                return result
            
            result['file_exists'] = True
            
            # Check file readability
            if not os.access(resolved_path, os.R_OK):
                result['errors'].append(f"Service account file not readable: {resolved_path}")
                return result
            
            result['file_readable'] = True
            
            # Validate JSON format
            try:
                with open(resolved_path, 'r') as f:
                    service_account_data = json.load(f)
                result['valid_json'] = True
            except json.JSONDecodeError as e:
                result['errors'].append(f"Invalid JSON in service account file: {str(e)}")
                return result
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email', 'private_key_id']
            missing_fields = [field for field in required_fields if field not in service_account_data]
            
            if missing_fields:
                result['errors'].append(f"Missing required fields in service account file: {missing_fields}")
                return result
            
            result['required_fields_present'] = True
            result['project_id'] = service_account_data.get('project_id')
            
            # Validate service account type
            if service_account_data.get('type') != 'service_account':
                result['errors'].append(f"Invalid service account type: {service_account_data.get('type')}")
                return result
            
            # Validate private key format
            private_key = service_account_data.get('private_key', '')
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                result['errors'].append("Invalid private key format")
                return result
            
            result['valid'] = True
            
        except Exception as e:
            result['errors'].append(f"Unexpected error validating service account file: {str(e)}")
        
        return result
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variables configuration"""
        result = {
            'valid': False,
            'warnings': [],
            'present_variables': {},
            'missing_variables': [],
            'project_id': None
        }
        
        required_vars = {
            'FIREBASE_PROJECT_ID': 'Firebase project ID',
            'FIREBASE_PRIVATE_KEY': 'Firebase private key',
            'FIREBASE_CLIENT_EMAIL': 'Firebase client email'
        }
        
        optional_vars = {
            'FIREBASE_PRIVATE_KEY_ID': 'Firebase private key ID',
            'FIREBASE_CLIENT_ID': 'Firebase client ID',
            'FIREBASE_CLIENT_CERT_URL': 'Firebase client certificate URL'
        }
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                result['present_variables'][var] = {
                    'present': True,
                    'length': len(value),
                    'description': description
                }
                if var == 'FIREBASE_PROJECT_ID':
                    result['project_id'] = value
            else:
                result['missing_variables'].append(var)
                result['present_variables'][var] = {
                    'present': False,
                    'description': description
                }
        
        # Check optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var)
            result['present_variables'][var] = {
                'present': bool(value),
                'length': len(value) if value else 0,
                'description': description
            }
        
        # Validate private key format if present
        private_key = os.getenv('FIREBASE_PRIVATE_KEY')
        if private_key:
            # Replace escaped newlines for validation
            formatted_key = private_key.replace('\\n', '\n')
            if not formatted_key.startswith('-----BEGIN PRIVATE KEY-----'):
                result['warnings'].append("FIREBASE_PRIVATE_KEY does not appear to be in correct format")
        
        # Determine if configuration is valid
        if not result['missing_variables']:
            result['valid'] = True
        else:
            result['warnings'].append(f"Missing required environment variables: {result['missing_variables']}")
        
        return result
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token with comprehensive error handling"""
        if not self._initialized:
            logger.error("❌ Firebase not initialized - cannot verify token")
            logger.error(f"📋 Initialization error: {self._initialization_error}")
            return None
        
        if not id_token:
            logger.error("❌ Empty or None token provided for verification")
            return None
        
        if not isinstance(id_token, str):
            logger.error(f"❌ Invalid token type: {type(id_token)}, expected string")
            return None
            
        try:
            logger.debug(f"🔍 Verifying Firebase token (length: {len(id_token)})")
            decoded_token = auth.verify_id_token(id_token)
            
            # Log successful verification with user info
            uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            logger.info(f"✅ Token verified successfully for user: {email} (UID: {uid})")
            
            return decoded_token
            
        except auth.InvalidIdTokenError as e:
            logger.error(f"❌ Invalid Firebase ID token: {str(e)}")
            return None
        except auth.ExpiredIdTokenError as e:
            logger.error(f"❌ Expired Firebase ID token: {str(e)}")
            return None
        except auth.RevokedIdTokenError as e:
            logger.error(f"❌ Revoked Firebase ID token: {str(e)}")
            return None
        except auth.CertificateFetchError as e:
            logger.error(f"❌ Firebase certificate fetch error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected token verification error: {str(e)}")
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            return None
    
    def _get_or_create_user_firestore(self, firebase_token: Dict[str, Any], additional_data: Dict[str, Any] = None) -> Optional[Dict]:
        """Get or create user in Firestore"""
        firebase_uid = firebase_token.get('uid')
        email = firebase_token.get('email')

        try:
            # Check if user exists by Firebase UID
            users_ref = self._firestore_db.collection('users')
            query = users_ref.where(filter=FieldFilter('firebaseUid', '==', firebase_uid)).where(filter=FieldFilter('isActive', '==', True)).limit(1)
            docs = list(query.stream())

            if docs:
                # User exists, update last login
                user_doc = docs[0]
                user_data = user_doc.to_dict()
                user_data['id'] = user_doc.id

                # Update last login
                user_doc.reference.update({
                    'lastLogin': firestore.SERVER_TIMESTAMP,
                    'updatedAt': firestore.SERVER_TIMESTAMP
                })

                logger.info(f"✅ Found existing Firestore user: {email}")
                return user_data

            # User doesn't exist, create new
            logger.info(f"👤 Creating new Firestore user: {email}")

            # Parse display name
            display_name = firebase_token.get('name', '')
            first_name, last_name = '', ''
            if display_name:
                parts = display_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''

            # Use additional data if provided
            if additional_data:
                first_name = additional_data.get('firstName', first_name)
                last_name = additional_data.get('lastName', last_name)

            # Create user document
            user_data = {
                'firebaseUid': firebase_uid,
                'email': email,
                'profile': {
                    'firstName': first_name,
                    'lastName': last_name,
                    'displayName': display_name,
                    'photoURL': firebase_token.get('picture', ''),
                    'phoneNumber': firebase_token.get('phone_number', ''),
                },
                'role': 'user',  # Default role lowercase
                'isActive': True,
                'isVerified': firebase_token.get('email_verified', False),
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'lastLogin': firestore.SERVER_TIMESTAMP,
            }

            # Create document with auto-generated ID
            doc_ref = users_ref.document()
            doc_ref.set(user_data)
            user_data['id'] = doc_ref.id

            logger.info(f"✅ Created new Firestore user: {email} (ID: {doc_ref.id})")
            return user_data

        except Exception as e:
            logger.error(f"❌ Firestore user creation/sync failed: {str(e)}")
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            return None

    def get_or_create_user(self, firebase_token: Dict[str, Any], additional_data: Dict[str, Any] = None) -> Optional[User]:
        """Get or create user from Firebase token with comprehensive error handling"""
        if not firebase_token:
            logger.error("❌ No Firebase token provided for user creation")
            return None

        firebase_uid = firebase_token.get('uid')
        email = firebase_token.get('email')

        if not firebase_uid:
            logger.error("❌ Missing 'uid' field in Firebase token")
            return None

        if not email:
            logger.error("❌ Missing 'email' field in Firebase token")
            return None

        logger.info(f"🔍 Processing user sync for: {email} (UID: {firebase_uid})")

        # Use Firestore if available, otherwise fall back to SQLAlchemy
        if self._firestore_db:
            return self._get_or_create_user_firestore(firebase_token, additional_data)

        try:
            # Try to find existing user by Firebase UID (primary lookup)
            user = User.query.filter_by(firebase_uid=firebase_uid).first()
            
            if user:
                logger.info(f"✅ Found existing user by Firebase UID: {email}")
                # Update last login and any changed profile data
                user.last_login = datetime.utcnow()
                
                # Update profile data from Firebase token if available
                if firebase_token.get('name') and not (user.first_name and user.last_name):
                    display_name = firebase_token.get('name', '')
                    if display_name:
                        name_parts = display_name.split(' ', 1)
                        if not user.first_name:
                            user.first_name = name_parts[0]
                        if not user.last_name and len(name_parts) > 1:
                            user.last_name = name_parts[1]
                
                if firebase_token.get('picture') and not user.avatar_url:
                    user.avatar_url = firebase_token.get('picture')
                
                db.session.commit()
                logger.info(f"✅ Updated existing user login time: {email}")
                return user
            
            # Try to find existing user by email (for migration scenarios)
            user = User.query.filter_by(email=email).first()
            
            if user:
                logger.info(f"🔗 Found existing user by email, linking to Firebase: {email}")
                # Link existing user to Firebase
                user.firebase_uid = firebase_uid
                user.last_login = datetime.utcnow()
                
                # Update profile data from Firebase if not already set
                if firebase_token.get('name') and not (user.first_name and user.last_name):
                    display_name = firebase_token.get('name', '')
                    if display_name:
                        name_parts = display_name.split(' ', 1)
                        if not user.first_name:
                            user.first_name = name_parts[0]
                        if not user.last_name and len(name_parts) > 1:
                            user.last_name = name_parts[1]
                
                if firebase_token.get('picture') and not user.avatar_url:
                    user.avatar_url = firebase_token.get('picture')
                
                db.session.commit()
                logger.info(f"✅ Linked existing user {email} to Firebase UID {firebase_uid}")
                return user
            
            # Create new user
            logger.info(f"👤 Creating new user from Firebase: {email}")
            
            # Parse display name
            display_name = firebase_token.get('name', '')
            first_name = ''
            last_name = ''
            
            if display_name:
                name_parts = display_name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Use additional data if provided (from registration form)
            if additional_data:
                first_name = additional_data.get('firstName', first_name)
                last_name = additional_data.get('lastName', last_name)
                logger.debug(f"📋 Using additional data: firstName={first_name}, lastName={last_name}")
            
            # Generate unique username
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            
            # Ensure username uniqueness
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                avatar_url=firebase_token.get('picture'),
                is_active=True,
                role=UserRole.USER,  # Default role
                last_login=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"✅ Created new user from Firebase: {email} (ID: {user.id})")
            logger.info(f"📋 User details: username={username}, name={first_name} {last_name}")
            
            return user
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"❌ User creation failed - integrity error: {str(e)}")
            logger.error(f"📋 This usually indicates a duplicate email or username")
            
            # Try to get existing user as fallback
            try:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    logger.info(f"🔄 Found existing user after integrity error: {email}")
                    return existing_user
            except Exception as fallback_error:
                logger.error(f"❌ Fallback user lookup failed: {str(fallback_error)}")
            
            return None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ User creation/sync failed: {str(e)}")
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            return None

# Global Firebase auth manager
firebase_auth_manager = FirebaseAuthManager()

def validate_firebase_startup_config() -> bool:
    """Validate Firebase configuration at startup and log results"""
    logger.info("🔍 Validating Firebase configuration at startup...")
    
    validation_result = firebase_auth_manager.validate_configuration()
    
    if validation_result['valid']:
        logger.info("✅ Firebase configuration validation passed")
        
        # Log which method is being used
        if validation_result['service_account_file'].get('valid'):
            project_id = validation_result['service_account_file'].get('project_id')
            logger.info(f"📋 Using service account file for project: {project_id}")
        elif validation_result['environment_variables'].get('valid'):
            project_id = validation_result['environment_variables'].get('project_id')
            logger.info(f"📋 Using environment variables for project: {project_id}")
        
        return True
    else:
        logger.error("❌ Firebase configuration validation failed")
        
        # Log errors
        for error in validation_result['errors']:
            logger.error(f"   ❌ {error}")
        
        # Log warnings
        for warning in validation_result['warnings']:
            logger.warning(f"   ⚠️ {warning}")
        
        # Log recommendations
        logger.info("💡 Recommendations:")
        for recommendation in validation_result['recommendations']:
            logger.info(f"   • {recommendation}")
        
        return False

def get_firebase_config_summary() -> Dict[str, Any]:
    """Get a summary of Firebase configuration for debugging"""
    return {
        'initialized': firebase_auth_manager._initialized,
        'initialization_error': firebase_auth_manager._initialization_error,
        'validation_result': firebase_auth_manager.validate_configuration(),
        'environment_summary': {
            'service_account_path': os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'),
            'project_id': os.getenv('FIREBASE_PROJECT_ID'),
            'has_private_key': bool(os.getenv('FIREBASE_PRIVATE_KEY')),
            'client_email': os.getenv('FIREBASE_CLIENT_EMAIL')
        }
    }

def verify_firebase_token(f):
    """Decorator to verify Firebase token (without requiring user creation)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_id = f"verify_{int(datetime.utcnow().timestamp() * 1000)}"
        endpoint = f"{request.method} {request.endpoint or request.path}"
        
        logger.debug(f"🔍 [{request_id}] Token verification for: {endpoint}")
        
        try:
            # Check Firebase initialization
            if not firebase_auth_manager._initialized:
                logger.error(f"❌ [{request_id}] Firebase not initialized for {endpoint}")
                return jsonify({
                    'error': 'Authentication service unavailable',
                    'code': 'AUTH_SERVICE_UNAVAILABLE',
                    'request_id': request_id
                }), 503
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                logger.warning(f"❌ [{request_id}] No authorization header for {endpoint}")
                return jsonify({
                    'error': 'No authorization header provided',
                    'code': 'MISSING_AUTH_HEADER',
                    'request_id': request_id
                }), 401
            
            # Extract token (format: "Bearer <token>")
            token_parts = auth_header.split(' ')
            if len(token_parts) != 2 or token_parts[0] != 'Bearer':
                logger.warning(f"❌ [{request_id}] Invalid auth header format for {endpoint}")
                return jsonify({
                    'error': 'Invalid authorization header format',
                    'code': 'INVALID_AUTH_HEADER',
                    'request_id': request_id
                }), 401
            
            id_token = token_parts[1]
            
            # Verify token with Firebase
            decoded_token = firebase_auth_manager.verify_token(id_token)
            if not decoded_token:
                logger.warning(f"❌ [{request_id}] Token verification failed for {endpoint}")
                return jsonify({
                    'error': 'Invalid or expired token',
                    'code': 'INVALID_TOKEN',
                    'request_id': request_id
                }), 401
            
            # Store decoded token in g for use in the route
            g.firebase_token = decoded_token
            g.firebase_uid = decoded_token.get('uid')
            g.request_id = request_id
            
            # Optionally get or create user (non-blocking)
            try:
                user = firebase_auth_manager.get_or_create_user(decoded_token)
                if user:
                    g.current_user = user
                    g.current_user_id = user.id
            except Exception as user_error:
                logger.warning(f"⚠️ [{request_id}] User creation failed but continuing: {str(user_error)}")
                # Continue without user context
            
            logger.debug(f"✅ [{request_id}] Token verification successful for {endpoint}")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Token verification error for {endpoint}: {str(e)}")
            logger.error(f"📋 [{request_id}] Stack trace: {traceback.format_exc()}")
            
            return jsonify({
                'error': 'Token verification failed',
                'code': 'TOKEN_VERIFICATION_ERROR',
                'request_id': request_id
            }), 401
    
    return decorated_function

def require_firebase_auth(f):
    """Decorator that requires Firebase authentication and ensures user exists"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_id = f"auth_{int(datetime.utcnow().timestamp() * 1000)}"
        endpoint = f"{request.method} {request.endpoint or request.path}"
        
        logger.debug(f"🔐 [{request_id}] Authentication required for: {endpoint}")
        
        try:
            # Check Firebase initialization status first
            if not firebase_auth_manager._initialized:
                logger.error(f"❌ [{request_id}] Firebase not initialized for {endpoint}")
                return jsonify({
                    'error': 'Authentication service unavailable',
                    'code': 'AUTH_SERVICE_UNAVAILABLE',
                    'request_id': request_id
                }), 503
            
            # Verify Authorization header presence
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                logger.warning(f"❌ [{request_id}] No authorization header for {endpoint}")
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'MISSING_AUTH_HEADER',
                    'request_id': request_id,
                    'suggestion': 'Please include Authorization header with Firebase token'
                }), 401
            
            # Parse Authorization header
            token_parts = auth_header.split(' ')
            if len(token_parts) != 2 or token_parts[0] != 'Bearer':
                logger.warning(f"❌ [{request_id}] Invalid auth header format for {endpoint}")
                return jsonify({
                    'error': 'Invalid authorization header format',
                    'code': 'INVALID_AUTH_HEADER',
                    'request_id': request_id,
                    'expected_format': 'Bearer <firebase_id_token>'
                }), 401
            
            id_token = token_parts[1]
            logger.debug(f"🔍 [{request_id}] Verifying token for {endpoint} (length: {len(id_token)})")
            
            # Verify Firebase token
            decoded_token = firebase_auth_manager.verify_token(id_token)
            
            if not decoded_token:
                logger.warning(f"❌ [{request_id}] Token verification failed for {endpoint}")
                return jsonify({
                    'error': 'Invalid or expired token',
                    'code': 'INVALID_TOKEN',
                    'request_id': request_id,
                    'suggestion': 'Please log in again to refresh your authentication token'
                }), 401
            
            # Extract user info from token
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            logger.debug(f"✅ [{request_id}] Token verified for {email} (UID: {firebase_uid})")
            
            # Get or create user in database
            try:
                user = firebase_auth_manager.get_or_create_user(decoded_token)
                
                if not user:
                    logger.error(f"❌ [{request_id}] User creation/retrieval failed for {email}")
                    return jsonify({
                        'error': 'User authentication failed',
                        'code': 'USER_AUTH_FAILED',
                        'request_id': request_id,
                        'suggestion': 'Please try logging in again'
                    }), 401
                
                # Store authentication context in Flask's g object
                g.firebase_token = decoded_token
                g.current_user = user
                # Handle both dict (Firestore) and User object (SQLAlchemy)
                g.current_user_id = user.get('id') if isinstance(user, dict) else user.id
                g.firebase_uid = firebase_uid
                g.request_id = request_id
                
                logger.debug(f"✅ [{request_id}] Authentication successful for {email} accessing {endpoint}")
                
                # Call the protected function
                return f(*args, **kwargs)
                
            except Exception as user_error:
                logger.error(f"❌ [{request_id}] User processing error for {endpoint}: {str(user_error)}")
                logger.error(f"📋 [{request_id}] Stack trace: {traceback.format_exc()}")
                
                return jsonify({
                    'error': 'User authentication processing failed',
                    'code': 'USER_PROCESSING_ERROR',
                    'request_id': request_id
                }), 500
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Unexpected authentication error for {endpoint}: {str(e)}")
            logger.error(f"📋 [{request_id}] Stack trace: {traceback.format_exc()}")
            
            return jsonify({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR',
                'request_id': request_id,
                'message': str(e) if current_app and current_app.debug else 'Internal authentication error'
            }), 500
    
    return decorated_function

def get_current_firebase_user() -> Optional[User]:
    """Get current authenticated Firebase user"""
    return getattr(g, 'current_user', None)

def get_current_firebase_token() -> Optional[Dict[str, Any]]:
    """Get current Firebase token payload"""
    return getattr(g, 'firebase_token', None)

def get_current_request_id() -> Optional[str]:
    """Get current request ID for logging correlation"""
    return getattr(g, 'request_id', None)

def create_auth_error_response(error_code: str, message: str, request_id: str = None, 
                              suggestion: str = None, status_code: int = 401) -> tuple:
    """Create standardized authentication error response"""
    response_data = {
        'error': message,
        'code': error_code,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if request_id:
        response_data['request_id'] = request_id
    
    if suggestion:
        response_data['suggestion'] = suggestion
    
    return jsonify(response_data), status_code

def log_auth_event(event_type: str, user_email: str = None, firebase_uid: str = None, 
                  endpoint: str = None, success: bool = True, error_message: str = None,
                  request_id: str = None):
    """Log authentication events for monitoring and debugging"""
    log_data = {
        'event_type': event_type,
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        'endpoint': endpoint,
        'request_id': request_id
    }
    
    if user_email:
        log_data['user_email'] = user_email
    
    if firebase_uid:
        log_data['firebase_uid'] = firebase_uid
    
    if error_message:
        log_data['error_message'] = error_message
    
    if success:
        logger.info(f"🔐 Auth Event: {event_type} - {log_data}")
    else:
        logger.warning(f"🔐 Auth Event Failed: {event_type} - {log_data}")

# Authentication status constants
class AuthStatus:
    SUCCESS = "AUTH_SUCCESS"
    MISSING_HEADER = "MISSING_AUTH_HEADER"
    INVALID_HEADER = "INVALID_AUTH_HEADER"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    SERVICE_UNAVAILABLE = "AUTH_SERVICE_UNAVAILABLE"
    PROCESSING_ERROR = "USER_PROCESSING_ERROR"