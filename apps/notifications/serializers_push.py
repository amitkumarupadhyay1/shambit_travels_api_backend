"""
Push Notification Serializers
"""

from rest_framework import serializers

from .models_push import PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for push subscription
    """

    class Meta:
        model = PushSubscription
        fields = [
            "id",
            "endpoint",
            "p256dh",
            "auth",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]


class PushSubscriptionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating push subscription
    """

    endpoint = serializers.URLField(max_length=500)
    keys = serializers.DictField(child=serializers.CharField())

    def validate_keys(self, value):
        """Validate that keys contain p256dh and auth"""
        if "p256dh" not in value or "auth" not in value:
            raise serializers.ValidationError("Keys must contain 'p256dh' and 'auth'")
        return value


class VAPIDPublicKeySerializer(serializers.Serializer):
    """
    Serializer for VAPID public key response
    """

    public_key = serializers.CharField()


class PushTestSerializer(serializers.Serializer):
    """
    Serializer for testing push notifications
    """

    title = serializers.CharField(max_length=255, default="Test Notification")
    message = serializers.CharField(default="This is a test push notification")
