from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PricingRule(models.Model):
    RULE_TYPE_CHOICES = [
        ("MARKUP", "Markup"),
        ("DISCOUNT", "Discount"),
    ]

    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, default="")
    rule_type = models.CharField(
        max_length=50, choices=RULE_TYPE_CHOICES, db_index=True
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_index=True,
        help_text="Percentage (e.g., 18 for 18%) or fixed amount",
    )
    is_percentage = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True for percentage, False for fixed amount",
    )

    # Applicability
    target_package = models.ForeignKey(
        "packages.Package",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="pricing_rules",
        help_text="Leave blank to apply to all packages",
    )

    # Validity period
    active_from = models.DateTimeField(db_index=True)
    active_to = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Leave blank for indefinite validity",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-active_from"]
        indexes = [
            models.Index(fields=["is_active", "active_from"]),
            models.Index(fields=["target_package", "is_active"]),
            models.Index(fields=["rule_type", "is_active"]),
            models.Index(fields=["active_from", "active_to"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class PricingConfiguration(models.Model):
    """
    PHASE 3: Global pricing configuration settings.
    Singleton model - only one instance should exist.
    """

    # Age-based pricing
    chargeable_age_threshold = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(18)],
        help_text="Minimum age for chargeable travelers (default: 5 years)",
    )

    # Seasonal pricing periods (JSON format)
    seasonal_pricing_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text='Seasonal pricing rules: {"summer": {"start": "06-01", "end": "08-31", "multiplier": 1.2}}',
    )

    # Weekend definition
    weekend_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Days considered as weekend (0=Monday, 6=Sunday). Default: [4, 5, 6] for Fri-Sun",
    )

    # Default values
    default_weekend_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.3,
        validators=[MinValueValidator(1.0), MaxValueValidator(3.0)],
        help_text="Default weekend price multiplier (e.g., 1.3 = 30% increase)",
    )

    # Booking policies
    min_advance_booking_days = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        help_text="Minimum days in advance for booking (default: 1 day)",
    )

    max_advance_booking_days = models.IntegerField(
        default=365,
        validators=[MinValueValidator(1), MaxValueValidator(730)],
        help_text="Maximum days in advance for booking (default: 365 days)",
    )

    # PHASE 3: Tax and Fee Configuration
    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="GST rate in percentage (default: 18%)",
    )

    platform_fee_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Platform fee rate in percentage (default: 2%)",
    )

    # PHASE 3: Price Lock Configuration
    price_lock_duration_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Duration in minutes to lock price for booking (default: 15 minutes)",
    )

    # PHASE 3: Price Change Detection
    price_change_alert_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Alert threshold for price changes in percentage (default: 5%)",
    )

    enable_price_change_alerts = models.BooleanField(
        default=True,
        help_text="Enable admin alerts for significant price changes",
    )

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pricing_config_updates",
    )

    class Meta:
        verbose_name = "Pricing Configuration"
        verbose_name_plural = "Pricing Configuration"

    def __str__(self):
        return f"Pricing Configuration (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        if not self.pk and PricingConfiguration.objects.exists():
            # Update existing instance instead of creating new
            existing = PricingConfiguration.objects.first()
            self.pk = existing.pk

        # Set default weekend days if not set
        if not self.weekend_days:
            self.weekend_days = [4, 5, 6]  # Friday, Saturday, Sunday

        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration instance."""
        config, created = cls.objects.get_or_create(pk=1)
        return config
