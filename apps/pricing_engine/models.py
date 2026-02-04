from django.db import models
from packages.models import Package


class PricingRule(models.Model):
    RULE_TYPES = [
        ("MARKUP", "Markup"),
        ("DISCOUNT", "Discount"),
    ]

    name = models.CharField(max_length=100, db_index=True)  # Rule name searching
    rule_type = models.CharField(
        max_length=50, choices=RULE_TYPES, db_index=True
    )  # Rule type filtering
    value = models.DecimalField(
        max_digits=10, decimal_places=2, db_index=True
    )  # Value filtering
    is_percentage = models.BooleanField(
        default=True, db_index=True
    )  # Percentage vs fixed filtering

    # Optional target filtering
    target_package = models.ForeignKey(
        Package, null=True, blank=True, on_delete=models.CASCADE, db_index=True
    )

    active_from = models.DateTimeField(db_index=True)  # Date range filtering
    active_to = models.DateTimeField(
        null=True, blank=True, db_index=True
    )  # Date range filtering
    is_active = models.BooleanField(
        default=True, db_index=True
    )  # Active rule filtering

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "active_from"]),  # Active rules by date
            models.Index(
                fields=["target_package", "is_active"]
            ),  # Package-specific active rules
            models.Index(fields=["rule_type", "is_active"]),  # Rule type filtering
            models.Index(fields=["active_from", "active_to"]),  # Date range queries
        ]
        ordering = ["-active_from"]

    def __str__(self):
        return self.name
