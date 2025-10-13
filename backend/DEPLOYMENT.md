# 🚀 Production Deployment Guide

## 📋 Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt or self-signed)
- Server with at least 2GB RAM and 20GB storage

## 🔧 Step 1: Environment Setup

### 1.1 Create Production Environment File
```bash
# Copy the production environment template
cp env.production .env.production

# Edit with your actual values
nano .env.production
```

### 1.2 Update Critical Security Variables
```bash
# Generate secure secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# Update these in .env.production:
SECRET_KEY=your-generated-secret-key
JWT_SECRET_KEY=your-generated-jwt-secret
OPENAI_API_KEY=sk-your-actual-openai-key
```

### 1.3 Configure Database
```bash
# Update PostgreSQL credentials
POSTGRES_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-secure-redis-password
```

## 🐳 Step 2: Docker Deployment

### 2.1 Build and Start Services
```bash
# Build the application
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### 2.2 Initialize Database
```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec api flask db upgrade

# Create initial admin user (if needed)
docker-compose -f docker-compose.prod.yml exec api flask create-admin
```

### 2.3 Verify Deployment
```bash
# Check health endpoint
curl https://yourdomain.com/health

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api
```

## 🔒 Step 3: SSL Configuration

### 3.1 Using Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to nginx
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
```

### 3.2 Using Self-Signed Certificates (Development)
```bash
# Generate self-signed certificate
mkdir ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

## 📊 Step 4: Monitoring Setup

### 4.1 Sentry Integration
1. Create account at [Sentry.io](https://sentry.io)
2. Create a new project for your Flask app
3. Get your DSN and add to `.env.production`
4. Restart the API service

### 4.2 Log Monitoring
```bash
# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Check specific service logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

## 🔄 Step 5: Maintenance

### 5.1 Database Backups
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U prototype_user prototype > backup_$DATE.sql
gzip backup_$DATE.sql
EOF

chmod +x backup.sh

# Run daily backup (add to crontab)
0 2 * * * /path/to/backup.sh
```

### 5.2 Application Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api flask db upgrade
```

### 5.3 Scaling
```bash
# Scale API workers
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

## 🛡️ Step 6: Security Hardening

### 6.1 Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 6.2 Regular Security Updates
```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 Step 7: Performance Optimization

### 7.1 Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_created_at ON reports(created_at);
CREATE INDEX idx_reports_status ON reports(status);
```

### 7.2 Redis Configuration
```bash
# Optimize Redis for production
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

#### 2. Celery Workers Not Processing
```bash
# Check Celery logs
docker-compose -f docker-compose.prod.yml logs celery-worker

# Restart Celery
docker-compose -f docker-compose.prod.yml restart celery-worker
```

#### 3. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew
```

#### 4. Memory Issues
```bash
# Check memory usage
docker stats

# Increase swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📞 Support

- **Logs**: Check `logs/` directory for application logs
- **Health Check**: Visit `/health` endpoint for system status
- **Monitoring**: Use Sentry for error tracking
- **Backups**: Check `backup_*.sql.gz` files for database backups

## 🔄 Maintenance Schedule

- **Daily**: Check application logs and health endpoint
- **Weekly**: Review Sentry reports and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate secrets/keys

---

**Last Updated**: July 20, 2025  
**Next Review**: August 20, 2025 