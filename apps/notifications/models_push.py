"""
Push Notification Models
Stores user push subscriptions for Web Push API
"""

from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    """
    Store push notification subscriptions for users
    Supports Web Push API (browser notifications)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        db_index=True,
    )

    # Push subscription endpoint (unique per device/browser)
    endpoint = models.URLField(max_length=500, unique=True)

    # P256DH key for encryption
    p256dh = models.CharField(max_length=255)

    # Auth secret for encryption
    auth = models.CharField(max_length=255)

    # Device/browser info (optional)
    user_agent = models.TextField(blank=True, null=True)

    # Subscription metadata
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Failure tracking
    failure_count = models.IntegerField(default=0)
    last_failure_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["endpoint"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Push subscription for {self.user.email} ({self.endpoint[:50]}...)"

    def mark_failed(self):
        """Mark subscription as failed (increment failure count)"""
        self.failure_count += 1
        self.last_failure_at = models.functions.Now()

        # Deactivate after 3 consecutive failures
        if self.failure_count >= 3:
            self.is_active = False

        self.save(update_fields=["failure_count", "last_failure_at", "is_active"])

    def mark_success(self):
        """Mark subscription as successful (reset failure count)"""
        self.failure_count = 0
        self.last_used_at = models.functions.Now()
        self.save(update_fields=["failure_count", "last_used_at"])
