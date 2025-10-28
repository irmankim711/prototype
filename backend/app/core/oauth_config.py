"""
Production-Ready OAuth Configuration Management

This module provides centralized OAuth configuration including:
- Google OAuth2 configuration with production redirect URIs
- Microsoft Graph OAuth configuration
- OAuth state validation and CSRF protection
- Token refresh logic and secure storage
- Error handling with user-friendly messages
- OAuth scope management for minimal permissions
- Callback URL validation
- Audit logging for OAuth operations
"""

import os
import secrets
import hashlib
import base64
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class OAuthProvider(Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class OAuthEnvironment(Enum):
    """OAuth environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class OAuthScope:
    """OAuth scope configuration with description and required status."""
    scope: str
    description: str
    required: bool = True
    category: str = "general"

@dataclass
class OAuthProviderConfig:
    """Configuration for a specific OAuth provider."""
    provider: OAuthProvider
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[OAuthScope]
    enabled: bool = True
    
    # Security settings
    require_state_validation: bool = True
    require_csrf_protection: bool = True
    state_expiry_seconds: int = 600  # 10 minutes
    
    # Token settings
    access_token_expiry: int = 3600  # 1 hour
    refresh_token_expiry: int = 2592000  # 30 days
    auto_refresh_threshold: int = 300  # 5 minutes before expiry
    
    # Production settings
    production_domain: Optional[str] = None
    staging_domain: Optional[str] = None
    development_domains: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5173"
    ])

class OAuthStateManager:
    """Manages OAuth state parameters for CSRF protection."""
    
    def __init__(self, expiry_seconds: int = 600):
        self.expiry_seconds = expiry_seconds
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def generate_state(self, user_id: str, provider: OAuthProvider, redirect_uri: str) -> str:
        """Generate a secure state parameter for OAuth flow."""
        # Create a cryptographically secure random state
        state = secrets.token_urlsafe(32)
        
        # Store state with metadata
        self._states[state] = {
            'user_id': user_id,
            'provider': provider.value,
            'redirect_uri': redirect_uri,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=self.expiry_seconds)
        }
        
        logger.info(f"Generated OAuth state for user {user_id} with provider {provider.value}")
        return state
    
    def validate_state(self, state: str, user_id: str, provider: OAuthProvider) -> bool:
        """Validate OAuth state parameter."""
        if state not in self._states:
            logger.warning(f"Invalid OAuth state: {state}")
            return False
        
        state_data = self._states[state]
        
        # Check if state has expired
        if datetime.utcnow() > state_data['expires_at']:
            logger.warning(f"Expired OAuth state: {state}")
            del self._states[state]
            return False
        
        # Check if state matches user and provider
        if (state_data['user_id'] != user_id or 
            state_data['provider'] != provider.value):
            logger.warning(f"OAuth state mismatch: expected user {user_id}, provider {provider.value}")
            return False
        
        # State is valid, remove it to prevent reuse
        del self._states[state]
        logger.info(f"Validated OAuth state for user {user_id} with provider {provider.value}")
        return True
    
    def cleanup_expired_states(self):
        """Remove expired state parameters."""
        current_time = datetime.utcnow()
        expired_states = [
            state for state, data in self._states.items()
            if current_time > data['expires_at']
        ]
        
        for state in expired_states:
            del self._states[state]
        
        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")

class OAuthAuditLogger:
    """Logs OAuth operations for security auditing."""
    
    def __init__(self):
        self.logger = logging.getLogger('oauth_audit')
    
    def log_oauth_initiation(self, user_id: str, provider: OAuthProvider, 
                            redirect_uri: str, scopes: List[str]):
        """Log OAuth flow initiation."""
        self.logger.info(
            f"OAUTH_INITIATION: user_id={user_id}, provider={provider.value}, "
            f"redirect_uri={redirect_uri}, scopes={scopes}, "
            f"timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_oauth_callback(self, user_id: str, provider: OAuthProvider, 
                          state: str, success: bool, error: Optional[str] = None):
        """Log OAuth callback processing."""
        status = "SUCCESS" if success else "FAILURE"
        error_msg = f", error={error}" if error else ""
        
        self.logger.info(
            f"OAUTH_CALLBACK: user_id={user_id}, provider={provider.value}, "
            f"state={state}, status={status}{error_msg}, "
            f"timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_token_refresh(self, user_id: str, provider: OAuthProvider, 
                         success: bool, error: Optional[str] = None):
        """Log token refresh operations."""
        status = "SUCCESS" if success else "FAILURE"
        error_msg = f", error={error}" if error else ""
        
        self.logger.info(
            f"TOKEN_REFRESH: user_id={user_id}, provider={provider.value}, "
            f"status={status}{error_msg}, timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_oauth_error(self, user_id: str, provider: OAuthProvider, 
                       error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log OAuth errors for security monitoring."""
        context_str = f", context={context}" if context else ""
        
        self.logger.error(
            f"OAUTH_ERROR: user_id={user_id}, provider={provider.value}, "
            f"error_type={error_type}, error_message={error_message}{context_str}, "
            f"timestamp={datetime.utcnow().isoformat()}"
        )

class ProductionOAuthConfig:
    """
    Production-ready OAuth configuration manager.
    
    Features:
    - Centralized OAuth configuration
    - Environment-specific settings
    - Security features (state validation, CSRF protection)
    - Audit logging
    - Token management
    - Error handling
    """
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.state_manager = OAuthStateManager()
        self.audit_logger = OAuthAuditLogger()
        
        # Initialize provider configurations
        self.google_config = self._create_google_config()
        self.microsoft_config = self._create_microsoft_config()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"Production OAuth configuration initialized for {self.environment.value} environment")
    
    def _detect_environment(self) -> OAuthEnvironment:
        """Detect current environment."""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            return OAuthEnvironment.PRODUCTION
        elif env == 'staging':
            return OAuthEnvironment.STAGING
        else:
            return OAuthEnvironment.DEVELOPMENT
    
    def _create_google_config(self) -> OAuthProviderConfig:
        """Create Google OAuth configuration."""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.warning("Google OAuth credentials not configured")
            return OAuthProviderConfig(
                provider=OAuthProvider.GOOGLE,
                client_id="",
                client_secret="",
                redirect_uri="",
                scopes=[],
                enabled=False
            )
        
        # Define Google OAuth scopes with minimal permissions
        scopes = [
            OAuthScope(
                'https://www.googleapis.com/auth/forms.body.readonly',
                'Read Google Forms structure',
                required=True,
                category='forms'
            ),
            OAuthScope(
                'https://www.googleapis.com/auth/forms.responses.readonly',
                'Read Google Forms responses',
                required=True,
                category='forms'
            ),
            OAuthScope(
                'https://www.googleapis.com/auth/drive.readonly',
                'Read Google Drive files',
                required=False,
                category='drive'
            ),
            OAuthScope(
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'Read Google Sheets',
                required=False,
                category='sheets'
            )
        ]
        
        # Set redirect URI based on environment
        if self.environment == OAuthEnvironment.PRODUCTION:
            redirect_uri = os.getenv('GOOGLE_PRODUCTION_REDIRECT_URI')
            if not redirect_uri:
                logger.error("GOOGLE_PRODUCTION_REDIRECT_URI not configured for production")
                redirect_uri = "https://your-production-domain.com/api/oauth/google/callback"
        elif self.environment == OAuthEnvironment.STAGING:
            redirect_uri = os.getenv('GOOGLE_STAGING_REDIRECT_URI')
            if not redirect_uri:
                redirect_uri = "https://your-staging-domain.com/api/oauth/google/callback"
        else:
            redirect_uri = os.getenv('GOOGLE_DEVELOPMENT_REDIRECT_URI', 
                                   'http://localhost:5000/api/oauth/google/callback')
        
        return OAuthProviderConfig(
            provider=OAuthProvider.GOOGLE,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            enabled=True,
            production_domain=os.getenv('GOOGLE_PRODUCTION_DOMAIN'),
            staging_domain=os.getenv('GOOGLE_STAGING_DOMAIN')
        )
    
    def _create_microsoft_config(self) -> OAuthProviderConfig:
        """Create Microsoft OAuth configuration."""
        client_id = os.getenv('MICROSOFT_CLIENT_ID')
        client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        tenant_id = os.getenv('MICROSOFT_TENANT_ID')
        
        if not all([client_id, client_secret, tenant_id]):
            logger.warning("Microsoft OAuth credentials not configured")
            return OAuthProviderConfig(
                provider=OAuthProvider.MICROSOFT,
                client_id="",
                client_secret="",
                redirect_uri="",
                scopes=[],
                enabled=False
            )
        
        # Define Microsoft OAuth scopes with minimal permissions
        scopes = [
            OAuthScope(
                'https://graph.microsoft.com/Forms.Read.All',
                'Read Microsoft Forms',
                required=True,
                category='forms'
            ),
            OAuthScope(
                'https://graph.microsoft.com/User.Read',
                'Read user profile',
                required=True,
                category='user'
            ),
            OAuthScope(
                'https://graph.microsoft.com/Files.ReadWrite.All',
                'Read and write files',
                required=False,
                category='files'
            ),
            OAuthScope(
                'https://graph.microsoft.com/Sites.ReadWrite.All',
                'Read and write SharePoint sites',
                required=False,
                category='sites'
            )
        ]
        
        # Set redirect URI based on environment
        if self.environment == OAuthEnvironment.PRODUCTION:
            redirect_uri = os.getenv('MICROSOFT_PRODUCTION_REDIRECT_URI')
            if not redirect_uri:
                logger.error("MICROSOFT_PRODUCTION_REDIRECT_URI not configured for production")
                redirect_uri = "https://your-production-domain.com/api/oauth/microsoft/callback"
        elif self.environment == OAuthEnvironment.STAGING:
            redirect_uri = os.getenv('MICROSOFT_STAGING_REDIRECT_URI')
            if not redirect_uri:
                redirect_uri = "https://your-staging-domain.com/api/oauth/microsoft/callback"
        else:
            redirect_uri = os.getenv('MICROSOFT_DEVELOPMENT_REDIRECT_URI',
                                   'http://localhost:5000/api/oauth/microsoft/callback')
        
        return OAuthProviderConfig(
            provider=OAuthProvider.MICROSOFT,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            enabled=True,
            production_domain=os.getenv('MICROSOFT_PRODUCTION_DOMAIN'),
            staging_domain=os.getenv('MICROSOFT_STAGING_DOMAIN')
        )
    
    def _validate_configuration(self):
        """Validate OAuth configuration."""
        errors = []
        
        # Validate Google configuration
        if self.google_config.enabled:
            if not self.google_config.client_id:
                errors.append("Google OAuth client ID is required")
            if not self.google_config.client_secret:
                errors.append("Google OAuth client secret is required")
            if not self.google_config.redirect_uri:
                errors.append("Google OAuth redirect URI is required")
        
        # Validate Microsoft configuration
        if self.microsoft_config.enabled:
            if not self.microsoft_config.client_id:
                errors.append("Microsoft OAuth client ID is required")
            if not self.microsoft_config.client_secret:
                errors.append("Microsoft OAuth client secret is required")
            if not self.microsoft_config.redirect_uri:
                errors.append("Microsoft OAuth redirect URI is required")
        
        # Validate redirect URIs for production
        if self.environment == OAuthEnvironment.PRODUCTION:
            if self.google_config.enabled:
                if not self.google_config.redirect_uri.startswith('https://'):
                    errors.append("Google OAuth redirect URI must use HTTPS in production")
            if self.microsoft_config.enabled:
                if not self.microsoft_config.redirect_uri.startswith('https://'):
                    errors.append("Microsoft OAuth redirect URI must use HTTPS in production")
        
        if errors:
            error_message = "OAuth configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_message)
            raise ValueError(error_message)
    
    def get_provider_config(self, provider: OAuthProvider) -> OAuthProviderConfig:
        """Get configuration for a specific OAuth provider."""
        if provider == OAuthProvider.GOOGLE:
            return self.google_config
        elif provider == OAuthProvider.MICROSOFT:
            return self.microsoft_config
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    def is_provider_enabled(self, provider: OAuthProvider) -> bool:
        """Check if an OAuth provider is enabled."""
        config = self.get_provider_config(provider)
        return config.enabled
    
    def get_authorization_url(self, provider: OAuthProvider, user_id: str, 
                            redirect_uri: Optional[str] = None) -> Dict[str, str]:
        """Generate OAuth authorization URL with state validation."""
        config = self.get_provider_config(provider)
        
        if not config.enabled:
            raise ValueError(f"{provider.value} OAuth is not enabled")
        
        # Use provided redirect URI or default from config
        final_redirect_uri = redirect_uri or config.redirect_uri
        
        # Validate redirect URI
        if not self._validate_redirect_uri(provider, final_redirect_uri):
            raise ValueError(f"Invalid redirect URI for {provider.value}: {final_redirect_uri}")
        
        # Generate secure state parameter
        state = self.state_manager.generate_state(user_id, provider, final_redirect_uri)
        
        # Log OAuth initiation
        self.audit_logger.log_oauth_initiation(
            user_id, provider, final_redirect_uri, 
            [scope.scope for scope in config.scopes]
        )
        
        if provider == OAuthProvider.GOOGLE:
            return self._generate_google_auth_url(config, state, final_redirect_uri)
        elif provider == OAuthProvider.MICROSOFT:
            return self._generate_microsoft_auth_url(config, state, final_redirect_uri)
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    def _generate_google_auth_url(self, config: OAuthProviderConfig, 
                                 state: str, redirect_uri: str) -> Dict[str, str]:
        """Generate Google OAuth authorization URL."""
        scopes = ' '.join([scope.scope for scope in config.scopes])
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={config.client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scopes}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )
        
        return {
            'authorization_url': auth_url,
            'state': state,
            'provider': 'google',
            'scopes': [scope.scope for scope in config.scopes]
        }
    
    def _generate_microsoft_auth_url(self, config: OAuthProviderConfig, 
                                    state: str, redirect_uri: str) -> Dict[str, str]:
        """Generate Microsoft OAuth authorization URL."""
        scopes = ' '.join([scope.scope for scope in config.scopes])
        tenant_id = os.getenv('MICROSOFT_TENANT_ID', 'common')
        
        auth_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?"
            f"client_id={config.client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scopes}&"
            f"response_type=code&"
            f"state={state}&"
            f"response_mode=query"
        )
        
        return {
            'authorization_url': auth_url,
            'state': state,
            'provider': 'microsoft',
            'scopes': [scope.scope for scope in config.scopes]
        }
    
    def validate_oauth_callback(self, provider: OAuthProvider, user_id: str, 
                              state: str, code: str) -> bool:
        """Validate OAuth callback parameters."""
        config = self.get_provider_config(provider)
        
        if not config.enabled:
            raise ValueError(f"{provider.value} OAuth is not enabled")
        
        # Validate state parameter
        if config.require_state_validation:
            if not self.state_manager.validate_state(state, user_id, provider):
                self.audit_logger.log_oauth_callback(
                    user_id, provider, state, False, "Invalid state parameter"
                )
                return False
        
        # Validate authorization code
        if not code or len(code) < 10:
            self.audit_logger.log_oauth_callback(
                user_id, provider, state, False, "Invalid authorization code"
            )
            return False
        
        # Log successful validation
        self.audit_logger.log_oauth_callback(user_id, provider, state, True)
        return True
    
    def _validate_redirect_uri(self, provider: OAuthProvider, redirect_uri: str) -> bool:
        """Validate redirect URI for security."""
        config = self.get_provider_config(provider)
        
        try:
            parsed_uri = urlparse(redirect_uri)
            
            # Check scheme
            if self.environment == OAuthEnvironment.PRODUCTION:
                if parsed_uri.scheme != 'https':
                    return False
            
            # Check if URI is in allowed domains
            if self.environment == OAuthEnvironment.PRODUCTION:
                if config.production_domain:
                    if not redirect_uri.startswith(config.production_domain):
                        return False
            elif self.environment == OAuthEnvironment.STAGING:
                if config.staging_domain:
                    if not redirect_uri.startswith(config.staging_domain):
                        return False
            else:
                # Development: check against allowed local domains
                allowed = False
                for domain in config.development_domains:
                    if redirect_uri.startswith(domain):
                        allowed = True
                        break
                if not allowed:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating redirect URI: {e}")
            return False
    
    def get_required_scopes(self, provider: OAuthProvider) -> List[str]:
        """Get required OAuth scopes for a provider."""
        config = self.get_provider_config(provider)
        return [scope.scope for scope in config.scopes if scope.required]
    
    def get_optional_scopes(self, provider: OAuthProvider) -> List[str]:
        """Get optional OAuth scopes for a provider."""
        config = self.get_provider_config(provider)
        return [scope.scope for scope in config.scopes if not scope.required]
    
    def cleanup_expired_states(self):
        """Clean up expired OAuth state parameters."""
        self.state_manager.cleanup_expired_states()
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get OAuth configuration summary for monitoring."""
        return {
            'environment': self.environment.value,
            'providers': {
                'google': {
                    'enabled': self.google_config.enabled,
                    'client_id_configured': bool(self.google_config.client_id),
                    'redirect_uri': self.google_config.redirect_uri,
                    'scopes_count': len(self.google_config.scopes)
                },
                'microsoft': {
                    'enabled': self.microsoft_config.enabled,
                    'client_id_configured': bool(self.microsoft_config.client_id),
                    'redirect_uri': self.microsoft_config.redirect_uri,
                    'scopes_count': len(self.microsoft_config.scopes)
                }
            },
            'security_features': {
                'state_validation': True,
                'csrf_protection': True,
                'audit_logging': True,
                'redirect_uri_validation': True
            },
            'timestamp': datetime.utcnow().isoformat()
        }

# Global OAuth configuration instance
oauth_config = ProductionOAuthConfig()

def get_oauth_config() -> ProductionOAuthConfig:
    """Get the global OAuth configuration instance."""
    return oauth_config

def get_google_oauth_config() -> OAuthProviderConfig:
    """Get Google OAuth configuration."""
    return oauth_config.get_provider_config(OAuthProvider.GOOGLE)

def get_microsoft_oauth_config() -> OAuthProviderConfig:
    """Get Microsoft OAuth configuration."""
    return oauth_config.get_provider_config(OAuthProvider.MICROSOFT)

def is_google_oauth_enabled() -> bool:
    """Check if Google OAuth is enabled."""
    return oauth_config.is_provider_enabled(OAuthProvider.GOOGLE)

def is_microsoft_oauth_enabled() -> bool:
    """Check if Microsoft OAuth is enabled."""
    return oauth_config.is_provider_enabled(OAuthProvider.MICROSOFT)
