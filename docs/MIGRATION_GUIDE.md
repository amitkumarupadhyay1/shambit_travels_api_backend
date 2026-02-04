# Migration Guide: Pre-Production Security Hardening

## Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis (for caching, optional but recommended)
- Node.js 18+ (for frontend coordination)

## Step-by-Step Migration

### 1. Database Migration

#### Backup Current Data
```bash
# Backup current SQLite database
cp backend/db.sqlite3 backend/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
```

#### Setup PostgreSQL
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE travel_platform;
CREATE USER travel_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE travel_platform TO travel_user;
\q
```

#### Migrate Data
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://travel_user:secure_password@localhost:5432/travel_platform"

# Run migrations
python manage.py migrate

# Verify connection
python manage.py dbshell
```

### 2. Environment Configuration

#### Create Production Environment File
```bash
cp .env.example .env
```

#### Required Environment Variables
```env
# Critical - Change these values
SECRET_KEY=your-unique-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/travel_platform
RAZORPAY_KEY_ID=rzp_live_your_key_id
RAZORPAY_KEY_SECRET=your_live_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GITHUB_OAUTH_CLIENT_ID=your-github-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret

# Production Settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
```

### 3. Security Configuration

#### Enable Rate Limiting
Rate limiting is now enabled by default. Configure limits in settings:
```python
RATELIMIT_AUTH_LOGIN = '5/minute;50/hour'
RATELIMIT_AUTH_SYNC = '10/minute;100/hour'
```

#### SSL/HTTPS Configuration
```python
# In production settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### 4. Frontend Integration Changes

#### OAuth Token Requirement
Frontend must now send OAuth tokens for authentication:

```javascript
// Before (INSECURE)
const response = await fetch('/api/auth/nextauth-sync/', {
  method: 'POST',
  body: JSON.stringify({
    email: user.email,
    provider: 'google',
    uid: user.id
  })
});

// After (SECURE)
const response = await fetch('/api/auth/nextauth-sync/', {
  method: 'POST',
  body: JSON.stringify({
    email: user.email,
    provider: 'google',
    uid: user.id,
    token: accessToken  // ← NOW REQUIRED
  })
});
```

#### Booking Creation Changes
Frontend can no longer set total_price:

```javascript
// Before (INSECURE)
const booking = {
  package_id: 1,
  selected_experiences: [1, 2],
  hotel_tier: 1,
  transport: 1,
  total_price: 1500  // ← REMOVED
};

// After (SECURE)
const booking = {
  package_id: 1,
  selected_experience_ids: [1, 2],
  hotel_tier_id: 1,
  transport_option_id: 1
  // total_price calculated on backend
};
```

### 5. Testing Migration

#### Run Security Tests
```bash
# Test OAuth verification
python manage.py test apps.users.tests.test_oauth_security

# Test price security
python manage.py test apps.bookings.tests.test_price_security

# Test payment security
python manage.py test apps.payments.tests.test_webhook_security
```

#### Manual Testing Checklist
- [ ] OAuth login with valid token works
- [ ] OAuth login with invalid token fails
- [ ] Booking creation calculates price correctly
- [ ] Payment webhook validates amounts
- [ ] Rate limiting blocks excessive requests

### 6. Production Deployment

#### Using Gunicorn
```bash
# Install gunicorn
pip install gunicorn

# Run production server
gunicorn backend.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 100
```

#### Using Docker (Optional)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/staticfiles/;
    }
    
    location /media/ {
        alias /app/media/;
    }
}
```

### 7. Monitoring Setup

#### Log Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'security': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}
```

#### Health Check Endpoint
```python
# Add to urls.py
path('health/', lambda request: JsonResponse({'status': 'ok'})),
```

### 8. Rollback Plan

#### Database Rollback
```bash
# Stop application
sudo systemctl stop gunicorn

# Restore database backup
pg_restore -d travel_platform backup_file.sql

# Restart with previous code version
git checkout previous-stable-tag
sudo systemctl start gunicorn
```

#### Code Rollback
```bash
# Rollback to previous version
git log --oneline  # Find previous stable commit
git checkout <previous-commit-hash>

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Troubleshooting

### Common Issues

#### OAuth Token Verification Fails
```bash
# Check network connectivity to OAuth providers
curl -I https://www.googleapis.com/oauth2/v1/tokeninfo
curl -I https://api.github.com/user

# Check logs
tail -f logs/django.log | grep "OAuth"
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U travel_user -d travel_platform

# Check Django database connection
python manage.py dbshell
```

#### Rate Limiting Too Aggressive
```python
# Temporarily increase limits in settings
RATELIMIT_AUTH_LOGIN = '10/minute;100/hour'
```

### Performance Monitoring
```bash
# Monitor response times
tail -f /var/log/nginx/access.log | grep "POST /api/"

# Monitor database queries
# Enable query logging in PostgreSQL
```

## Post-Migration Verification

### Security Verification
- [ ] OAuth tokens required and validated
- [ ] Price manipulation blocked
- [ ] Payment webhooks secured
- [ ] Rate limiting active
- [ ] HTTPS enforced
- [ ] Security headers present

### Functionality Verification
- [ ] User registration/login works
- [ ] Booking creation works
- [ ] Payment processing works
- [ ] Notifications sent
- [ ] Admin panel accessible

### Performance Verification
- [ ] API response times < 200ms
- [ ] Database queries optimized
- [ ] Static files served efficiently
- [ ] Memory usage stable

## Support Contacts

- **Security Issues**: security@yourdomain.com
- **Technical Issues**: tech@yourdomain.com
- **Emergency**: +1-xxx-xxx-xxxx

---

**Migration completed successfully when all checklist items are verified.**