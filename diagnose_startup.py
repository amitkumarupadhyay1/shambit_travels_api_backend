#!/usr/bin/env python3
"""
Diagnostic script to test Django startup and health check
"""
import os
import sys
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Test database connection
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Test health check endpoint
try:
    from django.test import RequestFactory
    from backend.urls import health_check
    
    factory = RequestFactory()
    request = factory.get('/health/')
    response = health_check(request)
    
    print(f"✅ Health check endpoint status: {response.status_code}")
    print(f"✅ Health check response: {response.content.decode()}")
except Exception as e:
    print(f"❌ Health check endpoint failed: {e}")

# Check critical settings
print(f"\n📋 Configuration:")
print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")
print(f"PORT: {os.environ.get('PORT', 'Not set')}")
print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")

print("\n✅ Diagnostic complete")