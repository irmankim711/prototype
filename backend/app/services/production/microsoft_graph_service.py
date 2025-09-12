"""
Production Microsoft Graph Service - ZERO MOCK DATA
Real Microsoft Graph API integration for production deployment with enhanced OAuth security
"""

import os
import json
import pickle
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.models import Form, FormSubmission, User, FormIntegration, FormResponse, Participant
from app import db
from app.core.oauth_config import (
    get_oauth_config, 
    OAuthProvider, 
    OAuthProviderConfig,
    OAuthAuditLogger
)

logger = logging.getLogger(__name__)

class MicrosoftGraphService:
    """
    Production Microsoft Graph Service - ZERO MOCK DATA with enhanced OAuth security
    
    Features:
    - Real Microsoft Graph API integration
    - Enhanced OAuth security with state validation
    - CSRF protection and audit logging
    - Token refresh logic and secure storage
    - Error handling with user-friendly messages
    - Minimal required permissions
    - Callback URL validation
    """

    def __init__(self):
        # Get OAuth configuration
        self.oauth_config = get_oauth_config()
        self.microsoft_config = self.oauth_config.get_provider_config(OAuthProvider.MICROSOFT)
        self.audit_logger = OAuthAuditLogger()
        
        if not self.microsoft_config.enabled:
            logger.warning("Microsoft Graph service disabled - OAuth not configured")
            return
        
        # Use OAuth configuration
        self.client_id = self.microsoft_config.client_id
        self.client_secret = self.microsoft_config.client_secret
        self.redirect_uri = self.microsoft_config.redirect_uri
        self.scopes = [scope.scope for scope in self.microsoft_config.scopes]
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', 'common')
        
        # Token storage configuration
        self.tokens_dir = os.getenv('MICROSOFT_TOKEN_FILE', './tokens/microsoft/')
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # NO MOCK MODE - This is production only
        self.mock_mode = False  # ALWAYS FALSE for production
        
        logger.info(f"Microsoft Graph Service initialized for production with client ID: {self.client_id[:20]}...")

    def _check_enabled(self):
        """Check if Microsoft Graph service is enabled."""
        if not self.microsoft_config.enabled:
            raise Exception("Microsoft Graph integration not available - OAuth not configured")

    async def get_authorization_url(self, user_id: str, redirect_uri: Optional[str] = None) -> Dict[str, str]:
        """Get real Microsoft OAuth authorization URL with enhanced security - NO MOCK DATA"""
        try:
            self._check_enabled()
            
            # Use centralized OAuth configuration
            auth_result = self.oauth_config.get_authorization_url(
                OAuthProvider.MICROSOFT, 
                user_id, 
                redirect_uri
            )
            
            logger.info(f"Generated real Microsoft OAuth URL for user {user_id}")
            
            return {
                'authorization_url': auth_result['authorization_url'],
                'state': auth_result['state'],
                'status': 'success',
                'platform': 'microsoft_graph',
                'scopes': auth_result['scopes']
            }
            
        except Exception as e:
            logger.error(f"Error generating Microsoft authorization URL: {str(e)}")
            self.audit_logger.log_oauth_error(
                user_id, OAuthProvider.MICROSOFT, "AUTH_URL_GENERATION", str(e)
            )
            raise Exception(f"Failed to generate authorization URL: {str(e)}")

    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle real OAuth callback with enhanced security - NO MOCK DATA"""
        self._check_enabled()
        
        try:
            # Extract user_id from state (state format: user_id_timestamp_random)
            # The state validation will be handled by the OAuth config
            user_id = state.split('_')[0] if '_' in state else state
            
            # Validate OAuth callback using centralized configuration
            if not self.oauth_config.validate_oauth_callback(
                OAuthProvider.MICROSOFT, user_id, state, code
            ):
                raise ValueError("OAuth callback validation failed")
            
            # Exchange code for tokens using Microsoft OAuth flow
            # Note: In production, you would use the Microsoft Authentication Library (MSAL)
            # For now, we'll simulate the token exchange process
            token_data = await self._exchange_code_for_tokens(code, state)
            
            # Store credentials securely for user
            await self._store_credentials(user_id, token_data)
            
            # Log successful authentication
            self.audit_logger.log_oauth_callback(user_id, OAuthProvider.MICROSOFT, state, True)
            
            logger.info(f"Microsoft OAuth callback successful for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'access_token': token_data.get('access_token'),
                'expires_in': token_data.get('expires_in', 3600),
                'platform': 'microsoft_graph',
                'status': 'success'
            }
                
        except Exception as e:
            logger.error(f"Error handling Microsoft OAuth callback: {str(e)}")
            user_id = state.split('_')[0] if '_' in state else state
            self.audit_logger.log_oauth_callback(
                user_id, OAuthProvider.MICROSOFT, state, False, str(e)
            )
            raise Exception(f"Failed to handle OAuth callback: {str(e)}")

    async def _exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens - NO MOCK DATA"""
        try:
            # In production, this would use MSAL or direct HTTP requests to Microsoft's token endpoint
            # For now, we'll simulate the process
            
            # Microsoft OAuth2 token endpoint
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            # Prepare token request data
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
                'scope': ' '.join(self.scopes)
            }
            
            # In production, you would make an HTTP POST request here
            # For now, we'll return a simulated token response
            # This should be replaced with actual HTTP client implementation
            
            import requests
            
            response = requests.post(token_url, data=token_data)
            
            if response.status_code == 200:
                token_response = response.json()
                
                return {
                    'access_token': token_response.get('access_token'),
                    'refresh_token': token_response.get('refresh_token'),
                    'expires_in': token_response.get('expires_in', 3600),
                    'token_type': token_response.get('token_type', 'Bearer'),
                    'scope': token_response.get('scope', ' '.join(self.scopes))
                }
            else:
                error_data = response.json()
                error_description = error_data.get('error_description', 'Unknown error')
                raise Exception(f"Token exchange failed: {error_description}")
                
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            raise Exception(f"Token exchange failed: {str(e)}")

    async def _store_credentials(self, user_id: str, token_data: Dict[str, Any]):
        """Store user credentials securely with enhanced error handling."""
        try:
            # Store credentials in file system
            token_path = os.path.join(self.tokens_dir, f"user_{user_id}_token.pickle")
            
            # Create credentials object
            credentials = {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in', 3600),
                'token_type': token_data.get('token_type', 'Bearer'),
                'scope': token_data.get('scope'),
                'expires_at': datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600)),
                'created_at': datetime.utcnow()
            }
            
            with open(token_path, 'wb') as token_file:
                pickle.dump(credentials, token_file)
            
            # Store token in database for tracking
            from app.models.production import UserToken, User
            
            user = User.query.filter_by(id=user_id).first()
            if user:
                # Remove existing Microsoft tokens for this user
                existing_tokens = UserToken.query.filter_by(
                    user_id=user.id,
                    platform='microsoft'
                ).all()
                
                for token in existing_tokens:
                    db.session.delete(token)
                
                # Create new token record
                user_token = UserToken(
                    user_id=user.id,
                    platform='microsoft',
                    access_token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    expires_at=credentials['expires_at'],
                    scopes=self.scopes,
                    platform_user_id=user_id
                )
                db.session.add(user_token)
                db.session.commit()
                
                logger.info(f"Successfully stored Microsoft OAuth credentials for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing Microsoft credentials: {str(e)}")
            raise Exception(f"Failed to store credentials: {str(e)}")

    def get_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get stored credentials for user with automatic refresh - NO MOCK DATA"""
        self._check_enabled()
        
        token_path = os.path.join(self.tokens_dir, f"user_{user_id}_token.pickle")
        
        if not os.path.exists(token_path):
            return None
            
        try:
            with open(token_path, 'rb') as token_file:
                credentials = pickle.load(token_file)
            
            # Check if credentials need refresh
            if credentials.get('expires_at') and datetime.utcnow() > credentials['expires_at']:
                if credentials.get('refresh_token'):
                    try:
                        # Refresh credentials
                        refreshed_credentials = self._refresh_tokens(user_id, credentials['refresh_token'])
                        
                        # Save refreshed credentials
                        with open(token_path, 'wb') as token_file:
                            pickle.dump(refreshed_credentials, token_file)
                        
                        # Update database token
                        self._update_database_token(user_id, refreshed_credentials)
                        
                        # Log successful refresh
                        self.audit_logger.log_token_refresh(user_id, OAuthProvider.MICROSOFT, True)
                        
                        logger.info(f"Successfully refreshed Microsoft credentials for user {user_id}")
                        
                        return refreshed_credentials
                        
                    except Exception as refresh_error:
                        logger.error(f"Failed to refresh Microsoft credentials for user {user_id}: {refresh_error}")
                        self.audit_logger.log_token_refresh(
                            user_id, OAuthProvider.MICROSOFT, False, str(refresh_error)
                        )
                        
                        # Remove invalid credentials
                        os.remove(token_path)
                        return None
                else:
                    # No refresh token, remove expired credentials
                    os.remove(token_path)
                    return None
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error loading Microsoft credentials: {str(e)}")
            return None

    def _refresh_tokens(self, user_id: str, refresh_token: str) -> Dict[str, Any]:
        """Refresh Microsoft access tokens - NO MOCK DATA"""
        try:
            # Microsoft OAuth2 token refresh endpoint
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            # Prepare refresh request data
            refresh_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'scope': ' '.join(self.scopes)
            }
            
            import requests
            
            response = requests.post(token_url, data=refresh_data)
            
            if response.status_code == 200:
                token_response = response.json()
                
                return {
                    'access_token': token_response.get('access_token'),
                    'refresh_token': token_response.get('refresh_token', refresh_token),  # Keep old if not provided
                    'expires_in': token_response.get('expires_in', 3600),
                    'token_type': token_response.get('token_type', 'Bearer'),
                    'scope': token_response.get('scope', ' '.join(self.scopes)),
                    'expires_at': datetime.utcnow() + timedelta(seconds=token_response.get('expires_in', 3600)),
                    'created_at': datetime.utcnow()
                }
            else:
                error_data = response.json()
                error_description = error_data.get('error_description', 'Unknown error')
                raise Exception(f"Token refresh failed: {error_description}")
                
        except Exception as e:
            logger.error(f"Error refreshing Microsoft tokens: {str(e)}")
            raise Exception(f"Token refresh failed: {str(e)}")

    def _update_database_token(self, user_id: str, credentials: Dict[str, Any]):
        """Update database token record with refreshed credentials."""
        try:
            from app.models.production import UserToken
            
            user_token = UserToken.query.filter_by(
                platform_user_id=user_id,
                platform='microsoft'
            ).first()
            
            if user_token:
                user_token.access_token = credentials.get('access_token')
                user_token.expires_at = credentials.get('expires_at')
                user_token.last_updated = datetime.utcnow()
                user_token.update_usage()
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating database token: {str(e)}")

    async def get_user_forms(self, user_id: str, page_size: int = 50) -> Dict[str, Any]:
        """Get real Microsoft Forms for authenticated user - NO MOCK DATA"""
        self._check_enabled()
        
        credentials = self.get_credentials(user_id)
        if not credentials:
            raise Exception("User not authenticated. Please authorize access to Microsoft Forms.")
        
        try:
            # In production, you would use the Microsoft Graph SDK or direct HTTP requests
            # For now, we'll simulate the API call structure
            
            access_token = credentials.get('access_token')
            if not access_token:
                raise Exception("No valid access token available")
            
            # Microsoft Graph API endpoint for forms
            graph_url = "https://graph.microsoft.com/v1.0/me/forms"
            
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            params = {
                '$top': page_size,
                '$select': 'id,displayName,createdDateTime,lastModifiedDateTime,webUrl'
            }
            
            import requests
            
            response = requests.get(graph_url, headers=headers, params=params)
            
            if response.status_code == 200:
                forms_data = response.json()
                forms = forms_data.get('value', [])
                
                processed_forms = []
                
                logger.info(f"Found {len(forms)} real Microsoft Forms for user {user_id}")
                
                for form in forms:
                    processed_form = {
                        'id': form.get('id'),
                        'title': form.get('displayName'),
                        'created_time': form.get('createdDateTime'),
                        'modified_time': form.get('lastModifiedDateTime'),
                        'web_url': form.get('webUrl'),
                        'platform': 'microsoft_forms'
                    }
                    processed_forms.append(processed_form)
                
                return {
                    'forms': processed_forms,
                    'total_count': len(processed_forms),
                    'status': 'success',
                    'platform': 'microsoft_forms'
                }
            else:
                error_data = response.json()
                error_description = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Failed to fetch forms: {error_description}")
                
        except Exception as e:
            logger.error(f"Error fetching user forms: {str(e)}")
            raise Exception(f"Failed to fetch forms: {str(e)}")

    async def get_form_responses(self, user_id: str, form_id: str) -> Dict[str, Any]:
        """Get real form responses from Microsoft Forms - NO MOCK DATA"""
        self._check_enabled()
        
        credentials = self.get_credentials(user_id)
        if not credentials:
            raise Exception("User not authenticated")
        
        try:
            access_token = credentials.get('access_token')
            if not access_token:
                raise Exception("No valid access token available")
            
            # Microsoft Graph API endpoint for form responses
            graph_url = f"https://graph.microsoft.com/v1.0/me/forms/{form_id}/responses"
            
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            import requests
            
            response = requests.get(graph_url, headers=headers)
            
            if response.status_code == 200:
                responses_data = response.json()
                responses = responses_data.get('value', [])
                
                # Process responses
                processed_responses = []
                
                logger.info(f"Processing {len(responses)} real responses for Microsoft form {form_id}")
                
                for response_item in responses:
                    processed_response = {
                        'response_id': response_item.get('id'),
                        'create_time': response_item.get('createdDateTime'),
                        'last_submitted_time': response_item.get('lastModifiedDateTime'),
                        'answers': response_item.get('answers', {})
                    }
                    processed_responses.append(processed_response)
                
                return {
                    'response_count': len(processed_responses),
                    'responses': processed_responses,
                    'status': 'success',
                    'platform': 'microsoft_forms'
                }
            else:
                error_data = response.json()
                error_description = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Failed to fetch responses: {error_description}")
                
        except Exception as e:
            logger.error(f"Error fetching form responses: {str(e)}")
            raise Exception(f"Failed to fetch responses: {str(e)}")

    def get_oauth_status(self, user_id: str) -> Dict[str, Any]:
        """Get OAuth status and configuration for user."""
        try:
            if not self.microsoft_config.enabled:
                return {
                    'status': 'error',
                    'error': 'Microsoft Graph integration not enabled',
                    'user_id': user_id
                }
            
            credentials = self.get_credentials(user_id)
            config_summary = self.oauth_config.get_configuration_summary()
            
            return {
                'status': 'success',
                'oauth_status': {
                    'authenticated': credentials is not None,
                    'provider': 'microsoft',
                    'scopes': self.scopes,
                    'required_scopes': self.oauth_config.get_required_scopes(OAuthProvider.MICROSOFT),
                    'optional_scopes': self.oauth_config.get_optional_scopes(OAuthProvider.MICROSOFT)
                },
                'configuration': config_summary,
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting OAuth status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'user_id': user_id
            }

    def is_enabled(self) -> bool:
        """Check if Microsoft Graph service is enabled."""
        return self.microsoft_config.enabled if hasattr(self, 'microsoft_config') else False
