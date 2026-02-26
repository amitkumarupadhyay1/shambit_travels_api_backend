"""
Push Notification Service
Handles sending push notifications via Web Push API
"""

import base64
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
    def _normalize_key(raw_key: str) -> str:
        """
        Normalize key strings from env/config.
        Supports both real newlines and escaped "\\n" sequences.
        """
        return (raw_key or "").strip().replace("\\n", "\n")

    @staticmethod
    def _to_base64url(data: bytes) -> str:
        """Encode bytes as URL-safe base64 without padding."""
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _public_key_to_browser_format(public_key: str) -> str:
        """
        Convert configured public key into browser-required base64url format.

        Supports:
        - PEM public key
        - Existing base64url uncompressed EC point (starts with 0x04 when decoded)
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        normalized = PushNotificationService._normalize_key(public_key)
        if not normalized:
            raise ValueError("VAPID public key is empty")

        if "BEGIN PUBLIC KEY" in normalized:
            key_obj = serialization.load_pem_public_key(
                normalized.encode("utf-8"), backend=default_backend()
            )
            public_bytes = key_obj.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint,
            )
            return PushNotificationService._to_base64url(public_bytes)

        # Already in browser format (base64url EC uncompressed point)
        candidate = normalized.replace("\n", "")
        try:
            padding = "=" * ((4 - len(candidate) % 4) % 4)
            decoded = base64.urlsafe_b64decode(candidate + padding)
            if len(decoded) == 65 and decoded[0] == 0x04:
                return candidate.rstrip("=")
        except Exception:
            pass

        raise ValueError(
            "Invalid VAPID_PUBLIC_KEY format. Expected PEM or base64url EC public key."
        )

    @staticmethod
    def _private_key_to_webpush_format(private_key: str) -> str:
        """
        Convert configured private key into pywebpush/py_vapid input format.

        Supports:
        - PEM private key (converted to raw 32-byte base64url)
        - Existing encoded key accepted by py_vapid
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from py_vapid import Vapid

        normalized = PushNotificationService._normalize_key(private_key)
        if not normalized:
            raise ValueError("VAPID private key is empty")

        if "BEGIN PRIVATE KEY" in normalized:
            key_obj = serialization.load_pem_private_key(
                normalized.encode("utf-8"), password=None, backend=default_backend()
            )
            raw_private = key_obj.private_numbers().private_value.to_bytes(32, "big")
            return PushNotificationService._to_base64url(raw_private)

        candidate = normalized.replace("\n", "").strip()
        # Validate format early to fail with a clear error message.
        Vapid.from_string(candidate)
        return candidate

    @staticmethod
    def get_vapid_keys() -> Dict[str, str]:
        """
        Get normalized VAPID keys for both browser subscription and pywebpush.

        Returns:
            {
                "public_key": "<base64url public key for browser>",
                "private_key": "<base64url/encoded private key for pywebpush>"
            }
        """
        public_key = getattr(settings, "VAPID_PUBLIC_KEY", "")
        private_key = getattr(settings, "VAPID_PRIVATE_KEY", "")

        if public_key and private_key:
            try:
                return {
                    "public_key": PushNotificationService._public_key_to_browser_format(
                        public_key
                    ),
                    "private_key": PushNotificationService._private_key_to_webpush_format(
                        private_key
                    ),
                }
            except Exception as exc:
                logger.error("Invalid VAPID key configuration: %s", exc)
                raise ValueError(f"Invalid VAPID key configuration: {exc}") from exc

        # Generate ephemeral keys only when settings are completely missing.
        from cryptography.hazmat.primitives import serialization
        from py_vapid import Vapid

        vapid = Vapid()
        vapid.generate_keys()
        public_bytes = vapid.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        private_bytes = vapid.private_key.private_numbers().private_value.to_bytes(
            32, "big"
        )
        generated_public_key = PushNotificationService._to_base64url(public_bytes)
        generated_private_key = PushNotificationService._to_base64url(private_bytes)

        logger.warning("VAPID keys missing in settings. Generated ephemeral keys.")

        return {
            "public_key": generated_public_key,
            "private_key": generated_private_key,
        }

    @staticmethod
    def get_vapid_public_key_for_browser() -> str:
        """
        Get VAPID public key in base64url format required by browser PushManager.
        """
        vapid_keys = PushNotificationService.get_vapid_keys()
        return vapid_keys["public_key"]

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
