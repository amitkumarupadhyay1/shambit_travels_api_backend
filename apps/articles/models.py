from django.db import models

from cities.models import City


class Article(models.Model):
    city = models.ForeignKey(
        City, related_name="articles", on_delete=models.CASCADE, db_index=True
    )
    title = models.CharField(max_length=255, db_index=True)  # Frequently searched
    slug = models.SlugField(unique=True, db_index=True)  # Primary lookup field
    content = models.TextField()  # Use rich text in admin
    author = models.CharField(
        max_length=100, blank=True, db_index=True
    )  # Frequently filtered

    status = models.CharField(
        max_length=20,
        choices=[("DRAFT", "Draft"), ("PUBLISHED", "Published")],
        default="DRAFT",
        db_index=True,  # Frequently filtered
    )

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True
    )  # Frequently ordered by
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"]
            ),  # Common filter + order combination
            models.Index(fields=["city", "status"]),  # City articles filter
            models.Index(fields=["author", "status"]),  # Author articles filter
            models.Index(fields=["title", "status"]),  # Search + filter combination
        ]
        ordering = ["-created_at"]  # Default ordering for performance

    def __str__(self):
        return self.title
