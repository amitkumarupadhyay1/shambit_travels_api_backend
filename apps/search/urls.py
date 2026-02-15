"""
URL configuration for search app
"""

from django.urls import path

from .views import (
    PopularSearchesView,
    SearchAnalyticsView,
    SearchClickTrackingView,
    SearchStatsView,
    UnifiedSearchView,
)

app_name = "search"

urlpatterns = [
    path("", UnifiedSearchView.as_view(), name="unified-search"),
    path("stats/", SearchStatsView.as_view(), name="search-stats"),
    path("analytics/", SearchAnalyticsView.as_view(), name="search-analytics"),
    path("popular/", PopularSearchesView.as_view(), name="popular-searches"),
    path("track-click/", SearchClickTrackingView.as_view(), name="track-click"),
]
