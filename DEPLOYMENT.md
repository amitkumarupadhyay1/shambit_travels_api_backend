# Deployment Guide

This guide covers various deployment options for the Shambit Travels API Backend.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- PostgreSQL 13+
- Redis 6+

## Environment Setup

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Configure your environment variables in `.env`:
```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgres://user:password@host:port/dbname

# Redis
REDIS_URL=redis://host:port/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# OAuth Settings
GOOGLE_OAUTH2_KEY=your-google-client-id
GOOGLE_OAUTH2_SECRET=your-google-client-secret

# Payment Gateway
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Production with Docker Compose

1. Create production docker-compose file:
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: shambit_travels
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    restart: unless-stopped

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --workers 3 backend.wsgi:application
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

2. Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Cloud Deployments

#### AWS ECS Deployment

1. Build and push to ECR:
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker build -t shambit-travels-api .
docker tag shambit-travels-api:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/shambit-travels-api:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/shambit-travels-api:latest
```

2. Create ECS task definition and service using AWS Console or CLI.

#### Google Cloud Run

1. Build and deploy:
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/shambit-travels-api
gcloud run deploy --image gcr.io/PROJECT-ID/shambit-travels-api --platform managed
```

#### Heroku Deployment

1. Create Heroku app:
```bash
heroku create shambit-travels-api
```

2. Add buildpacks:
```bash
heroku buildpacks:add heroku/python
```

3. Set environment variables:
```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
# ... other environment variables
```

4. Deploy:
```bash
git push heroku main
```

5. Run migrations:
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### 3. Traditional Server Deployment

#### Ubuntu/Debian Server

1. Install dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx
```

2. Create application user:
```bash
sudo adduser shambit
sudo usermod -aG sudo shambit
```

3. Clone and setup application:
```bash
su - shambit
git clone https://github.com/amitkumarupadhyay1/shambit_travels_api_backend.git
cd shambit_travels_api_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Configure PostgreSQL:
```bash
sudo -u postgres psql
CREATE DATABASE shambit_travels;
CREATE USER shambit_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE shambit_travels TO shambit_user;
\q
```

5. Configure environment and run migrations:
```bash
cp .env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

6. Create systemd service:
```bash
sudo nano /etc/systemd/system/shambit-travels.service
```

```ini
[Unit]
Description=Shambit Travels API
After=network.target

[Service]
User=shambit
Group=www-data
WorkingDirectory=/home/shambit/shambit_travels_api_backend
Environment="PATH=/home/shambit/shambit_travels_api_backend/venv/bin"
ExecStart=/home/shambit/shambit_travels_api_backend/venv/bin/gunicorn --workers 3 --bind unix:/home/shambit/shambit_travels_api_backend/shambit_travels.sock backend.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

7. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/shambit_travels
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/shambit/shambit_travels_api_backend;
    }
    location /media/ {
        root /home/shambit/shambit_travels_api_backend;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/shambit/shambit_travels_api_backend/shambit_travels.sock;
    }
}
```

8. Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl start shambit-travels
sudo systemctl enable shambit-travels
sudo ln -s /etc/nginx/sites-available/shambit_travels /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

## SSL Configuration

### Using Certbot (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Monitoring and Logging

### Application Monitoring

1. Add health check monitoring
2. Set up log aggregation
3. Configure error tracking (Sentry)
4. Monitor database performance

### Log Management

```bash
# View application logs
sudo journalctl -u shambit-travels -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Backup Strategy

### Database Backup

```bash
# Create backup
pg_dump -h localhost -U shambit_user shambit_travels > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql -h localhost -U shambit_user shambit_travels < backup_file.sql
```

### Media Files Backup

```bash
# Sync to cloud storage
aws s3 sync media/ s3://your-bucket/media/
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Use HTTPS in production
- [ ] Set up proper firewall rules
- [ ] Regular security updates
- [ ] Monitor for vulnerabilities
- [ ] Implement rate limiting
- [ ] Set up proper CORS headers
- [ ] Use environment variables for secrets

## Performance Optimization

1. **Database Optimization**:
   - Add database indexes
   - Use connection pooling
   - Implement query optimization

2. **Caching**:
   - Configure Redis caching
   - Implement view-level caching
   - Use CDN for static files

3. **Application Optimization**:
   - Use Gunicorn with multiple workers
   - Implement async views where appropriate
   - Optimize database queries

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Check DATABASE_URL format
   - Verify database credentials
   - Ensure database server is running

2. **Static Files Not Loading**:
   - Run `python manage.py collectstatic`
   - Check Nginx configuration
   - Verify file permissions

3. **502 Bad Gateway**:
   - Check if Gunicorn is running
   - Verify socket file permissions
   - Check Nginx configuration

### Useful Commands

```bash
# Check service status
sudo systemctl status shambit-travels

# Restart application
sudo systemctl restart shambit-travels

# View logs
sudo journalctl -u shambit-travels -f

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```