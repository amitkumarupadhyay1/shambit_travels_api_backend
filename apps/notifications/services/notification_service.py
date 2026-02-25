import logging
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from ..models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Service class for notification business logic
    Handles creation, bulk operations, and notification management
    """

    @staticmethod
    def create_notification(
        user: User, title: str, message: str, send_push: bool = True
    ) -> Notification:
        """
        Create a notification for user
        Optionally send push notification
        """
        try:
            notification = Notification.objects.create(
                user=user, title=title, message=message, is_read=False
            )
            logger.info(f"Notification created for user {user.id}: {title}")

            # Send push notification if enabled
            if send_push:
                try:
                    from .push_service import PushNotificationService

                    PushNotificationService.send_to_user(
                        user=user,
                        title=title,
                        message=message,
                        url="/dashboard/notifications",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send push notification: {str(e)}")

            return notification
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            raise

    @staticmethod
    def notify_booking_created(booking):
        """Send notification when booking created"""
        return NotificationService.create_notification(
            user=booking.user,
            title="Booking Created",
            message=f"Your booking for {booking.package.name} has been created. "
            f"Total: ₹{booking.total_price}. Please proceed to payment.",
        )

    @staticmethod
    def notify_payment_pending(booking):
        """Send notification when payment initiated"""
        return NotificationService.create_notification(
            user=booking.user,
            title="Payment Initiated",
            message=f"Payment for booking #{booking.id} is pending. "
            f"Please complete payment to confirm your booking.",
        )

    @staticmethod
    def notify_booking_confirmed(booking):
        """Send notification when booking confirmed"""
        # Create in-app notification
        notification = NotificationService.create_notification(
            user=booking.user,
            title="Booking Confirmed!",
            message=f"Your booking for {booking.package.name} has been confirmed! "
            f"Check your email for details.",
        )

        # Send email confirmation
        try:
            from users.services.email_service import EmailService

            EmailService.send_booking_confirmation_email(booking)
        except Exception as e:
            logger.warning(f"Failed to send booking confirmation email: {str(e)}")

        # Send SMS confirmation
        try:
            from users.services.otp_service import OTPService

            OTPService.send_booking_confirmation_sms(booking)
        except Exception as e:
            logger.warning(f"Failed to send booking confirmation SMS: {str(e)}")

        return notification

    @staticmethod
    def notify_payment_failed(booking):
        """Send notification when payment fails"""
        return NotificationService.create_notification(
            user=booking.user,
            title="Payment Failed",
            message=f"Payment for booking #{booking.id} failed. "
            f"Please try again or contact support.",
        )

    @staticmethod
    def notify_booking_cancelled(booking):
        """Send notification when booking cancelled"""
        return NotificationService.create_notification(
            user=booking.user,
            title="Booking Cancelled",
            message=f"Booking #{booking.id} for {booking.package.name} has been cancelled. "
            f"Refunds will be processed within 5-7 business days.",
        )

    @staticmethod
    def create_bulk_notifications(
        users: List[User], title: str, message: str
    ) -> List[Notification]:
        """
        Create notifications for multiple users efficiently
        """
        notifications = [
            Notification(user=user, title=title, message=message) for user in users
        ]
        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def create_user_notification(
        user_id: int, title: str, message: str
    ) -> Optional[Notification]:
        """
        Create notification by user ID with error handling
        """
        try:
            user = User.objects.get(id=user_id)
            return NotificationService.create_notification(user, title, message)
        except User.DoesNotExist:
            return None

    @staticmethod
    def notify_payment_successful(payment) -> Notification:
        """
        Create payment success notification
        """
        return NotificationService.create_notification(
            user=payment.booking.user,
            title="Payment Successful",
            message=f"Payment of ₹{payment.amount} for booking {payment.booking.id} "
            f"has been processed successfully.",
        )

    @staticmethod
    def notify_all_users(title: str, message: str) -> int:
        """
        Send notification to all active users
        Returns count of notifications created
        """
        active_users = User.objects.filter(is_active=True)
        notifications = NotificationService.create_bulk_notifications(
            list(active_users), title, message
        )
        return len(notifications)

    @staticmethod
    def get_user_stats(user: User) -> Dict[str, int]:
        """
        Get notification statistics for a user
        """
        user_notifications = Notification.objects.filter(user=user)

        return {
            "total": user_notifications.count(),
            "unread": user_notifications.filter(is_read=False).count(),
            "read": user_notifications.filter(is_read=True).count(),
        }

    @staticmethod
    @transaction.atomic
    def mark_all_read(user: User) -> int:
        """
        Mark all user notifications as read
        Returns count of updated notifications
        """
        return Notification.objects.filter(user=user, is_read=False).update(
            is_read=True
        )

    @staticmethod
    @transaction.atomic
    def clear_old_notifications(user: User, days: int = 30) -> int:
        """
        Delete notifications older than specified days
        Returns count of deleted notifications
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = Notification.objects.filter(
            user=user, created_at__lt=cutoff_date
        ).delete()
        return deleted_count

    @staticmethod
    @transaction.atomic
    def clear_read_notifications(user: User) -> int:
        """
        Delete all read notifications for user
        Returns count of deleted notifications
        """
        deleted_count, _ = Notification.objects.filter(user=user, is_read=True).delete()
        return deleted_count

    @staticmethod
    def get_recent_notifications(user: User, days: int = 7, limit: int = 20):
        """
        Get recent notifications for user
        """
        recent_date = timezone.now() - timezone.timedelta(days=days)
        return Notification.objects.filter(
            user=user, created_at__gte=recent_date
        ).order_by("-created_at")[:limit]

    @staticmethod
    def search_notifications(user: User, query: str, is_read: Optional[bool] = None):
        """
        Search user notifications by title and message
        """
        notifications = Notification.objects.filter(
            user=user, title__icontains=query
        ) | Notification.objects.filter(user=user, message__icontains=query)

        if is_read is not None:
            notifications = notifications.filter(is_read=is_read)

        return notifications.order_by("-created_at")
