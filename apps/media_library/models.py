from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Media(models.Model):
    file = models.FileField(upload_to="library/")
    alt_text = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)

    # Generic relation to attach media to anything (City, Article, Package)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "media_library"
        verbose_name = "Media"
        verbose_name_plural = "Media"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or (self.file.name if self.file else "Untitled Media")
