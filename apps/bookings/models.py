from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from packages.models import Experience, HotelTier, Package, TransportOption


class Booking(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING_PAYMENT", "Pending Payment"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    package = models.ForeignKey(Package, on_delete=models.PROTECT, db_index=True)

    # Snapshot of selections at time of booking
    selected_experiences = models.ManyToManyField(Experience)
    selected_hotel_tier = models.ForeignKey(
        HotelTier, on_delete=models.PROTECT, db_index=True
    )
    selected_transport = models.ForeignKey(
        TransportOption, on_delete=models.PROTECT, db_index=True
    )

    # Booking details
    booking_date = models.DateField(db_index=True, null=True, blank=True)
    num_travelers = models.PositiveIntegerField(default=1)

    # Traveler details with age-based pricing
    traveler_details = models.JSONField(
        default=list,
        blank=True,
        help_text="List of traveler information: [{name, age, gender}, ...]",
    )

    # Customer information (snapshot at booking time)
    customer_name = models.CharField(max_length=255, blank=True, default="")
    customer_email = models.EmailField(blank=True, default="")
    customer_phone = models.CharField(max_length=15, blank=True, default="")
    special_requests = models.TextField(blank=True, default="")

    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, db_index=True
    )  # Per-person price (base price after all calculations)

    total_amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="Total amount paid by customer (per_person_price × chargeable_travelers). This is the actual amount charged to the customer.",
    )  # Actual total amount charged

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True,  # Frequently filtered
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Expiration time for DRAFT bookings (auto-set to 20 minutes after creation)",
    )

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),  # User bookings by status
            models.Index(fields=["status", "created_at"]),  # Status + date ordering
            models.Index(fields=["package", "status"]),  # Package bookings by status
            models.Index(
                fields=["user", "created_at"]
            ),  # User bookings ordered by date
            models.Index(fields=["total_price", "status"]),  # Price analysis by status
            models.Index(fields=["booking_date"]),  # Bookings by travel date
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} - {self.customer_name} - {self.booking_date}"

    def can_transition_to(self, new_status):
        transitions = {
            "DRAFT": ["PENDING_PAYMENT", "EXPIRED", "CANCELLED"],
            "PENDING_PAYMENT": ["CONFIRMED", "CANCELLED", "EXPIRED"],
            "CONFIRMED": ["CANCELLED"],
            "CANCELLED": [],
            "EXPIRED": [],
        }
        return new_status in transitions.get(self.status, [])

    def transition_to(self, new_status):
        """
        Controlled state transition method.
        Validates transition is allowed before updating status.
        Raises ValidationError if transition is not permitted.
        """
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"Cannot transition booking from {self.status} to {new_status}"
            )

        old_status = self.status
        self.status = new_status
        self.save()

        # Log transition for audit trail
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Booking {self.id} transitioned from {old_status} to {new_status}")

        return True

    def save(self, *args, **kwargs):
        """
        Override save to set expires_at for DRAFT bookings.
        """
        # Set expiration time for new DRAFT bookings
        if not self.pk and self.status == "DRAFT" and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=20)

        super().save(*args, **kwargs)

    def is_expired(self):
        """
        Check if DRAFT booking has expired.
        """
        if self.status == "DRAFT" and self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_chargeable_travelers_count(self):
        """
        Calculate number of chargeable travelers (age >= 5).
        Used for age-based pricing validation.
        """
        if not self.traveler_details:
            return self.num_travelers

        return sum(
            1 for traveler in self.traveler_details if traveler.get("age", 0) >= 5
        )

    def is_editable(self):
        """
        Check if booking can be edited.
        Only DRAFT bookings can be edited.
        """
        return self.status == "DRAFT" and not self.is_expired()

    def is_deletable(self):
        """
        Check if booking can be deleted.
        Only DRAFT bookings can be deleted.
        """
        return self.status == "DRAFT"
