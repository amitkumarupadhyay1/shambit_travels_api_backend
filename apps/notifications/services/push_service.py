"""
Push Notification Service
Handles sending push notifications via Web Push API
"""

import json
import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model

from pywebpush import WebPushException, webpush

from ..models_push import PushSubscription

logger = logging.getLogger(__name__)
User = get_user_model()


class PushNotificationService:
    """
    Service for sending push notifications to users
    Uses Web Push API with VAPID authentication
    """

    @staticmethod
    def get_vapid_keys() -> Dict[str, str]:
        """
        Get VAPID keys from settings
        Generate them if not present
        """
        # Check if keys exist in settings
        if hasattr(settings, "VAPID_PUBLIC_KEY") and hasattr(
            settings, "VAPID_PRIVATE_KEY"
        ):
            return {
                "public_key": settings.VAPID_PUBLIC_KEY,
                "private_key": settings.VAPID_PRIVATE_KEY,
            }

        # Generate new keys if not present
        from py_vapid import Vapid

        vapid = Vapid()
        vapid.generate_keys()

        logger.warning(
            "VAPID keys not found in settings. Generated new keys. "
            "Add these to your settings.py:\n"
            f"VAPID_PUBLIC_KEY = '{vapid.public_key.decode()}'\n"
            f"VAPID_PRIVATE_KEY = '{vapid.private_key.decode()}'"
        )

        return {
            "public_key": vapid.public_key.decode(),
            "private_key": vapid.private_key.decode(),
        }

    @staticmethod
    def get_vapid_public_key_for_browser() -> str:
        """
        Get VAPID public key in base64url format for browser
        Converts PEM format to raw base64url string
        """
        import base64

        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        vapid_keys = PushNotificationService.get_vapid_keys()
        public_key_pem = vapid_keys["public_key"]

        # Load the PEM key
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(), backend=default_backend()
        )

        # Export as raw bytes (uncompressed point format for EC keys)
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        # Convert to base64url (URL-safe base64 without padding)
        base64url = base64.urlsafe_b64encode(public_bytes).decode("utf-8").rstrip("=")

        return base64url

    @staticmethod
    def subscribe_user(
        user: User,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: Optional[str] = None,
    ) -> PushSubscription:
        """
        Subscribe a user to push notifications
        Creates or updates subscription
        """
        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": user,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": user_agent,
                "is_active": True,
                "failure_count": 0,
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} push subscription for user {user.id}")

        return subscription

    @staticmethod
    def unsubscribe_user(user: User, endpoint: str) -> bool:
        """
        Unsubscribe a user from push notifications
        """
        try:
            subscription = PushSubscription.objects.get(user=user, endpoint=endpoint)
            subscription.delete()
            logger.info(f"Deleted push subscription for user {user.id}")
            return True
        except PushSubscription.DoesNotExist:
            logger.warning(f"Push subscription not found for user {user.id}")
            return False

    @staticmethod
    def get_user_subscriptions(
        user: User, active_only: bool = True
    ) -> List[PushSubscription]:
        """
        Get all push subscriptions for a user
        """
        queryset = PushSubscription.objects.filter(user=user)

        if active_only:
            queryset = queryset.filter(is_active=True)

        return list(queryset)

    @staticmethod
    def send_push_notification(
        subscription: PushSubscription,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        tag: Optional[str] = None,
        url: Optional[str] = None,
    ) -> bool:
        """
        Send a push notification to a specific subscription

        Args:
            subscription: PushSubscription object
            title: Notification title
            message: Notification body
            data: Additional data to send
            icon: Icon URL
            badge: Badge URL
            tag: Notification tag (for grouping)
            url: URL to open when clicked

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get VAPID keys
            vapid_keys = PushNotificationService.get_vapid_keys()

            # Prepare subscription info
            subscription_info = {
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            }

            # Prepare notification payload
            payload = {
                "title": title,
                "body": message,
                "icon": icon or "/icon.png",
                "badge": badge or "/badge.png",
                "tag": tag or "notification",
                "data": data or {},
            }

            if url:
                payload["data"]["url"] = url

            # Send push notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid_keys["private_key"],
                vapid_claims={"sub": f"mailto:{settings.DEFAULT_FROM_EMAIL}"},
            )

            # Mark as successful
            subscription.mark_success()
            logger.info(f"Push notification sent to user {subscription.user.id}")
            return True

        except WebPushException as e:
            logger.error(f"WebPush error for user {subscription.user.id}: {str(e)}")

            # Mark as failed
            subscription.mark_failed()

            # If subscription is expired/invalid, deactivate it
            if e.response and e.response.status_code in [404, 410]:
                subscription.is_active = False
                subscription.save(update_fields=["is_active"])
                logger.warning(
                    f"Deactivated invalid subscription for user {subscription.user.id}"
                )

            return False

        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {str(e)}")
            subscription.mark_failed()
            return False

    @staticmethod
    def send_to_user(
        user: User,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        icon: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Send push notification to all active subscriptions of a user

        Returns:
            Dict with success and failure counts
        """
        subscriptions = PushNotificationService.get_user_subscriptions(
            user, active_only=True
        )

        if not subscriptions:
            logger.info(f"No active push subscriptions for user {user.id}")
            return {"success": 0, "failed": 0}

        success_count = 0
        failed_count = 0

        for subscription in subscriptions:
            if PushNotificationService.send_push_notification(
                subscription=subscription,
                title=title,
                message=message,
                data=data,
                icon=icon,
                url=url,
            ):
                success_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Push notifications sent to user {user.id}: "
            f"{success_count} success, {failed_count} failed"
        )

        return {"success": success_count, "failed": failed_count}

    @staticmethod
    def send_to_multiple_users(
        users: List[User],
        title: str,
        message: str,
        data: Optional[Dict] = None,
        icon: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Send push notification to multiple users

        Returns:
            Dict with total success and failure counts
        """
        total_success = 0
        total_failed = 0

        for user in users:
            result = PushNotificationService.send_to_user(
                user=user, title=title, message=message, data=data, icon=icon, url=url
            )
            total_success += result["success"]
            total_failed += result["failed"]

        logger.info(
            f"Bulk push notifications sent: "
            f"{total_success} success, {total_failed} failed"
        )

        return {"success": total_success, "failed": total_failed}

    @staticmethod
    def cleanup_inactive_subscriptions(days: int = 90) -> int:
        """
        Delete inactive subscriptions older than specified days

        Returns:
            Number of subscriptions deleted
        """
        from datetime import timedelta

        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = PushSubscription.objects.filter(
            is_active=False, updated_at__lt=cutoff_date
        ).delete()

        logger.info(f"Cleaned up {deleted_count} inactive push subscriptions")
        return deleted_count
