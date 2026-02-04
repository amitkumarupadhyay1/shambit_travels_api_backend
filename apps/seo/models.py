from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class SEOData(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    title = models.CharField(max_length=255)
    description = models.TextField()
    keywords = models.CharField(max_length=255, blank=True)
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.TextField(blank=True)
    og_image = models.ImageField(upload_to="seo/", null=True, blank=True)

    structured_data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "SEO Data"
        verbose_name_plural = "SEO Data"

    def __str__(self):
        return f"SEO for {self.content_object}"
