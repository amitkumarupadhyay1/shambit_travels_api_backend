from django.conf import settings
from django.db import models
from packages.models import Experience, HotelTier, Package, TransportOption


class Booking(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING_PAYMENT", "Pending Payment"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
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

    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, db_index=True
    )  # Price filtering
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True,  # Frequently filtered
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),  # User bookings by status
            models.Index(fields=["status", "created_at"]),  # Status + date ordering
            models.Index(fields=["package", "status"]),  # Package bookings by status
            models.Index(
                fields=["user", "created_at"]
            ),  # User bookings ordered by date
            models.Index(fields=["total_price", "status"]),  # Price analysis by status
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} - {self.user.email}"

    def can_transition_to(self, new_status):
        transitions = {
            "DRAFT": ["PENDING_PAYMENT"],
            "PENDING_PAYMENT": ["CONFIRMED", "CANCELLED"],
            "CONFIRMED": ["CANCELLED"],
            "CANCELLED": [],
        }
        return new_status in transitions.get(self.status, [])
