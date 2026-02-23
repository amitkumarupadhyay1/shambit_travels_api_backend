#!/usr/bin/env python
"""
Simple health check script for debugging Railway deployment issues
"""

import os

import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()


def check_health():
    """Check application health"""
    print("=== Health Check ===")

    # Check Django settings
    print(f"Django settings module: {settings.SETTINGS_MODULE}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Allowed hosts: {settings.ALLOWED_HOSTS}")

    # Check database
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection: OK")
    except Exception as e:
        print(f"✗ Database connection: FAILED - {e}")

    # Check static files
    try:
        pass

        print(f"✓ Static files root: {settings.STATIC_ROOT}")
        print(f"✓ Static files URL: {settings.STATIC_URL}")
    except Exception as e:
        print(f"✗ Static files: FAILED - {e}")

    # Check apps
    print(f"✓ Installed apps: {len(settings.INSTALLED_APPS)} apps")

    # Check environment variables
    print(f"✓ PORT: {os.environ.get('PORT', 'Not set')}")
    print(f"✓ DATABASE_URL: {'Set' if os.environ.get('DATABASE_URL') else 'Not set'}")

    print("=== End Health Check ===")


if __name__ == "__main__":
    check_health()
