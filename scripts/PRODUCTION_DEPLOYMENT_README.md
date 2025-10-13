# Production Deployment Guide
# ===========================

This guide explains how to securely deploy your Flask application to production using the provided scripts and configuration templates.

## 🔐 Secure Key Generation

### Quick Start

1. **Generate Production Keys:**
   ```bash
   cd /path/to/your/project
   python scripts/generate_production_keys.py
   ```

2. **Review Generated Files:**
   - `.env.production` - Contains your actual production configuration with generated keys
   - `env.production.template` - Template for future deployments

### What the Script Does

The `generate_production_keys.py` script:

- ✅ Generates cryptographically secure `SECRET_KEY` (32 bytes, URL-safe)
- ✅ Generates cryptographically secure `JWT_SECRET_KEY` (32 bytes, URL-safe)
- ✅ Creates `.env.production` with all required variables
- ✅ Sets production flags (`DEBUG=false`, `ENVIRONMENT=production`)
- ✅ Includes database URL template for PostgreSQL
- ✅ Includes Redis URL template for Celery
- ✅ Adds comprehensive comments explaining each variable

## 🚀 Deployment Process

### 1. Pre-Deployment Checklist

- [ ] Generate new production keys
- [ ] Set up PostgreSQL database
- [ ] Configure Redis instance
- [ ] Set up monitoring (Sentry)
- [ ] Configure domain and SSL certificates
- [ ] Set up backup strategy

### 2. Environment Configuration

#### Database Setup
```bash
# PostgreSQL connection string format
DATABASE_URL=postgresql://username:password@host:port/database_name

# Example for local PostgreSQL
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/myapp_prod

# Example for cloud database (AWS RDS)
DATABASE_URL=postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/database_name
```

#### Redis Setup
```bash
# Redis connection string format
CELERY_BROKER_URL=redis://[password@]host:port/db_number

# Example for local Redis
CELERY_BROKER_URL=redis://localhost:6379/0

# Example for cloud Redis (AWS ElastiCache)
CELERY_BROKER_URL=redis://your-elasticache-endpoint.amazonaws.com:6379/0
```

### 3. Security Configuration

#### CORS Origins
```bash
# Replace with your actual domains
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### Monitoring
```bash
# Sentry DSN for error tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### 4. Production Deployment

#### Using Docker (Recommended)
```bash
# Build production image
docker build -t myapp:production -f Dockerfile.prod .

# Run with environment file
docker run -d \
  --name myapp-prod \
  --env-file .env.production \
  -p 8000:8000 \
  myapp:production
```

#### Using Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/myapp.service

# Enable and start service
sudo systemctl enable myapp
sudo systemctl start myapp
```

## 🔒 Security Best Practices

### 1. Key Management
- **Never commit `.env.production` to version control**
- Generate new keys for each environment
- Rotate keys every 90 days
- Use different keys for staging and production

### 2. Database Security
- Use strong, unique passwords
- Enable SSL connections
- Restrict network access
- Regular security updates

### 3. Network Security
- Enable HTTPS with valid SSL certificates
- Configure firewall rules
- Use VPN for database access
- Monitor network traffic

### 4. Application Security
- Enable security headers
- Implement rate limiting
- Validate all inputs
- Regular security audits

## 📊 Monitoring and Maintenance

### 1. Health Checks
```bash
# Application health endpoint
curl https://yourdomain.com/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-12-19T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "database": "healthy"
}
```

### 2. Log Monitoring
```bash
# View application logs
sudo journalctl -u myapp -f

# View Celery worker logs
sudo journalctl -u celery -f
```

### 3. Performance Monitoring
- Monitor database connection pool usage
- Track Redis memory usage
- Monitor Celery task execution times
- Set up alerting for critical metrics

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database connectivity
psql "postgresql://username:password@host:port/database_name" -c "SELECT 1"

# Verify connection pool settings
# Increase DB_POOL_SIZE if needed
```

#### 2. Redis Connection Issues
```bash
# Test Redis connectivity
redis-cli -h host -p port ping

# Check Redis memory usage
redis-cli -h host -p port info memory
```

#### 3. JWT Token Issues
```bash
# Verify JWT secret key is set
echo $JWT_SECRET_KEY

# Check token expiration settings
# Adjust JWT_ACCESS_TOKEN_EXPIRES if needed
```

### Emergency Procedures

#### 1. Maintenance Mode
```bash
# Enable maintenance mode
export MAINTENANCE_MODE=true
sudo systemctl restart myapp
```

#### 2. Rollback Deployment
```bash
# Revert to previous version
git checkout previous-tag
sudo systemctl restart myapp
```

## 📚 Additional Resources

### Documentation
- [Flask Production Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Redis Security](https://redis.io/topics/security)
- [Celery Production](https://docs.celeryproject.org/en/stable/userguide/deployment.html)

### Security Tools
- [OWASP Security Checklist](https://owasp.org/www-project-top-ten/)
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)

## 🆘 Support

If you encounter issues during deployment:

1. Check the application logs
2. Verify environment configuration
3. Test connectivity to external services
4. Review security settings
5. Contact your DevOps team

---

**Remember: Security is a continuous process, not a one-time setup!**
