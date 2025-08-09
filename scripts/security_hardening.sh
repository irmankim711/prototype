#!/bin/bash

# 🔐 Production Security Hardening Script
# Automates security configuration for the form automation platform

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_ROOT/ssl"
SECRETS_DIR="$PROJECT_ROOT/secrets"

# Main hardening function
main() {
    log "🔐 Starting production security hardening..."
    
    # Pre-flight checks
    check_prerequisites
    
    # Security configurations
    generate_ssl_certificates
    generate_secure_secrets
    configure_nginx_security
    setup_rate_limiting
    configure_database_security
    setup_aws_secrets_manager
    configure_monitoring
    setup_firewall_rules
    validate_security_config
    
    success "🛡️ Security hardening completed successfully!"
    display_security_summary
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if running as root for system configurations
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root. Some configurations will modify system settings."
    fi
    
    # Check required tools
    local tools=("openssl" "docker" "aws")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        error "Docker Compose v2 is required"
        exit 1
    fi
    
    success "All prerequisites met"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log "🔒 Generating SSL certificates..."
    
    mkdir -p "$SSL_DIR"
    
    if [[ ! -f "$SSL_DIR/cert.pem" ]]; then
        # Generate self-signed certificate for development/testing
        # In production, use Let's Encrypt or proper CA certificates
        openssl req -x509 -newkey rsa:4096 -keyout "$SSL_DIR/key.pem" \
            -out "$SSL_DIR/cert.pem" -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        # Set proper permissions
        chmod 600 "$SSL_DIR/key.pem"
        chmod 644 "$SSL_DIR/cert.pem"
        
        success "SSL certificates generated"
    else
        log "SSL certificates already exist"
    fi
    
    # Validate certificate
    if openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -q "Signature Algorithm"; then
        success "SSL certificate is valid"
    else
        error "SSL certificate validation failed"
        exit 1
    fi
}

# Generate secure secrets
generate_secure_secrets() {
    log "🔑 Generating secure secrets..."
    
    mkdir -p "$SECRETS_DIR"
    
    # Generate secure random secrets
    local secret_key=$(openssl rand -hex 32)
    local jwt_secret=$(openssl rand -hex 32)
    local postgres_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local redis_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Create secrets file
    cat > "$SECRETS_DIR/production.env" << EOF
# Generated secrets for production - $(date)
SECRET_KEY=$secret_key
JWT_SECRET_KEY=$jwt_secret
POSTGRES_PASSWORD=$postgres_password
REDIS_PASSWORD=$redis_password
EOF
    
    # Set restrictive permissions
    chmod 600 "$SECRETS_DIR/production.env"
    
    success "Secure secrets generated in $SECRETS_DIR/production.env"
    warning "IMPORTANT: Store these secrets securely and never commit to version control!"
}

# Configure Nginx security
configure_nginx_security() {
    log "🌐 Configuring Nginx security..."
    
    # Update nginx.conf with security headers
    cat > "$PROJECT_ROOT/backend/nginx.prod.conf" << 'EOF'
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' wss: https:" always;

    # Hide Nginx version
    server_tokens off;

    # Logging
    log_format secure '$remote_addr - $remote_user [$time_local] '
                     '"$request" $status $bytes_sent '
                     '"$http_referer" "$http_user_agent" '
                     '"$http_x_forwarded_for" "$request_time"';

    access_log /var/log/nginx/access.log secure;
    error_log /var/log/nginx/error.log warn;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 16M;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;

    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=perip:10m;
    limit_conn_zone $server_name zone=perserver:10m;

    # Upstream backend
    upstream api_backend {
        least_conn;
        server api:5000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1h;
        ssl_session_tickets off;

        # OCSP Stapling
        ssl_stapling on;
        ssl_stapling_verify on;

        # Connection limits
        limit_conn perip 10;
        limit_conn perserver 100;

        # Security-specific locations
        location /api/auth/ {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }

        location /api/ {
            limit_req zone=api burst=10 nodelay;
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }

        location / {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }

        # Security-related blocks
        location ~ /\.(ht|git) {
            deny all;
        }

        location ~* \.(sql|log|tar|gz)$ {
            deny all;
        }
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$server_name$request_uri;
    }
}
EOF

    success "Nginx security configuration updated"
}

# Setup rate limiting
setup_rate_limiting() {
    log "🚦 Setting up advanced rate limiting..."
    
    # Create rate limiting configuration for Flask app
    cat > "$PROJECT_ROOT/backend/rate_limit_config.py" << 'EOF'
"""
Advanced Rate Limiting Configuration
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request
import redis
import os

# Redis connection for distributed rate limiting
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

def get_user_id():
    """Get user ID from JWT token for user-specific rate limiting"""
    from flask_jwt_extended import get_jwt_identity, jwt_required
    try:
        return get_jwt_identity() or get_remote_address(request)
    except:
        return get_remote_address(request)

# Rate limiting configurations
RATE_LIMIT_CONFIG = {
    'default': "1000 per hour",
    'auth': {
        'login': "5 per minute",
        'register': "3 per minute", 
        'reset_password': "2 per minute"
    },
    'api': {
        'general': "300 per hour",
        'upload': "10 per hour",
        'download': "50 per hour",
        'report_generation': "20 per hour"
    },
    'admin': {
        'general': "500 per hour",
        'bulk_operations': "5 per hour"
    }
}

def create_limiter(app):
    """Create and configure rate limiter"""
    return Limiter(
        app,
        key_func=get_user_id,
        storage_uri=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        default_limits=[RATE_LIMIT_CONFIG['default']],
        strategy="moving-window"
    )
EOF

    success "Rate limiting configuration created"
}

# Configure database security
configure_database_security() {
    log "🗄️ Configuring database security..."
    
    # Create PostgreSQL security configuration
    cat > "$PROJECT_ROOT/backend/postgresql.conf.security" << 'EOF'
# PostgreSQL Security Configuration

# Connection settings
listen_addresses = 'localhost'
port = 5432
max_connections = 100

# SSL settings
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_min_protocol_version = 'TLSv1.2'

# Authentication
password_encryption = scram-sha-256

# Logging
log_statement = 'mod'
log_min_messages = warning
log_min_error_statement = error
log_min_duration_statement = 1000
log_connections = on
log_disconnections = on
log_duration = on

# Security
shared_preload_libraries = 'pg_stat_statements'
EOF

    # Create database initialization script with security
    cat > "$PROJECT_ROOT/backend/init_secure_db.sql" << 'EOF'
-- Secure database initialization

-- Create application user with limited privileges
CREATE USER app_user WITH ENCRYPTED PASSWORD 'CHANGE_THIS_PASSWORD';

-- Create read-only user for reporting
CREATE USER readonly_user WITH ENCRYPTED PASSWORD 'CHANGE_THIS_PASSWORD';

-- Grant specific privileges
GRANT CONNECT ON DATABASE prototype TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Read-only access for reporting user
GRANT CONNECT ON DATABASE prototype TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Revoke dangerous privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON pg_user FROM PUBLIC;
EOF

    success "Database security configuration created"
}

# Setup AWS Secrets Manager
setup_aws_secrets_manager() {
    log "☁️ Setting up AWS Secrets Manager integration..."
    
    # Create AWS secrets management script
    cat > "$PROJECT_ROOT/backend/aws_secrets.py" << 'EOF'
"""
AWS Secrets Manager Integration
Securely manages production secrets
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

class AWSSecretsManager:
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client(
            'secretsmanager',
            region_name=region_name
        )
    
    def get_secret(self, secret_name):
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret = response['SecretString']
            return json.loads(secret)
        except ClientError as e:
            print(f"Error retrieving secret {secret_name}: {e}")
            return None
    
    def create_secret(self, secret_name, secret_value, description=""):
        """Create a new secret in AWS Secrets Manager"""
        try:
            response = self.client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
                Description=description
            )
            return response['ARN']
        except ClientError as e:
            print(f"Error creating secret {secret_name}: {e}")
            return None
    
    def update_secret(self, secret_name, secret_value):
        """Update existing secret"""
        try:
            response = self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            return response['ARN']
        except ClientError as e:
            print(f"Error updating secret {secret_name}: {e}")
            return None

def load_secrets_from_aws():
    """Load all application secrets from AWS"""
    if not os.getenv('USE_AWS_SECRETS', '').lower() == 'true':
        return {}
    
    secrets_manager = AWSSecretsManager(
        region_name=os.getenv('AWS_SECRETS_REGION', 'us-east-1')
    )
    
    secret_name = os.getenv('SECRET_ARN', 'production/form-automation/secrets')
    secrets = secrets_manager.get_secret(secret_name)
    
    if secrets:
        # Update environment variables
        for key, value in secrets.items():
            os.environ[key] = value
        print(f"Loaded {len(secrets)} secrets from AWS Secrets Manager")
    
    return secrets or {}

# Example usage in Flask app initialization
def configure_app_secrets(app):
    """Configure Flask app with AWS secrets"""
    secrets = load_secrets_from_aws()
    
    if secrets:
        app.config.update({
            'SECRET_KEY': secrets.get('SECRET_KEY'),
            'JWT_SECRET_KEY': secrets.get('JWT_SECRET_KEY'),
            'DATABASE_URL': secrets.get('DATABASE_URL'),
            'OPENAI_API_KEY': secrets.get('OPENAI_API_KEY'),
            'SENDGRID_API_KEY': secrets.get('SENDGRID_API_KEY')
        })
EOF

    success "AWS Secrets Manager integration configured"
}

# Configure monitoring
configure_monitoring() {
    log "📊 Configuring security monitoring..."
    
    # Create security monitoring configuration
    cat > "$PROJECT_ROOT/backend/security_monitoring.py" << 'EOF'
"""
Security Monitoring and Alerting
"""

import logging
import json
from datetime import datetime, timedelta
from collections import defaultdict
import redis
from flask import request, g
import sentry_sdk

# Security event types
SECURITY_EVENTS = {
    'FAILED_LOGIN': 'failed_login',
    'RATE_LIMIT_EXCEEDED': 'rate_limit_exceeded',
    'SUSPICIOUS_REQUEST': 'suspicious_request',
    'ADMIN_ACCESS': 'admin_access',
    'DATA_EXPORT': 'data_export',
    'FILE_UPLOAD': 'file_upload',
    'SQL_INJECTION_ATTEMPT': 'sql_injection_attempt'
}

class SecurityMonitor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logging.getLogger('security')
    
    def log_security_event(self, event_type, user_id=None, ip_address=None, details=None):
        """Log security event for monitoring"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address or request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'details': details or {}
        }
        
        # Log to file
        self.logger.warning(f"Security Event: {json.dumps(event)}")
        
        # Send to Sentry for alerting
        sentry_sdk.capture_message(
            f"Security Event: {event_type}",
            level='warning',
            extra=event
        )
        
        # Store in Redis for real-time monitoring
        key = f"security_events:{event_type}:{datetime.utcnow().strftime('%Y%m%d')}"
        self.redis.lpush(key, json.dumps(event))
        self.redis.expire(key, 86400 * 7)  # Keep for 7 days
    
    def check_failed_logins(self, ip_address, user_id=None):
        """Check for failed login attempts"""
        key = f"failed_logins:{ip_address}"
        attempts = self.redis.get(key)
        
        if attempts and int(attempts) >= 5:
            self.log_security_event(
                SECURITY_EVENTS['FAILED_LOGIN'],
                user_id=user_id,
                ip_address=ip_address,
                details={'attempts': int(attempts)}
            )
            return True
        return False
    
    def record_failed_login(self, ip_address, user_id=None):
        """Record failed login attempt"""
        key = f"failed_logins:{ip_address}"
        self.redis.incr(key)
        self.redis.expire(key, 300)  # 5 minutes
    
    def check_suspicious_patterns(self, request):
        """Check for suspicious request patterns"""
        suspicious_patterns = [
            'union select',
            'drop table',
            'script>',
            '../',
            'eval(',
            'base64_decode'
        ]
        
        request_data = str(request.get_data()).lower()
        for pattern in suspicious_patterns:
            if pattern in request_data:
                self.log_security_event(
                    SECURITY_EVENTS['SUSPICIOUS_REQUEST'],
                    details={'pattern': pattern, 'data': request_data[:200]}
                )
                return True
        return False

def setup_security_monitoring(app):
    """Setup security monitoring middleware"""
    redis_client = redis.Redis.from_url(app.config['REDIS_URL'])
    monitor = SecurityMonitor(redis_client)
    
    @app.before_request
    def security_check():
        g.security_monitor = monitor
        
        # Check for suspicious patterns
        if monitor.check_suspicious_patterns(request):
            # Could block request here
            pass
EOF

    success "Security monitoring configured"
}

# Setup firewall rules
setup_firewall_rules() {
    log "🔥 Setting up firewall rules..."
    
    # Create UFW configuration script
    cat > "$PROJECT_ROOT/scripts/configure_firewall.sh" << 'EOF'
#!/bin/bash

# Configure UFW firewall for production security

# Enable UFW
ufw --force enable

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH access (be careful!)
ufw allow 22/tcp

# HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Database (only from localhost)
ufw allow from 127.0.0.1 to any port 5432

# Redis (only from localhost)
ufw allow from 127.0.0.1 to any port 6379

# Docker network
ufw allow from 172.16.0.0/12

# Rate limiting for SSH
ufw limit ssh

echo "Firewall configured successfully"
ufw status verbose
EOF

    chmod +x "$PROJECT_ROOT/scripts/configure_firewall.sh"
    
    success "Firewall configuration script created"
    warning "Run scripts/configure_firewall.sh on the production server"
}

# Validate security configuration
validate_security_config() {
    log "🔍 Validating security configuration..."
    
    local issues=0
    
    # Check SSL certificates
    if [[ ! -f "$SSL_DIR/cert.pem" ]]; then
        error "SSL certificate not found"
        ((issues++))
    fi
    
    # Check secrets file
    if [[ ! -f "$SECRETS_DIR/production.env" ]]; then
        error "Production secrets not generated"
        ((issues++))
    fi
    
    # Check file permissions
    if [[ -f "$SECRETS_DIR/production.env" ]]; then
        local perms=$(stat -c "%a" "$SECRETS_DIR/production.env")
        if [[ "$perms" != "600" ]]; then
            warning "Secrets file permissions are not secure: $perms"
        fi
    fi
    
    # Check for default passwords
    if grep -q "CHANGE" "$PROJECT_ROOT/.env.production.template"; then
        warning "Default passwords found in template - ensure they are changed in production"
    fi
    
    if [[ $issues -eq 0 ]]; then
        success "Security configuration validation passed"
    else
        error "$issues security issues found"
        return 1
    fi
}

# Display security summary
display_security_summary() {
    cat << 'EOF'

🛡️  SECURITY HARDENING COMPLETE
=====================================

✅ SSL/TLS Configuration
   - Self-signed certificates generated
   - TLS 1.2+ enforced
   - Secure cipher suites configured

✅ Secrets Management
   - Secure random secrets generated
   - AWS Secrets Manager integration ready
   - Environment variables secured

✅ Rate Limiting
   - Multi-tier rate limiting configured
   - Distributed rate limiting with Redis
   - Authentication-specific limits

✅ Database Security
   - Connection encryption enabled
   - User privilege separation
   - Query logging configured

✅ Nginx Security
   - Security headers implemented
   - Request filtering enabled
   - SSL termination configured

✅ Monitoring & Alerting
   - Security event logging
   - Sentry integration for alerts
   - Failed login tracking

🚨 NEXT STEPS:
1. Update .env.production with actual values
2. Deploy SSL certificates from proper CA
3. Configure AWS Secrets Manager
4. Set up monitoring dashboards
5. Test security configurations

⚠️  CRITICAL REMINDERS:
- Change ALL default passwords
- Use proper SSL certificates in production
- Configure backup and disaster recovery
- Regular security audits and updates
- Monitor logs for suspicious activity

EOF
}

# Execute main function
main "$@"
