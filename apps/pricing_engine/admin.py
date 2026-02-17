from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import PricingRule


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "rule_type_badge",
        "value_display",
        "target_package",
        "status_badge",
        "active_from",
        "active_to",
    ]
    list_filter = ["rule_type", "is_percentage", "is_active", "active_from"]
    search_fields = ["name", "target_package__name"]
    list_editable = []  # Removed is_active from here for better UX
    date_hierarchy = "active_from"

    # Add actions for bulk operations
    actions = ["activate_rules", "deactivate_rules", "duplicate_rule"]

    fieldsets = (
        (
            "Rule Details",
            {
                "fields": ("name", "rule_type", "value", "is_percentage"),
                "description": "Define the pricing rule name, type, and value. "
                "For taxes like GST, use MARKUP type with percentage.",
            },
        ),
        (
            "Targeting",
            {
                "fields": ("target_package",),
                "description": "Leave empty to apply to ALL packages. "
                "Select a specific package to apply only to that package.",
            },
        ),
        (
            "Activation",
            {
                "fields": ("is_active", "active_from", "active_to"),
                "description": "Control when this rule is active. "
                "Leave 'Active To' empty for indefinite duration.",
            },
        ),
    )

    # Make the form more user-friendly
    readonly_fields = []

    def rule_type_badge(self, obj):
        """Display rule type with color badge"""
        if obj.rule_type == "MARKUP":
            color = "orange"
            icon = "+"
        else:
            color = "green"
            icon = "-"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_rule_type_display(),
        )

    rule_type_badge.short_description = "Type"

    def value_display(self, obj):
        """Display value with proper formatting"""
        if obj.is_percentage:
            return format_html(
                '<strong style="color: #0066cc;">{}%</strong>', float(obj.value)
            )
        else:
            return format_html(
                '<strong style="color: #0066cc;">₹{}</strong>',
                f"{float(obj.value):,.2f}",
            )

    value_display.short_description = "Value"

    def status_badge(self, obj):
        """Display active status with badge"""
        now = timezone.now()

        # Check if rule is currently active based on dates
        is_currently_active = (
            obj.is_active
            and obj.active_from <= now
            and (obj.active_to is None or obj.active_to >= now)
        )

        if is_currently_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Active</span>'
            )
        elif obj.is_active and obj.active_from > now:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">⏰ Scheduled</span>'
            )
        elif obj.is_active and obj.active_to and obj.active_to < now:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">⏹ Expired</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✗ Inactive</span>'
            )

    status_badge.short_description = "Status"

    # Bulk actions
    def activate_rules(self, request, queryset):
        """Activate selected pricing rules"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} pricing rule(s) activated successfully.")

    activate_rules.short_description = "✓ Activate selected rules"

    def deactivate_rules(self, request, queryset):
        """Deactivate selected pricing rules"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated} pricing rule(s) deactivated successfully."
        )

    deactivate_rules.short_description = "✗ Deactivate selected rules"

    def duplicate_rule(self, request, queryset):
        """Duplicate selected pricing rules"""
        count = 0
        for rule in queryset:
            rule.pk = None
            rule.name = f"{rule.name} (Copy)"
            rule.is_active = False  # Duplicates start as inactive
            rule.save()
            count += 1
        self.message_user(
            request,
            f"{count} pricing rule(s) duplicated successfully. "
            "Duplicates are inactive by default.",
        )

    duplicate_rule.short_description = "📋 Duplicate selected rules"

    # Add helpful text at the top of the admin page
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Manage Tax & Pricing Rules"
        extra_context["subtitle"] = (
            "💡 Tip: To change GST rate when government updates it, "
            "simply edit the 'GST' rule and update the value. "
            "Changes apply immediately to all new price calculations."
        )
        return super().changelist_view(request, extra_context)
