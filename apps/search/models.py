"""
Models for search analytics and tracking
"""

from django.conf import settings
from django.db import models


class SearchQuery(models.Model):
    """Track all search queries for analytics"""

    query = models.CharField(max_length=200, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="search_queries",
    )
    result_count = models.IntegerField(default=0)
    search_time_ms = models.FloatField(default=0)
    categories = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Search Query"
        verbose_name_plural = "Search Queries"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["query", "timestamp"]),
            models.Index(fields=["result_count"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.query} ({self.result_count} results)"


class SearchClick(models.Model):
    """Track which search results users click on"""

    search_query = models.ForeignKey(
        SearchQuery, on_delete=models.CASCADE, related_name="clicks"
    )
    result_type = models.CharField(max_length=50)  # package, city, article, experience
    result_id = models.IntegerField()
    result_title = models.CharField(max_length=255)
    position = models.IntegerField()  # Position in search results
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Search Click"
        verbose_name_plural = "Search Clicks"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["result_type", "result_id"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.result_type}: {self.result_title}"


class PopularSearch(models.Model):
    """Aggregated popular searches (updated periodically)"""

    query = models.CharField(max_length=200, unique=True, db_index=True)
    search_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    avg_result_count = models.FloatField(default=0)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Popular Search"
        verbose_name_plural = "Popular Searches"
        ordering = ["-search_count"]

    def __str__(self):
        return f"{self.query} ({self.search_count} searches)"
