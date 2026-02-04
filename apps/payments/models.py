from bookings.models import Booking
from django.db import models


class Payment(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="payment", db_index=True
    )
    razorpay_order_id = models.CharField(
        max_length=255, unique=True, db_index=True
    )  # Primary lookup
    razorpay_payment_id = models.CharField(
        max_length=255, blank=True, db_index=True
    )  # Payment lookups
    razorpay_signature = models.CharField(max_length=255, blank=True)

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, db_index=True
    )  # Amount filtering
    status = models.CharField(
        max_length=20, default="PENDING", db_index=True
    )  # Status filtering

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"]
            ),  # Payment reports by status and date
            models.Index(fields=["amount", "status"]),  # Payment analysis
            models.Index(fields=["booking", "status"]),  # Booking payment status
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.razorpay_order_id
