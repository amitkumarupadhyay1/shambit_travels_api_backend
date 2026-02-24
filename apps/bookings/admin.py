from django.contrib import admin
from django.utils.html import format_html

from .models import Booking
from .models_draft import BookingDraft


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "booking_reference_display",
        "user",
        "package",
        "status",
        "total_price",
        "created_at",
    ]
    list_filter = ["status", "created_at", "package__city"]
    search_fields = [
        "user__email",
        "user__username",
        "package__name",
        "id",  # Allows searching by booking ID (part of reference)
        "customer_email",  # Search by customer email
        "customer_name",  # Search by customer name
        "customer_phone",  # Search by customer phone
    ]
    search_help_text = "Search by booking reference (e.g., SB-2026-000041), customer name, email, phone, package name, or traveler name"
    readonly_fields = ["created_at", "updated_at", "booking_reference_display"]
    list_editable = ["status"]

    def booking_reference_display(self, obj):
        """Display booking reference in list view"""
        return obj.booking_reference

    booking_reference_display.short_description = "Booking Reference"
    booking_reference_display.admin_order_field = "id"

    def get_search_results(self, request, queryset, search_term):
        """
        Custom search to handle:
        1. Booking reference format (SB-YYYY-NNNNNN)
        2. Traveler names/emails/phones inside JSON field
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        if not search_term:
            return queryset, use_distinct

        # Check if search term matches booking reference format
        if search_term.upper().startswith("SB-"):
            # Extract ID from booking reference: SB-2026-000041 -> 41
            parts = search_term.split("-")
            if len(parts) == 3:
                try:
                    booking_id = int(parts[2])  # Remove leading zeros
                    queryset |= self.model.objects.filter(id=booking_id)
                except (ValueError, IndexError):
                    pass  # Invalid format, ignore

        # Search in traveler_details JSON field
        # This searches for ANY field in the JSON (name, email, phone, etc.)
        # For PostgreSQL: Search for the term anywhere in the JSON structure
        # This will match partial names, emails, phones (e.g., "kirti" matches "Kirti Sharma")
        try:
            # Cast JSON to text and search (works for both PostgreSQL and SQLite)
            from django.db.models import TextField
            from django.db.models.functions import Cast

            # Search in the JSON field by casting to text
            # This will find matches in ANY field: name, email, phone, gender, etc.
            queryset |= self.model.objects.annotate(
                traveler_json_text=Cast("traveler_details", TextField())
            ).filter(traveler_json_text__icontains=search_term)

        except Exception as e:
            # Fallback: Simple contains search
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Traveler search fallback used: {e}")
            queryset |= self.model.objects.filter(
                traveler_details__icontains=search_term
            )

        return queryset, use_distinct

    fieldsets = (
        ("Booking Info", {"fields": ("user", "package", "status", "total_price")}),
        (
            "Selected Components",
            {
                "fields": (
                    "selected_experiences",
                    "selected_hotel_tier",
                    "selected_transport",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    filter_horizontal = ["selected_experiences"]

    def get_queryset(self, request):
        # Optimize admin queryset with select_related and prefetch_related
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user", "package__city", "selected_hotel_tier", "selected_transport"
            )
            .prefetch_related("selected_experiences")
        )


@admin.register(BookingDraft)
class BookingDraftAdmin(admin.ModelAdmin):
    """
    PHASE 4: Admin interface for booking drafts
    """

    list_display = [
        "id",
        "user_email",
        "package",
        "status_badge",
        "version",
        "created_at",
        "expires_at",
        "time_remaining",
    ]
    list_filter = ["migrated_from_local", "created_at", "expires_at", "package"]
    search_fields = [
        "user__email",
        "user__username",
        "package__name",
        "local_storage_key",
    ]
    readonly_fields = ["created_at", "updated_at", "version", "time_remaining_display"]

    fieldsets = (
        (
            "Draft Info",
            {
                "fields": (
                    "user",
                    "package",
                    "version",
                    "migrated_from_local",
                    "local_storage_key",
                )
            },
        ),
        ("Draft Data", {"fields": ("draft_data",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "expires_at",
                    "time_remaining_display",
                ),
            },
        ),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email if obj.user else "Anonymous"

    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"

    def status_badge(self, obj):
        """Display status with color badge"""
        if obj.is_expired():
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">EXPIRED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVE</span>'
            )

    status_badge.short_description = "Status"

    def time_remaining(self, obj):
        """Display time remaining until expiry"""
        from django.utils import timezone

        if obj.is_expired():
            return "Expired"

        delta = obj.expires_at - timezone.now()
        hours = int(delta.total_seconds() / 3600)
        minutes = int((delta.total_seconds() % 3600) / 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    time_remaining.short_description = "Time Left"

    def time_remaining_display(self, obj):
        """Display time remaining in readonly field"""
        return self.time_remaining(obj)

    time_remaining_display.short_description = "Time Remaining"

    def get_queryset(self, request):
        """Optimize admin queryset"""
        return super().get_queryset(request).select_related("user", "package")

    actions = ["extend_expiry_action", "delete_expired_action"]

    def extend_expiry_action(self, request, queryset):
        """Extend expiry for selected drafts"""
        count = 0
        for draft in queryset:
            draft.extend_expiry(hours=24)
            count += 1

        self.message_user(request, f"Extended expiry for {count} draft(s) by 24 hours.")

    extend_expiry_action.short_description = "Extend expiry by 24 hours"

    def delete_expired_action(self, request, queryset):
        """Delete expired drafts"""
        from django.utils import timezone

        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()

        self.message_user(request, f"Deleted {count} expired draft(s).")

    delete_expired_action.short_description = "Delete expired drafts"
