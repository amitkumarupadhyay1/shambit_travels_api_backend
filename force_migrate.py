#!/usr/bin/env python
"""
Force migrate with proper database connection.
This script ensures Django uses the correct database settings.
"""

import os
import sys

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")

# Setup Django
import django

django.setup()

# Force close and reinitialize all database connections
from django.db import connections

connections.close_all()

print("🔧 Database connections closed and will be reinitialized on first use")
print(f"🔍 DATABASES setting: {django.conf.settings.DATABASES}")
print(f"🔍 Default DB ENGINE: {django.conf.settings.DATABASES['default']['ENGINE']}")

# Now run migrations
from django.core.management import call_command

print("📦 Running migrations with fresh database connection...")
call_command("migrate", "--noinput")
print("✅ Migrations completed successfully!")
