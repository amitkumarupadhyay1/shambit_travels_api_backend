#!/bin/bash

set -e  # Exit on any error

# CRITICAL: Ensure DJANGO_SETTINGS_MODULE is set globally
export DJANGO_SETTINGS_MODULE=backend.settings.production

echo "🚀 Starting Django application..."
echo "Environment: $DJANGO_SETTINGS_MODULE"
echo "Port: $PORT"
echo "Database URL: ${DATABASE_URL:0:50}..."

# Test Django configuration first
echo "🔍 Testing Django configuration..."
python manage.py check --deploy

# Run migrations
echo "📦 Running migrations..."
# Force close any existing database connections before migrating
python -c "import django; django.setup(); from django.db import connections; connections.close_all()" 2>/dev/null || true
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Test health check endpoint
echo "🏥 Testing health check endpoint..."
python diagnose_startup.py

# Start the application
echo "🌟 Starting Gunicorn on port $PORT..."
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    backend.wsgi:application