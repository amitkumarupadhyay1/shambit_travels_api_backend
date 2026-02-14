"""
Django management command to fix Cloudinary URLs in database
Usage: python manage.py fix_cloudinary_urls
"""
from django.core.management.base import BaseCommand
import cloudinary.api
from cities.models import City


class Command(BaseCommand):
    help = 'Fix Cloudinary URLs in database to match actual files on Cloudinary'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Fetching files from Cloudinary...\n")
        
        try:
            # Get all files from Cloudinary
            resources = cloudinary.api.resources(
                type='upload',
                prefix='media/library',
                max_results=100
            )
            
            self.stdout.write(f"Found {len(resources['resources'])} files on Cloudinary:\n")
            
            cloudinary_files = {}
            for r in resources['resources']:
                # Extract filename without extension
                public_id = r['public_id']
                filename = public_id.split('/')[-1]
                cloudinary_files[filename] = r['secure_url']
                self.stdout.write(f"  - {public_id}")
                self.stdout.write(f"    URL: {r['secure_url']}\n")
            
            # Fix Ayodhya city if ram_ji image exists
            if 'ram_ji_l9mhm6' in cloudinary_files:
                self.stdout.write("\n🏛️ Fixing Ayodhya city...")
                try:
                    ayodhya = City.objects.get(slug='ayodhya')
                    correct_url = cloudinary_files['ram_ji_l9mhm6']
                    
                    if str(ayodhya.hero_image) != correct_url:
                        self.stdout.write(f"  Current: {ayodhya.hero_image}")
                        self.stdout.write(f"  Correct: {correct_url}")
                        
                        ayodhya.hero_image = correct_url
                        ayodhya.save()
                        
                        self.stdout.write(self.style.SUCCESS("  ✅ Updated Ayodhya hero_image"))
                    else:
                        self.stdout.write(self.style.SUCCESS("  ✅ Ayodhya URL already correct"))
                        
                except City.DoesNotExist:
                    self.stdout.write(self.style.WARNING("  ⚠️  Ayodhya city not found"))
            
            self.stdout.write(self.style.SUCCESS("\n✅ Done!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))
            raise
