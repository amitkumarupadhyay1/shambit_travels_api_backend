from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .services.notification_service import NotificationService

User = get_user_model()

@receiver(post_save, sender='bookings.Booking')
def booking_status_changed(sender, instance, created, **kwargs):
    """
    Create notifications when booking status changes
    """
    if created:
        # New booking created
        NotificationService.create_notification(
            user=instance.user,
            title="Booking Created",
            message=f"Your booking for {instance.package.name} has been created. "
                   f"Booking ID: {instance.id}"
        )
    else:
        # Check if status changed
        if hasattr(instance, '_original_status'):
            old_status = instance._original_status
            new_status = instance.status
            
            if old_status != new_status:
                if new_status == 'CONFIRMED':
                    NotificationService.notify_booking_confirmed(instance)
                elif new_status == 'CANCELLED':
                    NotificationService.notify_booking_cancelled(instance)

@receiver(pre_save, sender='bookings.Booking')
def store_original_booking_status(sender, instance, **kwargs):
    """
    Store original status to detect changes
    """
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except sender.DoesNotExist:
            instance._original_status = None

@receiver(post_save, sender='payments.Payment')
def payment_status_changed(sender, instance, created, **kwargs):
    """
    Create notifications when payment status changes
    """
    if not created and hasattr(instance, '_original_status'):
        old_status = instance._original_status
        new_status = instance.status
        
        if old_status != new_status:
            if new_status == 'COMPLETED':
                NotificationService.notify_payment_successful(instance)
            elif new_status == 'FAILED':
                NotificationService.notify_payment_failed(instance)

@receiver(pre_save, sender='payments.Payment')
def store_original_payment_status(sender, instance, **kwargs):
    """
    Store original payment status to detect changes
    """
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except sender.DoesNotExist:
            instance._original_status = None

@receiver(post_save, sender=User)
def welcome_notification(sender, instance, created, **kwargs):
    """
    Send welcome notification to new users
    """
    if created:
        NotificationService.create_notification(
            user=instance,
            title="Welcome to Travel Platform!",
            message="Welcome to our travel platform! Start exploring amazing "
                   "destinations and book your dream vacation."
        )