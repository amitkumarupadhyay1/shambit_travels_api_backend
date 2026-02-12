#!/usr/bin/env python
"""
Cloudinary Setup and Verification Script

This script helps verify Cloudinary configuration and test the setup.

Usage:
    python scripts/setup_cloudinary.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps"))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django

django.setup()

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage

from media_library.models import Media


def check_environment_variables():
    """Check if required environment variables are set"""
    print("=" * 60)
    print("1. Checking Environment Variables")
    print("=" * 60)

    required_vars = [
        "USE_CLOUDINARY",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
    ]

    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "KEY" in var:
                display_value = value[:4] + "*" * (len(value) - 4)
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print("\n⚠️  Missing environment variables!")
        print("Please add these to your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return False

    print("\n✅ All environment variables are set!")
    return True


def check_storage_backend():
    """Check if Cloudinary storage backend is active"""
    print("\n" + "=" * 60)
    print("2. Checking Storage Backend")
    print("=" * 60)

    storage_class = default_storage.__class__.__name__
    print(f"Current storage backend: {storage_class}")

    if "Cloudinary" in storage_class:
        print("✅ Cloudinary storage is active!")
        return True
    else:
        print("❌ Cloudinary storage is NOT active!")
        print(f"   Current: {storage_class}")
        print("   Expected: MediaCloudinaryStorage")
        print("\nTroubleshooting:")
        print("1. Ensure USE_CLOUDINARY=True in .env")
        print("2. Restart Django server")
        print("3. Check backend/backend/settings/storage.py")
        return False


def check_installed_apps():
    """Check if Cloudinary apps are in INSTALLED_APPS"""
    print("\n" + "=" * 60)
    print("3. Checking Installed Apps")
    print("=" * 60)

    required_apps = ["cloudinary", "cloudinary_storage"]
    installed_apps = settings.INSTALLED_APPS

    all_installed = True
    for app in required_apps:
        if app in installed_apps:
            print(f"✅ {app} is installed")
        else:
            print(f"❌ {app} is NOT installed")
            all_installed = False

    if not all_installed:
        print("\n⚠️  Missing apps!")
        print("Add to INSTALLED_APPS in settings/base.py:")
        print("  'cloudinary_storage',")
        print("  'cloudinary',")
        return False

    print("\n✅ All required apps are installed!")
    return True


def test_cloudinary_connection():
    """Test connection to Cloudinary"""
    print("\n" + "=" * 60)
    print("4. Testing Cloudinary Connection")
    print("=" * 60)

    try:
        import cloudinary
        import cloudinary.api

        # Try to get account details
        result = cloudinary.api.ping()
        print(f"✅ Successfully connected to Cloudinary!")
        print(f"   Status: {result.get('status', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Cloudinary!")
        print(f"   Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify credentials in Cloudinary dashboard")
        print("2. Check internet connection")
        print("3. Ensure cloudinary package is installed: pip install cloudinary")
        return False


def check_media_model():
    """Check if Media model is accessible"""
    print("\n" + "=" * 60)
    print("5. Checking Media Model")
    print("=" * 60)

    try:
        count = Media.objects.count()
        print(f"✅ Media model is accessible!")
        print(f"   Total media files: {count}")
        return True
    except Exception as e:
        print(f"❌ Failed to access Media model!")
        print(f"   Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Check database connection")
        return False


def test_file_upload():
    """Test uploading a file to Cloudinary"""
    print("\n" + "=" * 60)
    print("6. Testing File Upload (Optional)")
    print("=" * 60)

    response = input("Do you want to test file upload? (y/n): ").strip().lower()
    if response != "y":
        print("⏭️  Skipping file upload test")
        return True

    try:
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a simple test image
        test_content = b"Test file content"
        test_file = SimpleUploadedFile(
            "test_image.txt", test_content, content_type="text/plain"
        )

        # Get a content type (use City as example)
        try:
            ct = ContentType.objects.get(app_label="cities", model="city")
            # Try to get first city
            from cities.models import City

            city = City.objects.first()

            if not city:
                print("⚠️  No cities found. Creating test city...")
                city = City.objects.create(
                    name="Test City",
                    slug="test-city",
                    description="Test city for media upload",
                    status="DRAFT",
                )

            # Create media object
            media = Media.objects.create(
                file=test_file,
                title="Test Upload",
                alt_text="Test image for Cloudinary verification",
                content_type=ct,
                object_id=city.id,
            )

            print(f"✅ Successfully uploaded test file!")
            print(f"   Media ID: {media.id}")
            print(f"   File URL: {media.file.url}")

            # Check if URL is Cloudinary URL
            if "cloudinary.com" in media.file.url:
                print(f"   ✅ File is stored on Cloudinary!")
            else:
                print(f"   ⚠️  File URL doesn't look like Cloudinary URL")

            # Clean up test file
            cleanup = input("\nDelete test file? (y/n): ").strip().lower()
            if cleanup == "y":
                media.delete()
                print("   Test file deleted")

            return True

        except Exception as e:
            print(f"❌ Failed to create test upload!")
            print(f"   Error: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ Failed to test file upload!")
        print(f"   Error: {str(e)}")
        return False


def print_summary(results):
    """Print summary of all checks"""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    checks = [
        ("Environment Variables", results["env_vars"]),
        ("Storage Backend", results["storage"]),
        ("Installed Apps", results["apps"]),
        ("Cloudinary Connection", results["connection"]),
        ("Media Model", results["model"]),
    ]

    if "upload" in results:
        checks.append(("File Upload Test", results["upload"]))

    all_passed = all(result for _, result in checks)

    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Cloudinary is properly configured.")
        print("\nNext steps:")
        print("1. Start uploading media via Django admin")
        print("2. Check Cloudinary dashboard: https://cloudinary.com/console")
        print("3. Monitor usage to stay within free tier")
        print("4. Read admin guide: docs/ADMIN_MEDIA_GUIDE.md")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nFor help:")
        print("1. Read: docs/MEDIA_LIBRARY_ANALYSIS_AND_IMPLEMENTATION_PLAN.md")
        print("2. Read: docs/ADMIN_MEDIA_GUIDE.md")
        print("3. Check Django logs: backend/logs/django.log")
    print("=" * 60)


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("CLOUDINARY SETUP VERIFICATION")
    print("=" * 60)
    print("\nThis script will verify your Cloudinary configuration.")
    print("Make sure you have:")
    print("1. Created a Cloudinary account")
    print("2. Added credentials to .env file")
    print("3. Installed dependencies: pip install -r requirements.txt")
    print("4. Restarted Django server")
    print("\n" + "=" * 60)

    input("Press Enter to continue...")

    results = {}

    # Run all checks
    results["env_vars"] = check_environment_variables()
    results["storage"] = check_storage_backend()
    results["apps"] = check_installed_apps()
    results["connection"] = test_cloudinary_connection()
    results["model"] = check_media_model()

    # Optional upload test
    if all(results.values()):
        results["upload"] = test_file_upload()

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
