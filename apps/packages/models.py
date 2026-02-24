from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from cities.models import City


class Experience(models.Model):
    DIFFICULTY_CHOICES = [
        ("EASY", "Easy"),
        ("MODERATE", "Moderate"),
        ("HARD", "Hard"),
    ]

    CATEGORY_CHOICES = [
        ("CULTURAL", "Cultural"),
        ("ADVENTURE", "Adventure"),
        ("FOOD", "Food & Culinary"),
        ("SPIRITUAL", "Spiritual"),
        ("NATURE", "Nature & Wildlife"),
        ("ENTERTAINMENT", "Entertainment"),
        ("EDUCATIONAL", "Educational"),
    ]

    # Basic Information
    name = models.CharField(max_length=200, db_index=True)  # Frequently searched
    description = models.TextField()
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_index=True,
        validators=[
            MinValueValidator(
                0, message="Base price must be at least ₹0 (free experiences allowed)"
            ),
            MaxValueValidator(100000, message="Base price cannot exceed ₹100,000"),
        ],
        help_text="Price in INR (₹0 - ₹100,000). Set to 0 for free experiences.",
    )  # Price filtering

    # New Fields - Phase 1 Enhancement
    is_active = models.BooleanField(default=True, db_index=True)
    featured_image = models.ForeignKey(
        "media_library.Media",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="experiences",
    )
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.5,
        validators=[
            MinValueValidator(0.5, message="Duration must be at least 0.5 hours"),
        ],
        help_text="Duration in hours (minimum 0.5 hours)",
    )
    max_participants = models.IntegerField(
        default=15,
        validators=[
            MinValueValidator(1, message="Must allow at least 1 participant"),
        ],
        help_text="Maximum number of participants (minimum 1)",
    )
    difficulty_level = models.CharField(
        max_length=20, choices=DIFFICULTY_CHOICES, default="EASY", db_index=True
    )
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, db_index=True, default="CULTURAL"
    )
    city = models.ForeignKey(
        City,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="experiences",
        db_index=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["name", "base_price"]),  # Search + price filter
            models.Index(fields=["base_price", "created_at"]),  # Price + date ordering
            models.Index(fields=["category", "is_active"]),  # Category filter
            models.Index(fields=["city", "is_active"]),  # City filter
            models.Index(
                fields=["is_active", "created_at"]
            ),  # Active experiences ordered by date
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class HotelTier(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField()

    # PHASE 1: New pricing fields
    base_price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="Base price per room per night (weekday rate in INR)",
    )
    weekend_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.3,
        help_text="Weekend price multiplier (e.g., 1.3 = 30% increase for Fri-Sun)",
    )
    max_occupancy_per_room = models.IntegerField(
        default=2,
        help_text="Maximum number of people per room",
    )

    # Room types configuration (JSON: {single: price, double: price, family: price})
    room_types = models.JSONField(
        default=dict,
        blank=True,
        help_text='Available room types with prices: {"single": 1500, "double": 1700, "family": 2500}',
    )

    # Amenities list
    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text='List of included amenities: ["WiFi", "Breakfast", "AC", "Pool"]',
    )

    # DEPRECATED: Keep for backward compatibility
    price_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        db_index=True,
        help_text="DEPRECATED: Use base_price_per_night instead. Kept for backward compatibility.",
    )

    class Meta:
        indexes = [
            models.Index(fields=["price_multiplier"]),  # Price tier filtering (legacy)
            models.Index(fields=["base_price_per_night"]),  # New price filtering
        ]
        ordering = ["price_multiplier"]

    def __str__(self):
        return self.name

    def get_effective_price_per_night(self):
        """Get the effective price per night, preferring new field over legacy multiplier"""
        if self.base_price_per_night:
            return self.base_price_per_night
        # Fallback to legacy multiplier (will be removed in future)
        return None


class TransportOption(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_index=True,
        help_text="DEPRECATED: Use base_price_per_day instead. Kept for backward compatibility.",
    )

    # New fields for vehicle optimization
    base_price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="Base price per vehicle per day (24-hour period)",
    )
    passenger_capacity = models.IntegerField(
        default=4,
        help_text="Maximum passenger capacity per vehicle",
    )
    luggage_capacity = models.IntegerField(
        default=3,
        help_text="Maximum luggage pieces per vehicle",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this vehicle type is available for booking",
    )

    class Meta:
        indexes = [
            models.Index(fields=["base_price"]),  # Price filtering (legacy)
            models.Index(fields=["base_price_per_day"]),  # New price filtering
            models.Index(
                fields=["is_active", "base_price_per_day"]
            ),  # Active vehicles by price
        ]
        ordering = ["base_price"]

    def __str__(self):
        return self.name

    def get_effective_price_per_day(self):
        """Get the effective price per day, preferring new field over legacy"""
        if self.base_price_per_day:
            return self.base_price_per_day
        # Fallback to legacy base_price
        return self.base_price


class Package(models.Model):
    city = models.ForeignKey(
        City, related_name="packages", on_delete=models.CASCADE, db_index=True
    )
    name = models.CharField(max_length=200, db_index=True)  # Frequently searched
    slug = models.SlugField(unique=True, db_index=True)  # Primary lookup field
    description = models.TextField()

    # Media Library Integration
    featured_image = models.ForeignKey(
        "media_library.Media",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="packages",
        help_text="Main image for the package displayed in listings and detail pages",
    )

    experiences = models.ManyToManyField(Experience, blank=True)
    hotel_tiers = models.ManyToManyField(HotelTier, blank=True)
    transport_options = models.ManyToManyField(TransportOption, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)  # Frequently filtered
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["city", "is_active"]),  # City packages filter
            models.Index(
                fields=["is_active", "created_at"]
            ),  # Active packages ordered by date
            models.Index(fields=["name", "is_active"]),  # Search + filter combination
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
