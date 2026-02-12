"""
Simple Cloudinary verification script
Run with: python manage.py shell < scripts/verify_cloudinary.py
"""

import os

from django.conf import settings
from django.core.files.storage import default_storage

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
    print(f"   {status} {key}: {value or 'NOT SET'}")

# Check storage backend
print("\n2. Storage Backend:")
storage_class = default_storage.__class__.__name__
print(f"   Current: {storage_class}")

if "Cloudinary" in storage_class:
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
    print(f"   ❌ Failed to connect: {str(e)}")

# Check media model
print("\n5. Media Model:")
try:
    from media_library.models import Media

    count = Media.objects.count()
    print(f"   ✅ Media model accessible")
    print(f"   Total media files: {count}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. If Cloudinary is not active, add credentials to .env")
print("2. Restart Django server")
print("3. Test upload via admin panel")
print("=" * 60 + "\n")
