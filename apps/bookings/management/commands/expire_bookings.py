"""
Management command to expire DRAFT bookings past their expiry time.
Run this command periodically (e.g., every 5 minutes via cron or Celery).
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking
from bookings.services.booking_service import BookingService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Expire DRAFT bookings past their expiry time"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be expired without actually expiring",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        now = timezone.now()

        # Find expired DRAFT bookings
        expired_bookings = Booking.objects.filter(
            status="DRAFT", expires_at__lte=now
        ).select_related("user", "package")

        total_count = expired_bookings.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No expired DRAFT bookings found"))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would expire {total_count} bookings:")
            )
            for booking in expired_bookings[:10]:  # Show first 10
                self.stdout.write(
                    f"  - Booking #{booking.id} (User: {booking.user.email}, "
                    f"Package: {booking.package.name}, "
                    f"Expired: {booking.expires_at})"
                )
            if total_count > 10:
                self.stdout.write(f"  ... and {total_count - 10} more")
            return

        # Expire bookings
        success_count = 0
        error_count = 0

        for booking in expired_bookings:
            try:
                if BookingService.transition_status(booking, "EXPIRED"):
                    success_count += 1
                    logger.info(
                        f"Expired booking #{booking.id} "
                        f"(User: {booking.user.email}, "
                        f"Package: {booking.package.name})"
                    )
                else:
                    error_count += 1
                    logger.warning(
                        f"Failed to expire booking #{booking.id}: "
                        f"Invalid state transition"
                    )
            except Exception as e:
                error_count += 1
                logger.error(f"Error expiring booking #{booking.id}: {str(e)}")

        # Output summary
        self.stdout.write(
            self.style.SUCCESS(f"Successfully expired {success_count} bookings")
        )

        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to expire {error_count} bookings (check logs)"
                )
            )

        # Log summary
        logger.info(
            f"Booking expiry job completed: "
            f"{success_count} expired, {error_count} errors"
        )
