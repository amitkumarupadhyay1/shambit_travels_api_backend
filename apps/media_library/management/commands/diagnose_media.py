from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnose Media library issues"

    def handle(self, *args, **options):
        Media = apps.get_model("media_library", "Media")

        self.stdout.write("=" * 60)
        self.stdout.write("MEDIA LIBRARY DIAGNOSTIC")
        self.stdout.write("=" * 60)

        total_media = Media.objects.count()
        self.stdout.write(f"\n📊 Total Media Objects: {total_media}")

        if total_media == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ No media objects found - admin should work fine")
            )
            return

        # Check for media with issues
        self.stdout.write("\n🔍 Checking for issues...")

        issues_found = 0

        for media in Media.objects.all()[:10]:  # Check first 10
            try:
                # Try to access file properties
                if media.file:
                    _ = media.file.name
                    _ = media.file.url
                    _ = media.file.size

                # Try to access content object
                if media.content_type:
                    _ = media.content_object

                self.stdout.write(f"✅ Media ID {media.id}: OK")

            except Exception as e:
                issues_found += 1
                self.stdout.write(self.style.ERROR(f"❌ Media ID {media.id}: {str(e)}"))

        if issues_found == 0:
            self.stdout.write(
                self.style.SUCCESS("\n✅ All checked media objects are healthy")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️ Found {issues_found} media objects with issues"
                )
            )
