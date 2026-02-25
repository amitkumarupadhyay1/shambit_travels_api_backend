from django.contrib import admin, messages
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from .models import Notification
from .models_push import PushSubscription
from .services.notification_service import NotificationService


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user_email",
        "is_read_badge",
        "created_at",
        "message_preview",
    ]
    list_filter = ["is_read", "created_at"]
    search_fields = ["title", "message", "user__email"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    list_per_page = 50

    fieldsets = (
        ("Notification", {"fields": ("user", "title", "message", "is_read")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    actions = ["mark_as_read", "mark_as_unread", "send_bulk_notification"]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Read</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Unread</span>'
            )

    is_read_badge.short_description = "Status"
    is_read_badge.admin_order_field = "is_read"

    def message_preview(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message

    message_preview.short_description = "Message Preview"

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request, f"{updated} notifications marked as read.", messages.SUCCESS
        )

    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(
            request, f"{updated} notifications marked as unread.", messages.SUCCESS
        )

    mark_as_unread.short_description = "Mark selected notifications as unread"

    def send_bulk_notification(self, request, queryset):
        # This action redirects to a custom form for bulk notification
        selected = queryset.values_list("user_id", flat=True)
        request.session["selected_users"] = list(set(selected))
        return redirect("admin:send_bulk_notification")

    send_bulk_notification.short_description = "Send notification to selected users"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "send-bulk/",
                self.admin_site.admin_view(self.send_bulk_notification_view),
                name="send_bulk_notification",
            ),
            path(
                "stats/",
                self.admin_site.admin_view(self.notification_stats_view),
                name="notification_stats",
            ),
        ]
        return custom_urls + urls

    def send_bulk_notification_view(self, request):
        if request.method == "POST":
            title = request.POST.get("title")
            message = request.POST.get("message")
            user_ids = request.session.get("selected_users", [])

            if title and message and user_ids:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                users = User.objects.filter(id__in=user_ids)

                notifications = NotificationService.create_bulk_notifications(
                    list(users), title, message
                )

                self.message_user(
                    request,
                    f"Sent notification to {len(notifications)} users.",
                    messages.SUCCESS,
                )
                return redirect("admin:notifications_notification_changelist")

        user_ids = request.session.get("selected_users", [])
        context = {
            "title": "Send Bulk Notification",
            "user_count": len(user_ids),
            "opts": self.model._meta,
        }
        return render(request, "admin/notifications/send_bulk.html", context)

    def notification_stats_view(self, request):
        stats = Notification.objects.aggregate(
            total=Count("id"),
            read=Count("id", filter=Q(is_read=True)),
            unread=Count("id", filter=Q(is_read=False)),
        )

        context = {
            "title": "Notification Statistics",
            "stats": stats,
            "opts": self.model._meta,
        }
        return render(request, "admin/notifications/stats.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["notification_stats_url"] = "admin:notification_stats"
        return super().changelist_view(request, extra_context)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_email",
        "endpoint_short",
        "is_active",
        "failure_count",
        "created_at",
        "last_used_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["user__email", "endpoint"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "last_used_at",
        "last_failure_at",
        "failure_count",
    ]
    date_hierarchy = "created_at"
    list_per_page = 50

    fieldsets = (
        (
            "Subscription",
            {"fields": ("user", "endpoint", "p256dh", "auth", "is_active")},
        ),
        ("Device Info", {"fields": ("user_agent",)}),
        (
            "Failure Tracking",
            {"fields": ("failure_count", "last_failure_at", "last_used_at")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = [
        "test_push_notification",
        "deactivate_subscriptions",
        "activate_subscriptions",
    ]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def endpoint_short(self, obj):
        """Display shortened endpoint"""
        return f"{obj.endpoint[:50]}..." if len(obj.endpoint) > 50 else obj.endpoint

    endpoint_short.short_description = "Endpoint"

    def test_push_notification(self, request, queryset):
        """Send test push notification to selected subscriptions"""
        from .services.push_service import PushNotificationService

        success_count = 0
        failed_count = 0

        for subscription in queryset:
            if PushNotificationService.send_push_notification(
                subscription=subscription,
                title="Test Notification",
                message="This is a test push notification from admin",
                url="/dashboard",
            ):
                success_count += 1
            else:
                failed_count += 1

        self.message_user(
            request,
            f"Sent test notifications: {success_count} success, {failed_count} failed",
            messages.SUCCESS if success_count > 0 else messages.WARNING,
        )

    test_push_notification.short_description = "Send test push notification"

    def deactivate_subscriptions(self, request, queryset):
        """Deactivate selected subscriptions"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated} subscriptions deactivated", messages.SUCCESS
        )

    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"

    def activate_subscriptions(self, request, queryset):
        """Activate selected subscriptions"""
        updated = queryset.update(is_active=True, failure_count=0)
        self.message_user(
            request, f"{updated} subscriptions activated", messages.SUCCESS
        )

    activate_subscriptions.short_description = "Activate selected subscriptions"
