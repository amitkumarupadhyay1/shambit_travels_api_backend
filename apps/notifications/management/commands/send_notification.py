from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.services.notification_service import NotificationService

User = get_user_model()

class Command(BaseCommand):
    help = 'Send notification to users'

    def add_arguments(self, parser):
        parser.add_argument('title', type=str, help='Notification title')
        parser.add_argument('message', type=str, help='Notification message')
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send to specific user ID'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Send to all active users'
        )

    def handle(self, *args, **options):
        title = options['title']
        message = options['message']
        user_id = options.get('user_id')
        all_users = options.get('all_users')

        if user_id:
            notification = NotificationService.create_user_notification(
                user_id, title, message
            )
            if notification:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Notification sent to user {user_id}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'User {user_id} not found'
                    )
                )
        elif all_users:
            count = NotificationService.notify_all_users(title, message)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Notification sent to {count} users'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Please specify either --user-id or --all-users'
                )
            )