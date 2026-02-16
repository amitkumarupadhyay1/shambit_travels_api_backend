from datetime import timedelta

from django.db.models import Case, Count, IntegerField, Q, When
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import (
    NotificationCreateSerializer,
    NotificationListSerializer,
    NotificationSerializer,
    NotificationStatsSerializer,
    NotificationUpdateSerializer,
)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    Production-level notification viewset with comprehensive features:
    - User-specific notifications only
    - Optimized queries with proper indexing
    - Bulk operations for performance
    - Statistics endpoint
    - Filtering and search capabilities
    """

    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.none()  # Default queryset for schema generation

    def get_queryset(self):
        """
        Optimized queryset that only returns user's notifications
        Uses database indexes for performance
        """
        # Prevent errors during schema generation
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")

        # Search in title and message
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )

        # Filter by date range
        days = self.request.query_params.get("days")
        if days:
            try:
                days_int = int(days)
                since_date = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(created_at__gte=since_date)
            except ValueError:
                pass

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == "list":
            return NotificationListSerializer
        elif self.action == "create":
            return NotificationCreateSerializer
        elif self.action in ["partial_update", "update"]:
            return NotificationUpdateSerializer
        return NotificationSerializer

    def perform_create(self, serializer):
        """
        Ensure user is set when creating notifications
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Get notification statistics for the current user
        """
        user_notifications = Notification.objects.filter(user=request.user)

        stats = user_notifications.aggregate(
            total_count=Count("id"),
            unread_count=Count(
                Case(When(is_read=False, then=1), output_field=IntegerField())
            ),
            read_count=Count(
                Case(When(is_read=True, then=1), output_field=IntegerField())
            ),
        )

        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """
        Mark all user's notifications as read
        Bulk update for performance
        """
        updated_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)

        return Response(
            {
                "message": f"Marked {updated_count} notifications as read",
                "updated_count": updated_count,
            }
        )

    @action(detail=False, methods=["post"])
    def mark_all_unread(self, request):
        """
        Mark all user's notifications as unread
        """
        updated_count = Notification.objects.filter(
            user=request.user, is_read=True
        ).update(is_read=False)

        return Response(
            {
                "message": f"Marked {updated_count} notifications as unread",
                "updated_count": updated_count,
            }
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """
        Mark a specific notification as read
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response({"message": "Notification marked as read", "is_read": True})

    @action(detail=True, methods=["post"])
    def mark_unread(self, request, pk=None):
        """
        Mark a specific notification as unread
        """
        notification = self.get_object()
        notification.is_read = False
        notification.save(update_fields=["is_read"])

        return Response({"message": "Notification marked as unread", "is_read": False})

    @action(detail=False, methods=["delete"])
    def clear_read(self, request):
        """
        Delete all read notifications for the user
        """
        deleted_count, _ = Notification.objects.filter(
            user=request.user, is_read=True
        ).delete()

        return Response(
            {
                "message": f"Deleted {deleted_count} read notifications",
                "deleted_count": deleted_count,
            }
        )

    @action(detail=False, methods=["delete"])
    def clear_old(self, request):
        """
        Delete notifications older than specified days (default 30)
        """
        days = request.query_params.get("days", "30")
        try:
            days_int = int(days)
            cutoff_date = timezone.now() - timedelta(days=days_int)

            deleted_count, _ = Notification.objects.filter(
                user=request.user, created_at__lt=cutoff_date
            ).delete()

            return Response(
                {
                    "message": f"Deleted {deleted_count} notifications older than {days_int} days",
                    "deleted_count": deleted_count,
                }
            )
        except ValueError:
            return Response(
                {"error": "Invalid days parameter"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """
        Get recent notifications (last 7 days)
        """
        recent_date = timezone.now() - timedelta(days=7)
        recent_notifications = self.get_queryset().filter(created_at__gte=recent_date)[
            :20
        ]  # Limit to 20 most recent

        serializer = NotificationListSerializer(recent_notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """
        Get only unread notifications
        """
        unread_notifications = self.get_queryset().filter(is_read=False)
        serializer = NotificationListSerializer(unread_notifications, many=True)
        return Response(serializer.data)
