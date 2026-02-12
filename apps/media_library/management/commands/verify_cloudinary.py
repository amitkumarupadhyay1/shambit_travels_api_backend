"""
Django management command to verify Cloudinary setup
Usage: python manage.py verify_cloudinary
"""

import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify Cloudinary configuration and setup"

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("CLOUDINARY VERIFICATION")
        self.stdout.write("=" * 60)

        # Check environment variables
        self.stdout.write("\n1. Environment Variables:")
        env_vars = {
            "USE_CLOUDINARY": os.environ.get("USE_CLOUDINARY"),
            "CLOUDINARY_CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
            "CLOUDINARY_API_KEY": (
                os.environ.get("CLOUDINARY_API_KEY")[:4] + "***"
                if os.environ.get("CLOUDINARY_API_KEY")
                else None
            ),
            "CLOUDINARY_API_SECRET": (
                "***" if os.environ.get("CLOUDINARY_API_SECRET") else None
            ),
        }

        all_env_set = True
        for key, value in env_vars.items():
            if value and value != "NOT SET":
                self.stdout.write(self.style.SUCCESS(f"   ✅ {key}: {value}"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ {key}: NOT SET"))
                all_env_set = False

        # Check storage backend
        self.stdout.write("\n2. Storage Backend:")
        storage_class = default_storage.__class__.__name__
        self.stdout.write(f"   Current: {storage_class}")

        if "Cloudinary" in storage_class:
            self.stdout.write(self.style.SUCCESS("   ✅ Cloudinary storage is ACTIVE"))
        else:
            self.stdout.write(
                self.style.ERROR("   ❌ Cloudinary storage is NOT active")
            )
            self.stdout.write("   Expected: MediaCloudinaryStorage")

        # Check installed apps
        self.stdout.write("\n3. Installed Apps:")
        cloudinary_apps = ["cloudinary", "cloudinary_storage"]
        all_apps_installed = True
        for app in cloudinary_apps:
            if app in settings.INSTALLED_APPS:
                self.stdout.write(self.style.SUCCESS(f"   ✅ {app} is installed"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ {app} is NOT installed"))
                all_apps_installed = False

        # Test Cloudinary connection
        self.stdout.write("\n4. Cloudinary Connection:")
        cloudinary_connected = False
        try:
            import cloudinary
            import cloudinary.api

            result = cloudinary.api.ping()
            self.stdout.write(
                self.style.SUCCESS("   ✅ Successfully connected to Cloudinary!")
            )
            self.stdout.write(f"   Status: {result.get('status', 'unknown')}")
            cloudinary_connected = True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Failed to connect: {str(e)}"))

        # Check media model
        self.stdout.write("\n5. Media Model:")
        media_accessible = False
        try:
            from media_library.models import Media

            count = Media.objects.count()
            self.stdout.write(self.style.SUCCESS("   ✅ Media model accessible"))
            self.stdout.write(f"   Total media files: {count}")
            media_accessible = True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error: {str(e)}"))

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 60)

        all_passed = (
            all_env_set
            and "Cloudinary" in storage_class
            and all_apps_installed
            and cloudinary_connected
            and media_accessible
        )

        if all_passed:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n🎉 All checks passed! Cloudinary is properly configured."
                )
            )
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Test upload via Django admin")
            self.stdout.write(
                "2. Check Cloudinary dashboard: https://cloudinary.com/console"
            )
            self.stdout.write("3. Upload content for packages")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Some checks failed. Please fix the issues above."
                )
            )

            if not all_env_set:
                self.stdout.write("\nTo fix environment variables:")
                self.stdout.write(
                    "1. Sign up at https://cloudinary.com/users/register/free"
                )
                self.stdout.write("2. Add credentials to backend/.env file")
                self.stdout.write("3. Restart Django server")

            if "Cloudinary" not in storage_class:
                self.stdout.write("\nTo activate Cloudinary storage:")
                self.stdout.write("1. Ensure USE_CLOUDINARY=True in .env")
                self.stdout.write("2. Restart Django server")

        self.stdout.write("=" * 60 + "\n")
