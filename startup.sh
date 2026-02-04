#!/bin/bash

echo "Starting Django application..."
echo "Environment: $DJANGO_SETTINGS_MODULE"
echo "Port: $PORT"
echo "Database URL: ${DATABASE_URL:0:20}..."

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if the application can start
echo "Testing Django configuration..."
python manage.py check --deploy

# Start the application
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --access-logfile - --error-logfile - backend.wsgi:application