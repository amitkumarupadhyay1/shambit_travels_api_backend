"""
Management command to expire DRAFT bookings that have exceeded their expiration time.
Run this periodically via cron or Celery beat.
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Expire DRAFT bookings that have exceeded their expiration time"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be expired without actually expiring",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find all DRAFT bookings that have expired
        now = timezone.now()
        expired_bookings = Booking.objects.filter(
            status="DRAFT", expires_at__lt=now
        ).select_related("user", "package")

        count = expired_bookings.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No expired DRAFT bookings found"))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[DRY RUN] Would expire {count} bookings:")
            )
            for booking in expired_bookings:
                self.stdout.write(
                    f"  - Booking #{booking.id} (User: {booking.user.email}, "
                    f"Package: {booking.package.name}, Expired: {booking.expires_at})"
                )
        else:
            expired_count = 0
            for booking in expired_bookings:
                try:
                    booking.transition_to("EXPIRED")
                    expired_count += 1
                    logger.info(
                        f"Expired booking #{booking.id} (User: {booking.user.email})"
                    )
                except Exception as e:
                    logger.error(f"Failed to expire booking #{booking.id}: {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to expire booking #{booking.id}: {str(e)}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully expired {expired_count} out of {count} bookings"
                )
            )
