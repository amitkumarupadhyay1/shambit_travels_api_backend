#!/usr/bin/env python
"""
Debug script to test database connection in production
"""

import os
import sys

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")

import django

django.setup()

from django.conf import settings
from django.db import connection


def debug_database():
    """Debug database configuration"""
    print("=== Database Debug ===")

    # Check environment variables
    database_url = os.environ.get("DATABASE_URL")
    print(f"DATABASE_URL set: {'Yes' if database_url else 'No'}")
    if database_url:
        print(f"DATABASE_URL (first 50 chars): {database_url[:50]}...")

    # Check Django settings
    print(f"Django DATABASES config: {settings.DATABASES}")

    # Test connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            result = cursor.fetchone()
            print(f"✅ Database connection successful!")
            print(f"PostgreSQL version: {result[0]}")

            # Test a simple query
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
            print(f"✅ Migrations table accessible: {migration_count} migrations found")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    return True


if __name__ == "__main__":
    success = debug_database()
    sys.exit(0 if success else 1)
