import os

from django.core.management.base import BaseCommand

from media_library.services.media_service import MediaService


class Command(BaseCommand):
    help = "Check media storage health"

    def handle(self, *args, **options):
        storage_info = MediaService.get_storage_info()

        if "error" in storage_info:
            self.stdout.write(
                self.style.ERROR(f"❌ Storage Error: {storage_info['error']}")
            )
            return

        is_persistent = "RAILWAY_VOLUME_MOUNT_PATH" in os.environ

        self.stdout.write(self.style.SUCCESS("✅ Storage Health Check"))
        self.stdout.write(f"Media Root: {storage_info['media_root']}")
        self.stdout.write(
            f"Storage Type: {'Railway Volume (Persistent)' if is_persistent else 'Local (Ephemeral)'}"
        )
        self.stdout.write(f"Total Files: {storage_info['total_files']}")
        self.stdout.write(f"Total Size: {storage_info['total_size_mb']} MB")

        if storage_info.get("disk_info_available"):
            self.stdout.write(f"Disk Usage: {storage_info['disk_usage_percentage']}%")
            self.stdout.write(
                f"Disk Free: {round(storage_info['disk_free'] / (1024**3), 2)} GB"
            )

        if not is_persistent:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ WARNING: Using ephemeral storage! Files will be lost on deployment."
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "   Solution: Subscribe to Railway Hobby plan and configure volume."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Using persistent Railway volume - files will survive deployments"
                )
            )
