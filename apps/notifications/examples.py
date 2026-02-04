"""
Integration examples for the notification system
These examples show how other apps can integrate with notifications
"""

from django.contrib.auth import get_user_model

from .models import Notification
from .services.notification_service import NotificationService
from .utils import notify_booking_update, notify_payment_update

User = get_user_model()


# Example 1: Integration in booking views
def booking_view_example():
    """
    Example of how to integrate notifications in booking views
    """
    from bookings.models import Booking

    def confirm_booking(request, booking_id):
        booking = Booking.objects.get(id=booking_id)
        booking.status = "CONFIRMED"
        booking.save()

        # Method 1: Using service directly
        NotificationService.notify_booking_confirmed(booking)

        # Method 2: Using utility function
        notify_booking_update(booking, "confirmed")

        # Method 3: Custom notification
        NotificationService.create_notification(
            user=booking.user,
            title="Booking Confirmed!",
            message=f"Great news! Your booking for {booking.package.name} "
            f"has been confirmed. We'll send you more details soon.",
        )


# Example 2: Integration in payment processing
def payment_processing_example():
    """
    Example of payment processing with notifications
    """
    from payments.models import Payment

    def process_payment_success(payment_id):
        payment = Payment.objects.get(id=payment_id)
        payment.status = "COMPLETED"
        payment.save()

        # Automatic notification via signals
        # Or manual notification:
        NotificationService.notify_payment_successful(payment)


# Example 3: Bulk notifications for marketing
def marketing_notifications_example():
    """
    Example of sending marketing notifications
    """
    # Send to all active users
    count = NotificationService.notify_all_users(
        title="Special Offer: 20% Off All Packages!",
        message="Limited time offer! Book any travel package and get 20% off. "
        "Use code TRAVEL20 at checkout. Offer valid until end of month.",
    )
    print(f"Sent marketing notification to {count} users")

    # Send to specific user segment (e.g., users with bookings)
    from bookings.models import Booking

    users_with_bookings = User.objects.filter(booking__isnull=False).distinct()

    NotificationService.create_bulk_notifications(
        users=list(users_with_bookings),
        title="Thank You for Traveling With Us!",
        message="We hope you enjoyed your recent trip. Please leave us a review "
        "and get 10% off your next booking!",
    )


# Example 4: Custom notification types
def custom_notification_examples():
    """
    Examples of custom notification types
    """
    user = User.objects.first()

    # Welcome series for new users
    def send_welcome_series(user):
        notifications = [
            {
                "title": "Welcome to Travel Platform!",
                "message": "Thanks for joining us! Explore amazing destinations.",
                "delay_days": 0,
            },
            {
                "title": "Complete Your Profile",
                "message": "Add your preferences to get personalized recommendations.",
                "delay_days": 1,
            },
            {
                "title": "Your First Booking Awaits",
                "message": "Ready to plan your first trip? Browse our popular packages.",
                "delay_days": 3,
            },
        ]

        for notification in notifications:
            # In a real implementation, you'd use Celery or similar for delays
            NotificationService.create_notification(
                user=user, title=notification["title"], message=notification["message"]
            )

    # Reminder notifications
    def send_booking_reminders():
        from datetime import timedelta

        from bookings.models import Booking
        from django.utils import timezone

        # Find bookings starting in 7 days
        upcoming_date = timezone.now().date() + timedelta(days=7)
        upcoming_bookings = Booking.objects.filter(
            status="CONFIRMED",
            # Assuming you have a start_date field
            # start_date=upcoming_date
        )

        for booking in upcoming_bookings:
            NotificationService.create_notification(
                user=booking.user,
                title="Trip Reminder: 7 Days to Go!",
                message=f"Your trip to {booking.package.city.name} starts in 7 days. "
                f"Make sure you have all necessary documents ready.",
            )


# Example 5: Integration with external services
def external_service_integration():
    """
    Example of integrating with external notification services
    """

    def send_notification_with_email(user, title, message):
        # Create in-app notification
        notification = NotificationService.create_notification(
            user=user, title=title, message=message
        )

        # Also send email (pseudo-code)
        # send_email(
        #     to=user.email,
        #     subject=title,
        #     message=message,
        #     template='notification_email.html'
        # )

        # Send push notification (pseudo-code)
        # if user.push_token:
        #     send_push_notification(
        #         token=user.push_token,
        #         title=title,
        #         body=message
        #     )

        return notification


# Example 6: Notification preferences
def notification_preferences_example():
    """
    Example of handling user notification preferences
    """

    def create_notification_with_preferences(user, title, message, category="general"):
        # Check user preferences (pseudo-code)
        # preferences = user.notification_preferences
        # if preferences.get(category, True):  # Default to True

        return NotificationService.create_notification(
            user=user, title=title, message=message
        )


# Example 7: Notification analytics
def notification_analytics_example():
    """
    Example of notification analytics and reporting
    """

    def get_notification_metrics():
        from datetime import timedelta

        from django.db.models import Avg, Count
        from django.utils import timezone

        # Get metrics for last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)

        metrics = {
            "total_sent": Notification.objects.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            "read_rate": Notification.objects.filter(
                created_at__gte=thirty_days_ago
            ).aggregate(read_rate=Avg("is_read"))["read_rate"]
            or 0,
            "by_user": Notification.objects.filter(created_at__gte=thirty_days_ago)
            .values("user__email")
            .annotate(count=Count("id"))
            .order_by("-count")[:10],
        }

        return metrics


if __name__ == "__main__":
    # These are just examples - don't run directly
    print("Notification system integration examples")
    print("See the functions above for implementation details")
