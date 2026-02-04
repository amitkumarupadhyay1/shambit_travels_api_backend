from django.core.management.base import BaseCommand
from media_library.services.media_service import MediaService


class Command(BaseCommand):
    help = "Clean up media files and storage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--orphaned",
            action="store_true",
            help="Clean up orphaned media files (not attached to any object)",
        )
        parser.add_argument(
            "--unused", action="store_true", help="Clean up unused files from storage"
        )
        parser.add_argument(
            "--all", action="store_true", help="Clean up both orphaned and unused files"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if options["all"] or options["orphaned"]:
            self.stdout.write("Cleaning up orphaned media files...")

            if dry_run:
                # Count orphaned media
                orphaned_count = 0
                from media_library.models import Media

                for media in Media.objects.all():
                    try:
                        if not media.content_object:
                            orphaned_count += 1
                    except:
                        orphaned_count += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Would delete {orphaned_count} orphaned media files"
                    )
                )
            else:
                deleted_count = MediaService.cleanup_orphaned_media()
                self.stdout.write(
                    self.style.SUCCESS(f"Deleted {deleted_count} orphaned media files")
                )

        if options["all"] or options["unused"]:
            self.stdout.write("Cleaning up unused files from storage...")

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "Would scan storage for unused files (dry-run not implemented for this operation)"
                    )
                )
            else:
                result = MediaService.cleanup_unused_files()

                if "error" in result:
                    self.stdout.write(self.style.ERROR(f'Error: {result["error"]}'))
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Cleaned up {result["unused_files_removed"]} unused files, '
                            f'freed {result["total_size_freed"]} bytes, '
                            f'removed {result["empty_dirs_removed"]} empty directories'
                        )
                    )

        if not any([options["orphaned"], options["unused"], options["all"]]):
            self.stdout.write(
                self.style.ERROR("Please specify --orphaned, --unused, or --all")
            )
