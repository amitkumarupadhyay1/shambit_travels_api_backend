"""
Push Notification Views
API endpoints for managing push subscriptions
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models_push import PushSubscription
from .serializers_push import (
    PushSubscriptionCreateSerializer,
    PushSubscriptionSerializer,
    PushTestSerializer,
    VAPIDPublicKeySerializer,
)
from .services.push_service import PushNotificationService


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing push notification subscriptions

    Endpoints:
    - GET /api/notifications/push/subscriptions/ - List user's subscriptions
    - POST /api/notifications/push/subscriptions/ - Create subscription
    - DELETE /api/notifications/push/subscriptions/{id}/ - Delete subscription
    - GET /api/notifications/push/vapid-public-key/ - Get VAPID public key
    - POST /api/notifications/push/test/ - Send test notification
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PushSubscriptionSerializer
    queryset = PushSubscription.objects.none()

    def get_queryset(self):
        """Return only user's subscriptions"""
        if getattr(self, "swagger_fake_view", False):
            return PushSubscription.objects.none()

        return PushSubscription.objects.filter(user=self.request.user, is_active=True)

    def create(self, request):
        """
        Subscribe to push notifications

        Request body:
        {
            "endpoint": "https://...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
        """
        serializer = PushSubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user agent from request
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Create subscription
        subscription = PushNotificationService.subscribe_user(
            user=request.user,
            endpoint=serializer.validated_data["endpoint"],
            p256dh=serializer.validated_data["keys"]["p256dh"],
            auth=serializer.validated_data["keys"]["auth"],
            user_agent=user_agent,
        )

        # Return subscription
        response_serializer = PushSubscriptionSerializer(subscription)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        Unsubscribe from push notifications
        """
        try:
            subscription = self.get_queryset().get(pk=pk)
            subscription.delete()
            return Response(
                {"message": "Subscription deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except PushSubscription.DoesNotExist:
            return Response(
                {"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"], url_path="vapid-public-key")
    def vapid_public_key(self, request):
        """
        Get VAPID public key for push subscription

        Returns:
        {
            "public_key": "..."
        }
        """
        public_key = PushNotificationService.get_vapid_public_key_for_browser()
        serializer = VAPIDPublicKeySerializer({"public_key": public_key})
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def test(self, request):
        """
        Send a test push notification to user

        Request body (optional):
        {
            "title": "Test Notification",
            "message": "This is a test"
        }
        """
        serializer = PushTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Send test notification
        result = PushNotificationService.send_to_user(
            user=request.user,
            title=serializer.validated_data["title"],
            message=serializer.validated_data["message"],
            icon="/icon.png",
            url="/dashboard",
        )

        if result["success"] > 0:
            return Response(
                {
                    "message": "Test notification sent successfully",
                    "success_count": result["success"],
                    "failed_count": result["failed"],
                }
            )
        else:
            errors = result.get("errors", []) if isinstance(result, dict) else []
            first_error = errors[0] if errors else None
            return Response(
                {
                    "error": "Failed to send test notification",
                    "detail": first_error
                    or "No active subscriptions found or all sends failed",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
