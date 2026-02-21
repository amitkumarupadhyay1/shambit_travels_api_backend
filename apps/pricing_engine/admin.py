from django.contrib import admin
from django.utils.html import format_html

from .models import PricingConfiguration, PricingRule


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "rule_type",
        "value_display",
        "target_package",
        "active_from",
        "active_to",
        "is_active",
    ]
    list_filter = ["rule_type", "is_active", "is_percentage", "active_from"]
    search_fields = ["name", "description"]
    date_hierarchy = "active_from"

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "description", "rule_type", "value", "is_percentage")},
        ),
        (
            "Applicability",
            {
                "fields": ("target_package", "is_active"),
                "description": "Leave target_package blank to apply to all packages",
            },
        ),
        (
            "Validity Period",
            {
                "fields": ("active_from", "active_to"),
                "description": "Leave active_to blank for indefinite validity",
            },
        ),
    )

    def value_display(self, obj):
        if obj.is_percentage:
            return f"{obj.value}%"
        return f"₹{obj.value}"

    value_display.short_description = "Value"


@admin.register(PricingConfiguration)
class PricingConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for global pricing configuration.
    This is a singleton model - only one instance exists.
    """

    list_display = [
        "id",
        "chargeable_age_threshold",
        "default_weekend_multiplier",
        "min_advance_booking_days",
        "max_advance_booking_days",
        "updated_at",
        "updated_by",
    ]

    readonly_fields = ["updated_at", "updated_by"]

    fieldsets = (
        (
            "Age-Based Pricing",
            {
                "fields": ("chargeable_age_threshold",),
                "description": format_html(
                    "<p><strong>Chargeable Age Threshold:</strong> Travelers below this age travel free. "
                    "Only travelers at or above this age are charged.</p>"
                    "<p><em>Example: If set to 5, children under 5 years old are free.</em></p>"
                ),
            },
        ),
        (
            "Weekend & Seasonal Pricing",
            {
                "fields": (
                    "default_weekend_multiplier",
                    "weekend_days",
                    "seasonal_pricing_rules",
                ),
                "description": format_html(
                    "<p><strong>Weekend Days:</strong> List of days considered as weekend (0=Monday, 6=Sunday).</p>"
                    "<p><strong>Seasonal Pricing:</strong> JSON format for seasonal rules.</p>"
                    '<p><em>Example: {{"summer": {{"start": "06-01", "end": "08-31", "multiplier": 1.2}}}}</em></p>'
                ),
            },
        ),
        (
            "Booking Policies",
            {
                "fields": ("min_advance_booking_days", "max_advance_booking_days"),
                "description": format_html(
                    "<p><strong>Advance Booking:</strong> Control how far in advance customers can book.</p>"
                    "<p><em>Example: Min=1 (book at least 1 day ahead), Max=365 (book up to 1 year ahead)</em></p>"
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("updated_at", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        # Only allow one instance (singleton)
        return not PricingConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the configuration
        return False

    def save_model(self, request, obj, form, change):
        # Track who updated the configuration
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        # If no config exists, create one and redirect to edit
        if not PricingConfiguration.objects.exists():
            config = PricingConfiguration.get_config()
            from django.shortcuts import redirect
            from django.urls import reverse

            return redirect(
                reverse(
                    "admin:pricing_engine_pricingconfiguration_change", args=[config.pk]
                )
            )
        return super().changelist_view(request, extra_context)
