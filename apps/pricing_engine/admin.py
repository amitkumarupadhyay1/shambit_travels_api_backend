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
        "gst_rate",
        "platform_fee_rate",
        "default_weekend_multiplier",
        "price_lock_duration_minutes",
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
            "Tax & Fee Configuration (PHASE 3)",
            {
                "fields": ("gst_rate", "platform_fee_rate"),
                "description": format_html(
                    "<p><strong>GST Rate:</strong> Goods and Services Tax percentage applied to bookings.</p>"
                    "<p><strong>Platform Fee:</strong> Platform service fee percentage.</p>"
                    "<p><em>Example: GST=18% (standard rate in India), Platform Fee=2%</em></p>"
                ),
            },
        ),
        (
            "Price Lock & Change Detection (PHASE 3)",
            {
                "fields": (
                    "price_lock_duration_minutes",
                    "price_change_alert_threshold",
                    "enable_price_change_alerts",
                ),
                "description": format_html(
                    "<p><strong>Price Lock Duration:</strong> How long prices are locked after calculation (in minutes).</p>"
                    "<p><strong>Price Change Alert:</strong> Alert admins if price changes by more than this percentage.</p>"
                    "<p><em>Example: Lock=15 minutes, Alert Threshold=5%</em></p>"
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
