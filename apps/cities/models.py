from django.db import models


def city_image_upload_path(instance, filename):
    """
    Generate upload path for city images.
    For Railway, we'll use a flat structure to avoid permission issues.
    """
    import os

    # Get file extension
    ext = os.path.splitext(filename)[1]
    # Create a simple filename with city name
    safe_name = instance.slug or instance.name.lower().replace(" ", "_")
    return f"city_{safe_name}_hero{ext}"


class City(models.Model):
    name = models.CharField(max_length=100, db_index=True)  # Frequently searched
    slug = models.SlugField(unique=True, db_index=True)  # Primary lookup field
    description = models.TextField()
    hero_image = models.ImageField(
        upload_to=city_image_upload_path, null=True, blank=True
    )
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

    @property
    def media_gallery(self):
        """
        Get all media files for this city from media library.
        Returns QuerySet of Media objects.
        """
        from django.contrib.contenttypes.models import ContentType

        from media_library.models import Media

        ct = ContentType.objects.get_for_model(self)
        return Media.objects.filter(content_type=ct, object_id=self.id)

    @property
    def featured_media(self):
        """
        Get first media file as featured image.
        Returns Media object or None.
        """
        gallery = self.media_gallery
        return gallery.first() if gallery.exists() else None

    def get_hero_image_url(self):
        """
        Get hero image URL with fallback logic:
        1. Try featured_media from media library
        2. Fall back to hero_image field
        3. Return None if no image available
        """
        if self.featured_media and self.featured_media.file:
            return self.featured_media.file.url
        elif self.hero_image:
            return self.hero_image.url
        return None


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
