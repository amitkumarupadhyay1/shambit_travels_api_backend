#!/usr/bin/env python
"""
Quick Cloudinary verification script
Run with: python verify_cloudinary_setup.py
"""

import os
import sys
from pathlib import Path

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file explicitly
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from django.conf import settings

print("\n" + "=" * 60)
print("CLOUDINARY VERIFICATION")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
env_vars = {
    "USE_CLOUDINARY": os.environ.get("USE_CLOUDINARY"),
    "CLOUDINARY_CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
    "CLOUDINARY_API_KEY": (
        os.environ.get("CLOUDINARY_API_KEY")[:4] + "***"
        if os.environ.get("CLOUDINARY_API_KEY")
        else None
    ),
    "CLOUDINARY_API_SECRET": "***" if os.environ.get("CLOUDINARY_API_SECRET") else None,
}

for key, value in env_vars.items():
    status = "✅" if value else "❌"
    print(f"   {status} {key}: {value}")

# Check storage backend
print("\n2. Storage Backend:")
storage_class = (
    settings.DEFAULT_FILE_STORAGE
    if hasattr(settings, "DEFAULT_FILE_STORAGE")
    else "Not configured"
)
print(f"   Current: {storage_class}")

if "Cloudinary" in str(storage_class):
    print("   ✅ Cloudinary storage is ACTIVE")
else:
    print("   ❌ Cloudinary storage is NOT active")
    print("   Expected: MediaCloudinaryStorage")

# Check installed apps
print("\n3. Installed Apps:")
cloudinary_apps = ["cloudinary", "cloudinary_storage"]
for app in cloudinary_apps:
    if app in settings.INSTALLED_APPS:
        print(f"   ✅ {app} is installed")
    else:
        print(f"   ❌ {app} is NOT installed")

# Test Cloudinary connection
print("\n4. Cloudinary Connection:")
try:
    import cloudinary
    import cloudinary.api

    result = cloudinary.api.ping()
    print(f"   ✅ Successfully connected to Cloudinary!")
    print(f"   Status: {result.get('status', 'unknown')}")
except Exception as e:
    print(f"   ❌ Connection failed: {str(e)}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

# Summary
all_good = (
    os.environ.get("USE_CLOUDINARY") == "True"
    and os.environ.get("CLOUDINARY_CLOUD_NAME")
    and os.environ.get("CLOUDINARY_API_KEY")
    and os.environ.get("CLOUDINARY_API_SECRET")
    and "Cloudinary" in str(storage_class)
)

if all_good:
    print("\n✅ SUCCESS: Cloudinary is properly configured!")
    print("\nNext steps:")
    print("1. Test upload via Django admin")
    print("2. Verify URL starts with: https://res.cloudinary.com/")
    print("3. Deploy to Railway")
    print("4. Test persistence after deployment")
else:
    print("\n⚠️  WARNING: Some issues detected")
    print("\nTroubleshooting:")
    print("1. Check .env file has correct credentials")
    print("2. Ensure USE_CLOUDINARY=True (not 'true' or '1')")
    print("3. Restart Django server")
    print("4. Run this script again")

print()
