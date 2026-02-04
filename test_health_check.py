#!/usr/bin/env python3
"""
Simple script to test the health check endpoint
"""

import os
import sys

import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()

from django.test import RequestFactory

from backend.urls import health_check


def test_health_check():
    """Test the health check endpoint"""
    factory = RequestFactory()
    request = factory.get("/health/")

    try:
        response = health_check(request)
        print(f"✅ Health check status: {response.status_code}")
        print(f"✅ Response content: {response.content.decode()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing health check endpoint...")
    success = test_health_check()
    sys.exit(0 if success else 1)
