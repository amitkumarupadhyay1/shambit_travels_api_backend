#!/usr/bin/env python
"""
Force migrate with proper database connection.
This script ensures Django uses the correct database settings.
"""

import os
import sys

# Set Django settings module BEFORE any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")

# Setup Django
import django

django.setup()

# Verify database configuration
from django.conf import settings

print("🔍 Verifying database configuration...")
print(f"   ENGINE: {settings.DATABASES['default']['ENGINE']}")
print(f"   NAME: {settings.DATABASES['default']['NAME']}")
print(f"   HOST: {settings.DATABASES['default']['HOST']}")

# Run migrations
from django.core.management import call_command

print("📦 Running migrations...")
call_command("migrate", "--noinput")
print("✅ Migrations completed successfully!")
