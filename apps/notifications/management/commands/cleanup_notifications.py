from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.services.notification_service import NotificationService

User = get_user_model()


class Command(BaseCommand):
    help = "Clean up old notifications"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete notifications older than this many days (default: 30)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff_date = timezone.now() - timedelta(days=days)

        if dry_run:
            from notifications.models import Notification

            count = Notification.objects.filter(created_at__lt=cutoff_date).count()
            self.stdout.write(
                self.style.WARNING(
                    f"Would delete {count} notifications older than {days} days"
                )
            )
        else:
            total_deleted = 0
            for user in User.objects.filter(is_active=True):
                deleted = NotificationService.clear_old_notifications(user, days)
                total_deleted += deleted

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {total_deleted} notifications older than {days} days"
                )
            )
