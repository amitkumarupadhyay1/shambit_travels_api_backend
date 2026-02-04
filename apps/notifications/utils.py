from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from .models import Notification
from .services.notification_service import NotificationService

User = get_user_model()

class NotificationUtils:
    """
    Utility functions for notification management
    """
    
    @staticmethod
    def create_and_send_notification(
        user: User,
        title: str,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create notification and prepare for real-time sending
        """
        notification = NotificationService.create_notification(
            user=user,
            title=title,
            message=message
        )
        
        # Here you would integrate with WebSocket/real-time system
        # For example, using Django Channels or similar
        NotificationUtils.send_realtime_notification(notification, extra_data)
        
        return notification
    
    @staticmethod
    def send_realtime_notification(
        notification: Notification,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Send real-time notification (placeholder for WebSocket integration)
        """
        # This is where you'd integrate with your real-time system
        # Example with Django Channels:
        # from channels.layers import get_channel_layer
        # from asgiref.sync import async_to_sync
        
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f"user_{notification.user.id}",
        #     {
        #         "type": "notification_message",
        #         "notification": {
        #             "id": notification.id,
        #             "title": notification.title,
        #             "message": notification.message,
        #             "is_read": notification.is_read,
        #             "created_at": notification.created_at.isoformat(),
        #             **(extra_data or {})
        #         }
        #     }
        # )
        pass
    
    @staticmethod
    def format_notification_data(notification: Notification) -> Dict[str, Any]:
        """
        Format notification data for API responses
        """
        return {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'user_id': notification.user.id
        }
    
    @staticmethod
    def get_notification_context(notification: Notification) -> Dict[str, Any]:
        """
        Get additional context for notification (for templates, etc.)
        """
        return {
            'notification': notification,
            'user': notification.user,
            'formatted_date': notification.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'time_ago': NotificationUtils.time_ago(notification.created_at)
        }
    
    @staticmethod
    def time_ago(datetime_obj):
        """
        Simple time ago calculation
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - datetime_obj
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return datetime_obj.strftime('%B %d, %Y')

# Convenience functions for common notification types
def notify_booking_update(booking, status_change: str):
    """Convenience function for booking notifications"""
    title_map = {
        'confirmed': 'Booking Confirmed',
        'cancelled': 'Booking Cancelled',
        'pending': 'Booking Pending',
    }
    
    message_map = {
        'confirmed': f'Your booking for {booking.package.name} has been confirmed.',
        'cancelled': f'Your booking for {booking.package.name} has been cancelled.',
        'pending': f'Your booking for {booking.package.name} is pending confirmation.',
    }
    
    return NotificationUtils.create_and_send_notification(
        user=booking.user,
        title=title_map.get(status_change, 'Booking Update'),
        message=message_map.get(status_change, f'Your booking status has been updated to {status_change}.'),
        extra_data={'booking_id': booking.id, 'type': 'booking_update'}
    )

def notify_payment_update(payment, status_change: str):
    """Convenience function for payment notifications"""
    title_map = {
        'completed': 'Payment Successful',
        'failed': 'Payment Failed',
        'pending': 'Payment Pending',
    }
    
    message_map = {
        'completed': f'Payment of ₹{payment.amount} has been processed successfully.',
        'failed': f'Payment of ₹{payment.amount} has failed. Please try again.',
        'pending': f'Payment of ₹{payment.amount} is being processed.',
    }
    
    return NotificationUtils.create_and_send_notification(
        user=payment.booking.user,
        title=title_map.get(status_change, 'Payment Update'),
        message=message_map.get(status_change, f'Your payment status has been updated to {status_change}.'),
        extra_data={'payment_id': payment.id, 'type': 'payment_update'}
    )