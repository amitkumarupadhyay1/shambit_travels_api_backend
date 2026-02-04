from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100, db_index=True)  # Frequently searched
    slug = models.SlugField(unique=True, db_index=True)  # Primary lookup field
    description = models.TextField()
    hero_image = models.ImageField(upload_to="cities/hero/", null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("DRAFT", "Draft"), ("PUBLISHED", "Published")],
        default="DRAFT",
        db_index=True,  # Frequently filtered
    )

    # SEO fields (could be in a separate model, but spec says "seo fields" in city context)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True
    )  # Frequently ordered by
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Cities"
        indexes = [
            models.Index(fields=["status", "created_at"]),  # Common filter combination
            models.Index(fields=["name", "status"]),  # Search + filter combination
        ]

    def __str__(self):
        return self.name


class Highlight(models.Model):
    city = models.ForeignKey(
        City, related_name="highlights", on_delete=models.CASCADE, db_index=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Lucide icon name", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["city"]),  # Foreign key queries
        ]

    def __str__(self):
        return f"{self.city.name} - {self.title}"


class TravelTip(models.Model):
    city = models.ForeignKey(
        City, related_name="travel_tips", on_delete=models.CASCADE, db_index=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["city"]),  # Foreign key queries
        ]

    def __str__(self):
        return f"{self.city.name} - {self.title}"
