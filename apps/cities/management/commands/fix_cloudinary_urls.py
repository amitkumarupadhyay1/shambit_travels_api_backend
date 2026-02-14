"""
Django management command to fix Cloudinary URLs in database
Usage: python manage.py fix_cloudinary_urls
"""

from django.core.management.base import BaseCommand

import cloudinary.api
from cities.models import City


class Command(BaseCommand):
    help = "Fix Cloudinary URLs in database to match actual files on Cloudinary"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Fetching files from Cloudinary...\n")

        try:
            # Get all files from Cloudinary
            resources = cloudinary.api.resources(
                type="upload", prefix="media/library", max_results=100
            )

            self.stdout.write(
                f"Found {len(resources['resources'])} files on Cloudinary:\n"
            )

            cloudinary_files = {}
            for r in resources["resources"]:
                # Extract filename without extension
                public_id = r["public_id"]
                filename = public_id.split("/")[-1]
                cloudinary_files[filename] = r["secure_url"]
                self.stdout.write(f"  - {public_id}")
                self.stdout.write(f"    URL: {r['secure_url']}\n")

            # Fix Ayodhya city if ram_ji image exists
            if "ram_ji_l9mhm6" in cloudinary_files:
                self.stdout.write("\n🏛️ Fixing Ayodhya city...")
                try:
                    ayodhya = City.objects.get(slug="ayodhya")
                    # Store only the path, not the full URL
                    # Cloudinary storage will automatically generate the full URL
                    correct_path = "media/library/ram_ji_l9mhm6"

                    current_value = (
                        str(ayodhya.hero_image) if ayodhya.hero_image else ""
                    )

                    if current_value != correct_path:
                        self.stdout.write(f"  Current: {current_value}")
                        self.stdout.write(f"  Correct path: {correct_path}")

                        # Save just the path
                        ayodhya.hero_image = correct_path
                        ayodhya.save()

                        # Refresh to get the generated URL
                        ayodhya.refresh_from_db()
                        self.stdout.write(f"  Generated URL: {ayodhya.hero_image.url}")

                        self.stdout.write(
                            self.style.SUCCESS("  ✅ Updated Ayodhya hero_image")
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS("  ✅ Ayodhya path already correct")
                        )

                except City.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING("  ⚠️  Ayodhya city not found")
                    )

            self.stdout.write(self.style.SUCCESS("\n✅ Done!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))
            raise
