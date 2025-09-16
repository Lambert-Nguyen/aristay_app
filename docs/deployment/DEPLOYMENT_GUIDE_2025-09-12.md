# Aristay Property Management - Deployment Guide

**Date:** September 12, 2025  
**Version:** 2.0  
**Status:** Production Ready  

## Overview

This guide provides comprehensive instructions for deploying the Aristay Property Management System to production environments. The system has been thoroughly tested and is ready for production deployment.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04 LTS or later, CentOS 8+, or similar Linux distribution

**Recommended Requirements:**
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 22.04 LTS

### Software Dependencies

- **Python**: 3.13+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Nginx**: 1.18+
- **Node.js**: 18+ (for static file processing)

## Environment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.13 python3.13-venv python3.13-dev \
    postgresql postgresql-contrib redis-server nginx \
    git curl wget build-essential libpq-dev

# Install Node.js (for static file processing)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE aristay_production;
CREATE USER aristay_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE aristay_production TO aristay_user;
ALTER USER aristay_user CREATEDB;
\q
```

### 3. Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/aristay
sudo chown $USER:$USER /opt/aristay
cd /opt/aristay

# Clone repository
git clone https://github.com/your-org/aristay-app.git .

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r aristay_backend/requirements.txt

# Install additional production dependencies
pip install gunicorn psycopg2-binary redis
```

## Configuration

### 1. Environment Variables

Create production environment file:

```bash
# Create environment file
sudo nano /opt/aristay/.env.production
```

```bash
# Database Configuration
DATABASE_URL=postgresql://aristay_user:secure_password@localhost/aristay_production
DB_NAME=aristay_production
DB_USER=aristay_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
DJANGO_SETTINGS_MODULE=backend.settings_production
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SIGNING_KEY=your-jwt-signing-key-here

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Cloudinary Configuration (if using)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Sentry Configuration (for error tracking)
SENTRY_DSN=your-sentry-dsn

# Production Environment
DJANGO_ENVIRONMENT=production
```

### 2. Django Settings

Create production settings file:

```bash
# Create production settings
sudo nano /opt/aristay/aristay_backend/backend/settings_production.py
```

```python
import os
from .settings import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Static files
STATIC_ROOT = '/opt/aristay/staticfiles'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_ROOT = '/opt/aristay/media'
MEDIA_URL = '/media/'

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS (uncomment when SSL is configured)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/opt/aristay/logs/django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
    },
}
```

### 3. Gunicorn Configuration

Create Gunicorn configuration:

```bash
# Create Gunicorn config
sudo nano /opt/aristay/gunicorn.conf.py
```

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "www-data"
group = "www-data"
tmp_upload_dir = None
```

## Database Migration

### 1. Run Migrations

```bash
# Activate virtual environment
cd /opt/aristay
source venv/bin/activate

# Set environment
export DJANGO_SETTINGS_MODULE=backend.settings_production

# Run migrations
python aristay_backend/manage.py migrate

# Create superuser
python aristay_backend/manage.py createsuperuser

# Collect static files
python aristay_backend/manage.py collectstatic --noinput
```

### 2. Load Initial Data

```bash
# Load initial data (if available)
python aristay_backend/manage.py loaddata initial_data.json

# Create initial task groups
python aristay_backend/manage.py assign_task_groups --auto-assign
```

## Web Server Configuration

### 1. Nginx Configuration

Create Nginx configuration:

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/aristay
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com api.yourdomain.com;

    # Redirect HTTP to HTTPS (uncomment when SSL is configured)
    # return 301 https://$server_name$request_uri;

    # Static files
    location /static/ {
        alias /opt/aristay/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/aristay/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # API and admin
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}

# HTTPS configuration (uncomment when SSL is configured)
# server {
#     listen 443 ssl http2;
#     server_name yourdomain.com www.yourdomain.com api.yourdomain.com;
#
#     ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
#     ssl_prefer_server_ciphers off;
#
#     # Same location blocks as HTTP
# }
```

Enable the site:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/aristay /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Service Configuration

### 1. Gunicorn Service

Create systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/aristay.service
```

```ini
[Unit]
Description=Aristay Property Management Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/aristay
Environment="PATH=/opt/aristay/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=backend.settings_production"
ExecStart=/opt/aristay/venv/bin/gunicorn --config gunicorn.conf.py backend.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aristay
sudo systemctl start aristay
sudo systemctl status aristay
```

### 2. Redis Service

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3. PostgreSQL Service

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Monitoring and Logging

### 1. Log Configuration

Create log directory:

```bash
# Create log directory
sudo mkdir -p /opt/aristay/logs
sudo chown www-data:www-data /opt/aristay/logs
```

### 2. Log Rotation

Create logrotate configuration:

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/aristay
```

```
/opt/aristay/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload aristay
    endscript
}
```

### 3. Health Checks

Create health check script:

```bash
# Create health check script
sudo nano /opt/aristay/health_check.sh
```

```bash
#!/bin/bash

# Check if Gunicorn is running
if ! systemctl is-active --quiet aristay; then
    echo "ERROR: Aristay service is not running"
    exit 1
fi

# Check if database is accessible
cd /opt/aristay
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=backend.settings_production
if ! python aristay_backend/manage.py check --deploy; then
    echo "ERROR: Django health check failed"
    exit 1
fi

# Check if Redis is accessible
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis is not accessible"
    exit 1
fi

echo "OK: All health checks passed"
exit 0
```

Make executable:

```bash
sudo chmod +x /opt/aristay/health_check.sh
```

## Backup Strategy

### 1. Database Backup

Create backup script:

```bash
# Create backup script
sudo nano /opt/aristay/backup_db.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/opt/aristay/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aristay_db_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U aristay_user aristay_production > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "aristay_db_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

### 2. Media Files Backup

```bash
# Create media backup script
sudo nano /opt/aristay/backup_media.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/opt/aristay/backups"
DATE=$(date +%Y%m%d_%H%M%S)
MEDIA_BACKUP="$BACKUP_DIR/media_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create media backup
tar -czf $MEDIA_BACKUP -C /opt/aristay media/

# Remove backups older than 30 days
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +30 -delete

echo "Media backup completed: $MEDIA_BACKUP"
```

### 3. Automated Backups

Add to crontab:

```bash
# Edit crontab
sudo crontab -e
```

```bash
# Daily database backup at 2 AM
0 2 * * * /opt/aristay/backup_db.sh

# Daily media backup at 3 AM
0 3 * * * /opt/aristay/backup_media.sh

# Weekly full backup on Sunday at 1 AM
0 1 * * 0 /opt/aristay/backup_db.sh && /opt/aristay/backup_media.sh
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2Ban Configuration

```bash
# Install Fail2Ban
sudo apt install fail2ban

# Create custom jail
sudo nano /etc/fail2ban/jail.d/aristay.conf
```

```ini
[aristay]
enabled = true
port = http,https
filter = aristay
logpath = /opt/aristay/logs/django.log
maxretry = 5
bantime = 3600
findtime = 600
```

### 3. Regular Security Updates

```bash
# Create security update script
sudo nano /opt/aristay/security_update.sh
```

```bash
#!/bin/bash

# Update system packages
apt update && apt upgrade -y

# Update Python packages
cd /opt/aristay
source venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r aristay_backend/requirements.txt

# Restart services
systemctl restart aristay
systemctl restart nginx

echo "Security updates completed"
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check service status
   sudo systemctl status aristay
   
   # Check logs
   sudo journalctl -u aristay -f
   ```

2. **Database connection issues**
   ```bash
   # Test database connection
   sudo -u postgres psql -c "SELECT 1;"
   
   # Check Django database connection
   cd /opt/aristay
   source venv/bin/activate
   python aristay_backend/manage.py dbshell
   ```

3. **Static files not loading**
   ```bash
   # Recollect static files
   python aristay_backend/manage.py collectstatic --noinput
   
   # Check Nginx configuration
   sudo nginx -t
   ```

4. **Permission issues**
   ```bash
   # Fix ownership
   sudo chown -R www-data:www-data /opt/aristay
   sudo chmod -R 755 /opt/aristay
   ```

### Performance Monitoring

1. **System Resources**
   ```bash
   # Check system resources
   htop
   df -h
   free -h
   ```

2. **Application Performance**
   ```bash
   # Check Gunicorn processes
   ps aux | grep gunicorn
   
   # Check database connections
   sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
   ```

## Maintenance

### Regular Maintenance Tasks

1. **Daily**
   - Check service status
   - Monitor log files
   - Verify backups

2. **Weekly**
   - Review security logs
   - Check disk space
   - Update dependencies

3. **Monthly**
   - Security updates
   - Performance review
   - Backup verification

### Update Procedure

1. **Backup current version**
2. **Pull latest changes**
3. **Update dependencies**
4. **Run migrations**
5. **Test functionality**
6. **Deploy to production**

## Support

For deployment support:

- **Documentation**: https://docs.aristay.com/deployment
- **Support Email**: deployment-support@aristay.com
- **Emergency Contact**: +1-555-ARISTAY

---
*Deployment Guide generated on September 12, 2025*  
*Version: 2.0*  
*Status: Production Ready*
