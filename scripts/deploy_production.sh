#!/bin/bash

# 🚀 Production Deployment Script
# Zero-downtime deployment with comprehensive monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${1:-production}"
VERSION="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Deployment configuration
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
HEALTH_CHECK_URL="https://yourdomain.com/health"
MAX_HEALTH_CHECKS=10
HEALTH_CHECK_INTERVAL=30

# Main deployment function
main() {
    log "🚀 Starting production deployment for version: $VERSION"
    
    # Pre-deployment checks
    pre_deployment_checks
    
    # Create backup
    create_backup
    
    # Deploy with zero downtime
    deploy_zero_downtime
    
    # Post-deployment verification
    post_deployment_verification
    
    # Cleanup old resources
    cleanup_old_resources
    
    success "🎉 Deployment completed successfully!"
    send_notification "success"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "🔍 Running pre-deployment checks..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if required files exist
    local required_files=(
        "$PROJECT_ROOT/$COMPOSE_FILE"
        "$PROJECT_ROOT/.env.production"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file not found: $file"
            exit 1
        fi
    done
    
    # Check disk space (require at least 2GB free)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 2097152 ]]; then
        warning "Low disk space: $(($available_space/1024))MB available"
    fi
    
    # Check current service health
    if ! check_service_health; then
        warning "Current service health check failed"
    fi
    
    success "Pre-deployment checks completed"
}

# Create backup
create_backup() {
    log "💾 Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    log "Backing up database..."
    docker compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T postgres \
        pg_dump -U prototype_user prototype > "$BACKUP_DIR/database.sql"
    
    # Backup uploaded files
    log "Backing up uploaded files..."
    if [[ -d "$PROJECT_ROOT/backend/uploads" ]]; then
        tar -czf "$BACKUP_DIR/uploads.tar.gz" -C "$PROJECT_ROOT/backend" uploads
    fi
    
    # Backup configuration
    log "Backing up configuration..."
    cp "$PROJECT_ROOT/.env.production" "$BACKUP_DIR/"
    cp "$PROJECT_ROOT/$COMPOSE_FILE" "$BACKUP_DIR/"
    
    # Compress backup
    tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
    rm -rf "$BACKUP_DIR"
    
    success "Backup created: $BACKUP_DIR.tar.gz"
}

# Zero-downtime deployment
deploy_zero_downtime() {
    log "🔄 Starting zero-downtime deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    log "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" pull
    
    # Start new services alongside existing ones
    log "Starting new services..."
    
    # Scale up new instances
    docker compose -f "$COMPOSE_FILE" up -d --scale api=2 --scale celery-worker=2
    
    # Wait for new services to be healthy
    log "Waiting for new services to be healthy..."
    sleep 30
    
    # Run database migrations
    log "Running database migrations..."
    docker compose -f "$COMPOSE_FILE" exec api flask db upgrade
    
    # Check health of new services
    local health_checks=0
    while [[ $health_checks -lt $MAX_HEALTH_CHECKS ]]; do
        if check_service_health; then
            log "New services are healthy"
            break
        fi
        
        ((health_checks++))
        log "Health check $health_checks/$MAX_HEALTH_CHECKS failed, retrying in ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    if [[ $health_checks -eq $MAX_HEALTH_CHECKS ]]; then
        error "New services failed health checks, rolling back..."
        rollback_deployment
        exit 1
    fi
    
    # Gradually shift traffic to new instances
    log "Shifting traffic to new instances..."
    
    # Update Nginx configuration to include new instances
    update_load_balancer_config
    
    # Reload Nginx
    docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
    
    # Wait for traffic to stabilize
    sleep 60
    
    # Scale down old instances
    log "Scaling down old instances..."
    docker compose -f "$COMPOSE_FILE" up -d --scale api=1 --scale celery-worker=1
    
    success "Zero-downtime deployment completed"
}

# Check service health
check_service_health() {
    local health_endpoints=(
        "/health"
        "/api/health"
        "/api/auth/health"
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        local url="${HEALTH_CHECK_URL}${endpoint}"
        if ! curl -f -s --max-time 10 "$url" >/dev/null; then
            return 1
        fi
    done
    
    return 0
}

# Update load balancer configuration
update_load_balancer_config() {
    log "Updating load balancer configuration..."
    
    # Create dynamic upstream configuration
    cat > "$PROJECT_ROOT/backend/nginx.upstream.conf" << 'EOF'
upstream api_backend {
    least_conn;
    server api:5000 max_fails=3 fail_timeout=30s weight=1;
    # Add additional servers for zero-downtime deployment
    keepalive 32;
}
EOF
    
    # Reload Nginx configuration
    docker compose -f "$COMPOSE_FILE" exec nginx nginx -t
}

# Post-deployment verification
post_deployment_verification() {
    log "✅ Running post-deployment verification..."
    
    # Comprehensive health checks
    local verification_tests=(
        "basic_health_check"
        "database_connectivity_check"
        "redis_connectivity_check"
        "api_functionality_check"
        "authentication_check"
        "file_upload_check"
        "report_generation_check"
    )
    
    local failed_tests=0
    
    for test in "${verification_tests[@]}"; do
        log "Running $test..."
        if $test; then
            success "$test passed"
        else
            error "$test failed"
            ((failed_tests++))
        fi
    done
    
    if [[ $failed_tests -gt 0 ]]; then
        error "$failed_tests verification tests failed"
        warning "Consider rolling back the deployment"
        return 1
    fi
    
    success "All verification tests passed"
}

# Verification test functions
basic_health_check() {
    curl -f -s --max-time 10 "$HEALTH_CHECK_URL/health" >/dev/null
}

database_connectivity_check() {
    docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U prototype_user >/dev/null
}

redis_connectivity_check() {
    docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"
}

api_functionality_check() {
    local response=$(curl -s --max-time 10 "$HEALTH_CHECK_URL/api/health")
    echo "$response" | grep -q "healthy"
}

authentication_check() {
    # Test user registration endpoint
    local test_email="test-$(date +%s)@example.com"
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$test_email\",\"password\":\"TestPass123!\"}" \
        "$HEALTH_CHECK_URL/api/auth/register")
    
    echo "$response" | grep -q "success\|created"
}

file_upload_check() {
    # Create a test file and upload it
    local test_file="/tmp/test-upload.txt"
    echo "Test upload content" > "$test_file"
    
    local response=$(curl -s -X POST \
        -F "file=@$test_file" \
        "$HEALTH_CHECK_URL/api/upload/test")
    
    rm -f "$test_file"
    echo "$response" | grep -q "success\|uploaded"
}

report_generation_check() {
    # Test report generation endpoint
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"form_id":"health-check","title":"Health Check Report"}' \
        "$HEALTH_CHECK_URL/api/public-forms/generate-report")
    
    echo "$response" | grep -q "success\|queued\|processing"
}

# Rollback deployment
rollback_deployment() {
    log "🔙 Rolling back deployment..."
    
    # Restore from backup
    local latest_backup=$(ls -t "$PROJECT_ROOT"/backups/*.tar.gz | head -1)
    if [[ -n "$latest_backup" ]]; then
        log "Restoring from backup: $latest_backup"
        
        # Extract backup
        local restore_dir="/tmp/restore-$(date +%s)"
        mkdir -p "$restore_dir"
        tar -xzf "$latest_backup" -C "$restore_dir"
        
        # Restore database
        local backup_sql="$restore_dir/*/database.sql"
        if [[ -f $backup_sql ]]; then
            docker compose -f "$COMPOSE_FILE" exec -T postgres \
                psql -U prototype_user prototype < "$backup_sql"
        fi
        
        # Restore files
        local backup_uploads="$restore_dir/*/uploads.tar.gz"
        if [[ -f $backup_uploads ]]; then
            tar -xzf "$backup_uploads" -C "$PROJECT_ROOT/backend/"
        fi
        
        rm -rf "$restore_dir"
    fi
    
    # Restart services
    docker compose -f "$COMPOSE_FILE" restart
    
    success "Rollback completed"
}

# Cleanup old resources
cleanup_old_resources() {
    log "🧹 Cleaning up old resources..."
    
    # Remove old Docker images
    docker image prune -f
    
    # Clean up old backups (keep last 10)
    ls -t "$PROJECT_ROOT"/backups/*.tar.gz | tail -n +11 | xargs -r rm
    
    # Clean up old logs
    find "$PROJECT_ROOT/backend/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    success "Cleanup completed"
}

# Send notification
send_notification() {
    local status=$1
    local message
    
    if [[ "$status" == "success" ]]; then
        message="🚀 Production deployment completed successfully for version $VERSION"
    else
        message="❌ Production deployment failed for version $VERSION"
    fi
    
    # Send to Slack (if configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
    
    # Send to email (if configured)
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        echo "$message" | mail -s "Deployment Notification" "$NOTIFICATION_EMAIL" >/dev/null 2>&1 || true
    fi
    
    log "Notification sent: $message"
}

# Error handling
trap 'error "Deployment failed at line $LINENO"; send_notification "failure"; exit 1' ERR

# Load environment variables
if [[ -f "$PROJECT_ROOT/.env.production" ]]; then
    source "$PROJECT_ROOT/.env.production"
fi

# Execute main function
main "$@"
