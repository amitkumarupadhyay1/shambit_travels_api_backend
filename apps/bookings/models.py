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

    # Booking details - PHASE 1: Updated date fields
    booking_date = models.DateField(
        db_index=True,
        null=True,
        blank=True,
        help_text="DEPRECATED: Use booking_start_date instead. Kept for backward compatibility.",
    )
    booking_start_date = models.DateField(
        db_index=True,
        null=True,
        blank=True,
        help_text="Trip start date",
    )
    booking_end_date = models.DateField(
        db_index=True,
        null=True,
        blank=True,
        help_text="Trip end date",
    )
    num_nights = models.IntegerField(
        default=1,
        help_text="Number of nights (auto-calculated from start/end dates)",
    )
    num_travelers = models.PositiveIntegerField(default=1)

    # Traveler details with age-based pricing
    traveler_details = models.JSONField(
        default=list,
        blank=True,
        help_text="List of traveler information: [{name, age, gender}, ...]",
    )

    # PHASE 1: Room allocation fields
    num_rooms_required = models.IntegerField(
        default=1,
        help_text="Number of rooms booked",
    )
    room_allocation = models.JSONField(
        default=list,
        blank=True,
        help_text='Room allocation details: [{"room_type": "double", "occupants": [traveler_ids]}]',
    )
    room_preferences = models.TextField(
        blank=True,
        default="",
        help_text="User's room preferences or special requests for accommodation",
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

    # PHASE 1: Hotel cost breakdown
    hotel_cost_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hotel cost per night (all rooms combined)",
    )
    total_hotel_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total hotel cost (all nights × all rooms)",
    )

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
        Override save to:
        1. Set expires_at for DRAFT bookings
        2. Auto-calculate num_nights from date range (PHASE 1)
        3. Sync booking_date with booking_start_date for backward compatibility
        """
        # PHASE 1: Auto-calculate num_nights from date range
        if self.booking_start_date and self.booking_end_date:
            delta = self.booking_end_date - self.booking_start_date
            self.num_nights = max(1, delta.days)  # At least 1 night

        # Backward compatibility: sync booking_date with booking_start_date
        if self.booking_start_date and not self.booking_date:
            self.booking_date = self.booking_start_date
        elif self.booking_date and not self.booking_start_date:
            self.booking_start_date = self.booking_date
            # If no end date, default to 1 night
            if not self.booking_end_date:
                self.booking_end_date = self.booking_date + timedelta(days=1)
                self.num_nights = 1

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

    @property
    def booking_reference(self):
        """
        Generate a user-friendly booking reference.
        Format: SB-YYYY-NNNNNN (e.g., SB-2024-000123)
        """
        year = self.created_at.year
        return f"SB-{year}-{str(self.id).zfill(6)}"
