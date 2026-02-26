from django.contrib import admin
from django.utils.html import format_html

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Admin interface for managing customer inquiries"""

    list_display = [
        "id",
        "name",
        "email",
        "subject_display",
        "status_badge",
        "created_at",
        "response_time_display",
    ]
    list_filter = ["status", "subject", "created_at"]
    search_fields = ["name", "email", "message", "phone"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "ip_address",
        "user_agent",
        "response_time_display",
    ]

    fieldsets = (
        (
            "Customer Information",
            {
                "fields": ("name", "email", "phone"),
            },
        ),
        (
            "Inquiry Details",
            {
                "fields": ("subject", "message"),
            },
        ),
        (
            "Status & Management",
            {
                "fields": ("status", "admin_notes", "resolved_at"),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                    "response_time_display",
                    "ip_address",
                    "user_agent",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    actions = ["mark_as_in_progress", "mark_as_resolved"]

    def subject_display(self, obj):
        """Display subject with icon"""
        icons = {
            "booking": "📅",
            "package": "📦",
            "support": "🆘",
            "feedback": "💬",
            "other": "❓",
        }
        icon = icons.get(obj.subject, "❓")
        return f"{icon} {obj.get_subject_display()}"

    subject_display.short_description = "Subject"

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            "NEW": "#dc3545",  # Red
            "IN_PROGRESS": "#ffc107",  # Yellow
            "RESOLVED": "#28a745",  # Green
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def response_time_display(self, obj):
        """Display response time in human-readable format"""
        if obj.response_time:
            total_seconds = int(obj.response_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60

            if hours > 24:
                days = hours // 24
                return f"{days} day{'s' if days > 1 else ''}"
            elif hours > 0:
                return f"{hours} hour{'s' if hours > 1 else ''}, {minutes} min"
            else:
                return f"{minutes} minute{'s' if minutes > 1 else ''}"
        return "Not resolved yet"

    response_time_display.short_description = "Response Time"

    def mark_as_in_progress(self, request, queryset):
        """Bulk action to mark inquiries as in progress"""
        updated = queryset.filter(status="NEW").update(status="IN_PROGRESS")
        self.message_user(
            request,
            f"{updated} inquir{'y' if updated == 1 else 'ies'} marked as in progress.",
        )

    mark_as_in_progress.short_description = "Mark selected as In Progress"

    def mark_as_resolved(self, request, queryset):
        """Bulk action to mark inquiries as resolved"""
        count = 0
        for inquiry in queryset.filter(status__in=["NEW", "IN_PROGRESS"]):
            inquiry.mark_resolved()
            count += 1
        self.message_user(
            request, f"{count} inquir{'y' if count == 1 else 'ies'} marked as resolved."
        )

    mark_as_resolved.short_description = "Mark selected as Resolved"

    def has_add_permission(self, request):
        """Disable adding inquiries through admin (use public form)"""
        return False
