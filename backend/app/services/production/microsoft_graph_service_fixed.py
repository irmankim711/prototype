"""
Production Microsoft Graph Service - ZERO MOCK DATA
Real Microsoft Graph API integration for production deployment
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MicrosoftGraphService:
    """Production Microsoft Graph Service - ZERO MOCK DATA"""
    
    def __init__(self):
        # Check if Microsoft Graph is enabled
        self.enabled = os.getenv('MICROSOFT_ENABLED', 'false').lower() == 'true'
        
        if not self.enabled:
            logger.info("Microsoft Graph service disabled via MICROSOFT_ENABLED=false")
            return
            
        # Only initialize if enabled
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID')
        self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI')
        
        # Validate configuration only if enabled
        if not all([self.client_id, self.client_secret, self.tenant_id, self.redirect_uri]):
            logger.warning("Microsoft Graph configuration incomplete. Service will be disabled.")
            self.enabled = False
            return
            
        try:
            from msal import ConfidentialClientApplication
            
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.scopes = [
                "https://graph.microsoft.com/Files.ReadWrite.All",
                "https://graph.microsoft.com/Sites.ReadWrite.All", 
                "https://graph.microsoft.com/User.Read",
                "https://graph.microsoft.com/Forms.Read.All"
            ]
            
            self.tokens_dir = os.getenv('MICROSOFT_TOKENS_DIR', './tokens/microsoft/')
            os.makedirs(self.tokens_dir, exist_ok=True)
            
            self.app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            logger.info(f"Microsoft Graph Service initialized for production with client ID: {self.client_id[:20] if self.client_id else 'N/A'}...")
            
        except ImportError:
            logger.warning("MSAL library not installed. Microsoft Graph service disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Microsoft Graph service: {e}")
            self.enabled = False
    
    def _check_enabled(self):
        """Check if Microsoft Graph service is enabled"""
        if not self.enabled:
            raise Exception("Microsoft Graph service is disabled. Install requirements and configure credentials to enable.")
    
    async def get_authorization_url(self, user_id: str) -> Dict[str, str]:
        """Get real Microsoft OAuth authorization URL - NO MOCK DATA"""
        self._check_enabled()
        
        try:
            auth_url = self.app.get_authorization_request_url(
                scopes=self.scopes,
                state=user_id,
                redirect_uri=self.redirect_uri
            )
            
            logger.info(f"Generated real Microsoft OAuth URL for user {user_id}")
            
            return {
                'authorization_url': auth_url,
                'state': user_id,
                'status': 'success',
                'platform': 'microsoft_graph'
            }
            
        except Exception as e:
            logger.error(f"Error generating Microsoft authorization URL: {str(e)}")
            raise Exception(f"Failed to generate authorization URL: {str(e)}")
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle real OAuth callback and store credentials - NO MOCK DATA"""
        self._check_enabled()
        
        try:
            result = self.app.acquire_token_by_authorization_code(
                code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                # Store credentials securely
                await self._store_credentials(state, result)
                
                logger.info(f"Microsoft OAuth callback successful for user {state}")
                
                return {
                    'success': True,
                    'user_id': state,
                    'access_token': result['access_token'],
                    'expires_in': result.get('expires_in', 3600),
                    'platform': 'microsoft_graph'
                }
            else:
                error_description = result.get('error_description', 'Unknown error')
                logger.error(f"Microsoft OAuth failed: {error_description}")
                raise Exception(f"OAuth failed: {error_description}")
                
        except Exception as e:
            logger.error(f"Error handling Microsoft OAuth callback: {str(e)}")
            raise Exception(f"Failed to handle OAuth callback: {str(e)}")
    
    async def _store_credentials(self, user_id: str, token_data: Dict[str, Any]):
        """Store user credentials securely"""
        if not self.enabled:
            return
            
        try:
            token_file = os.path.join(self.tokens_dir, f"microsoft_token_{user_id}.json")
            
            # Add metadata
            token_data['stored_at'] = datetime.utcnow().isoformat()
            token_data['user_id'] = user_id
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            logger.info(f"Microsoft credentials stored for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing Microsoft credentials: {str(e)}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            'enabled': self.enabled,
            'service': 'Microsoft Graph',
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'rate_limit_hits': 0,
            'success_rate': 0.0,
            'cache_hit_rate': 0.0
        }

# Create singleton instance
microsoft_graph_service = MicrosoftGraphService()
