from cities.models import City
from django.db import models


class Experience(models.Model):
    name = models.CharField(max_length=200, db_index=True)  # Frequently searched
    description = models.TextField()
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, db_index=True
    )  # Price filtering
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["name", "base_price"]),  # Search + price filter
            models.Index(fields=["base_price", "created_at"]),  # Price + date ordering
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class HotelTier(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    price_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["price_multiplier"]),  # Price tier filtering
        ]
        ordering = ["price_multiplier"]

    def __str__(self):
        return self.name


class TransportOption(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["base_price"]),  # Price filtering
        ]
        ordering = ["base_price"]

    def __str__(self):
        return self.name


class Package(models.Model):
    city = models.ForeignKey(
        City, related_name="packages", on_delete=models.CASCADE, db_index=True
    )
    name = models.CharField(max_length=200, db_index=True)  # Frequently searched
    slug = models.SlugField(unique=True, db_index=True)  # Primary lookup field
    description = models.TextField()

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
