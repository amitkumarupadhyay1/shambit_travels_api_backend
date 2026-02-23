"""
Admin configuration for search analytics
"""

from django.contrib import admin
from django.db.models import Avg, Count
from django.utils.html import format_html

from .models import PopularSearch, SearchClick, SearchQuery


class ZeroResultsFilter(admin.SimpleListFilter):
    """Custom filter for zero-result searches"""

    title = "result count"
    parameter_name = "has_results"

    def lookups(self, request, model_admin):
        return (
            ("zero", "Zero results"),
            ("some", "Has results"),
        )

    def queryset(self, request, queryset):
        if self.value() == "zero":
            return queryset.filter(result_count=0)
        if self.value() == "some":
            return queryset.filter(result_count__gt=0)
        return queryset


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """Admin interface for search queries"""

    list_display = [
        "query",
        "result_count",
        "search_time_ms",
        "user_display",
        "categories",
        "timestamp",
        "click_count",
    ]
    list_filter = [
        "categories",
        "timestamp",
        ZeroResultsFilter,
    ]
    search_fields = ["query", "user__email", "ip_address"]
    readonly_fields = [
        "query",
        "user",
        "result_count",
        "search_time_ms",
        "categories",
        "ip_address",
        "user_agent",
        "timestamp",
    ]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def user_display(self, obj):
        """Display user email or 'Anonymous'"""
        if obj.user:
            return obj.user.email
        return format_html('<span style="color: gray;">Anonymous</span>')

    user_display.short_description = "User"

    def click_count(self, obj):
        """Display number of clicks for this search"""
        count = obj.clicks.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>', count
            )
        return format_html('<span style="color: gray;">0</span>')

    click_count.short_description = "Clicks"

    def has_add_permission(self, request):
        """Disable manual creation"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make read-only"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Add analytics summary to changelist"""
        extra_context = extra_context or {}

        # Get statistics
        queryset = self.get_queryset(request)

        # Total searches
        total_searches = queryset.count()

        # Zero result searches
        zero_results = queryset.filter(result_count=0).count()

        # Average results per search
        avg_results = queryset.aggregate(Avg("result_count"))["result_count__avg"] or 0

        # Average search time
        avg_time = queryset.aggregate(Avg("search_time_ms"))["search_time_ms__avg"] or 0

        # Most searched queries (top 10)
        top_queries = (
            queryset.values("query").annotate(count=Count("id")).order_by("-count")[:10]
        )

        extra_context["total_searches"] = total_searches
        extra_context["zero_results"] = zero_results
        extra_context["zero_results_percent"] = (
            round((zero_results / total_searches) * 100, 1) if total_searches > 0 else 0
        )
        extra_context["avg_results"] = round(avg_results, 1)
        extra_context["avg_time"] = round(avg_time, 1)
        extra_context["top_queries"] = top_queries

        return super().changelist_view(request, extra_context)


@admin.register(SearchClick)
class SearchClickAdmin(admin.ModelAdmin):
    """Admin interface for search clicks"""

    list_display = [
        "result_title",
        "result_type",
        "position",
        "search_query_display",
        "timestamp",
    ]
    list_filter = ["result_type", "timestamp"]
    search_fields = ["result_title", "search_query__query"]
    readonly_fields = [
        "search_query",
        "result_type",
        "result_id",
        "result_title",
        "position",
        "timestamp",
    ]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def search_query_display(self, obj):
        """Display the search query"""
        return obj.search_query.query

    search_query_display.short_description = "Search Query"

    def has_add_permission(self, request):
        """Disable manual creation"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make read-only"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Add click analytics to changelist"""
        extra_context = extra_context or {}

        queryset = self.get_queryset(request)

        # Total clicks
        total_clicks = queryset.count()

        # Clicks by type
        clicks_by_type = (
            queryset.values("result_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Most clicked results
        most_clicked = (
            queryset.values("result_title", "result_type")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        extra_context["total_clicks"] = total_clicks
        extra_context["clicks_by_type"] = clicks_by_type
        extra_context["most_clicked"] = most_clicked

        return super().changelist_view(request, extra_context)


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    """Admin interface for popular searches"""

    list_display = [
        "query",
        "search_count",
        "click_count",
        "avg_result_count",
        "click_through_rate",
        "last_searched",
    ]
    search_fields = ["query"]
    readonly_fields = [
        "query",
        "search_count",
        "click_count",
        "avg_result_count",
        "last_searched",
    ]
    ordering = ["-search_count"]

    def click_through_rate(self, obj):
        """Calculate and display click-through rate"""
        if obj.search_count > 0:
            ctr = (obj.click_count / obj.search_count) * 100
            ctr_formatted = f"{ctr:.1f}"
            color = "green" if ctr > 50 else "orange" if ctr > 20 else "red"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color,
                ctr_formatted,
            )
        return format_html('<span style="color: gray;">0%</span>')

    click_through_rate.short_description = "CTR"

    def has_add_permission(self, request):
        """Disable manual creation"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make read-only"""
        return False
