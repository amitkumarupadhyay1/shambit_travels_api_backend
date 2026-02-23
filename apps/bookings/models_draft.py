"""
PHASE 4: Booking Draft Model

Protocol Compliance:
- §6: Draft persistence with 24h TTL
- Pre-login drafts stored in localStorage
- Post-login drafts stored in database
- Automatic expiration after 24 hours
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from packages.models import Package


class BookingDraft(models.Model):
    """
    Temporary booking draft with 24-hour TTL.

    Lifecycle:
    1. User starts booking (pre-login) → localStorage
    2. User logs in → POST /api/bookings/drafts/ (migrate from localStorage)
    3. User continues editing → PATCH /api/bookings/drafts/{id}/
    4. User completes booking → Convert to Booking, delete draft
    5. After 24h → Auto-expire and delete
    """

    # User (nullable for pre-login drafts that haven't been migrated yet)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        help_text="User who owns this draft. Null for pre-login drafts.",
    )

    # Package reference
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        db_index=True,
        help_text="Package being booked",
    )

    # Draft data (stored as JSON for flexibility)
    draft_data = models.JSONField(
        default=dict,
        help_text="""
        Complete draft state:
        {
            "packageId": int,
            "experiences": [int],
            "days": int,
            "dateRange": {"start": str, "end": str},
            "travellers": [{"id": str, "name": str, "age": int, "gender": str, "isChild": bool}],
            "hotelTier": int,
            "rooms": [{"id": str, "type": str, "occupants": [str]}],
            "vehicles": [{"id": str, "type": str, "passengers": [str]}],
            "pricingEstimate": {"base": float, "experiences": float, "totalEstimate": float},
            "status": str,
            "versionToken": str
        }
        """,
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="Draft expires 24 hours after creation",
    )

    # Migration tracking
    migrated_from_local = models.BooleanField(
        default=False,
        help_text="True if this draft was migrated from localStorage",
    )
    local_storage_key = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Original localStorage key for tracking",
    )

    # Version control
    version = models.IntegerField(
        default=1,
        help_text="Incremented on each update for optimistic locking",
    )

    class Meta:
        db_table = "booking_drafts"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["expires_at", "created_at"]),
            models.Index(fields=["package", "user"]),
        ]
        verbose_name = "Booking Draft"
        verbose_name_plural = "Booking Drafts"

    def __str__(self):
        user_str = self.user.email if self.user else "Anonymous"
        return f"Draft #{self.id} - {user_str} - {self.package.name}"

    def save(self, *args, **kwargs):
        """Set expires_at to 24 hours from now if not set"""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if draft has expired"""
        return timezone.now() > self.expires_at

    def extend_expiry(self, hours=24):
        """Extend expiry by specified hours"""
        self.expires_at = timezone.now() + timedelta(hours=hours)
        self.save(update_fields=["expires_at", "updated_at"])

    def to_booking_data(self):
        """
        Convert draft data to booking creation data.
        Returns dict suitable for BookingCreateSerializer.
        """
        draft = self.draft_data

        return {
            "package_id": draft.get("packageId"),
            "experience_ids": draft.get("experiences", []),
            "hotel_tier_id": draft.get("hotelTier"),
            "transport_option_id": draft.get(
                "transportOptionId"
            ),  # May need to be stored
            "booking_date": draft.get("dateRange", {}).get("start"),
            "booking_end_date": draft.get("dateRange", {}).get("end"),
            "num_travelers": len(draft.get("travellers", [])),
            "traveler_details": [
                {
                    "name": t.get("name"),
                    "age": t.get("age"),
                    "gender": t.get("gender"),
                }
                for t in draft.get("travellers", [])
            ],
            "num_rooms": len(draft.get("rooms", [])),
            "room_allocation": draft.get("rooms", []),
            # Customer info would come from user or form
        }

    @classmethod
    def cleanup_expired(cls):
        """
        Delete all expired drafts.
        Should be called by a periodic task (celery beat).
        """
        expired_count = cls.objects.filter(expires_at__lt=timezone.now()).delete()[0]
        return expired_count

    @classmethod
    def get_user_drafts(cls, user, include_expired=False):
        """Get all drafts for a user"""
        queryset = cls.objects.filter(user=user)
        if not include_expired:
            queryset = queryset.filter(expires_at__gt=timezone.now())
        return queryset.order_by("-updated_at")
