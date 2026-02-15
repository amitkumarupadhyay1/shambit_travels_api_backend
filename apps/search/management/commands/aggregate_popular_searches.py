"""
Management command to aggregate popular searches
Run this periodically (e.g., daily via cron) to update PopularSearch table
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from search.models import PopularSearch, SearchClick, SearchQuery


class Command(BaseCommand):
    help = "Aggregate search queries into popular searches table"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back (default: 30)",
        )
        parser.add_argument(
            "--min-searches",
            type=int,
            default=2,
            help="Minimum number of searches to be considered popular (default: 2)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        min_searches = options["min_searches"]

        self.stdout.write(f"Aggregating searches from last {days} days...")

        # Calculate date threshold
        date_threshold = timezone.now() - timedelta(days=days)

        # Get search queries from the period
        queries = (
            SearchQuery.objects.filter(timestamp__gte=date_threshold)
            .values("query")
            .annotate(
                search_count=Count("id"),
                avg_result_count=Avg("result_count"),
            )
            .filter(search_count__gte=min_searches)
            .order_by("-search_count")
        )

        updated_count = 0
        created_count = 0

        for query_data in queries:
            query_text = query_data["query"]

            # Count clicks for this query
            click_count = SearchClick.objects.filter(
                search_query__query=query_text,
                search_query__timestamp__gte=date_threshold,
            ).count()

            # Update or create popular search
            popular_search, created = PopularSearch.objects.update_or_create(
                query=query_text,
                defaults={
                    "search_count": query_data["search_count"],
                    "click_count": click_count,
                    "avg_result_count": query_data["avg_result_count"],
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully aggregated popular searches: "
                f"{created_count} created, {updated_count} updated"
            )
        )

        # Show top 10
        top_searches = PopularSearch.objects.all()[:10]
        self.stdout.write("\nTop 10 Popular Searches:")
        for i, search in enumerate(top_searches, 1):
            ctr = (
                (search.click_count / search.search_count * 100)
                if search.search_count > 0
                else 0
            )
            self.stdout.write(
                f"  {i}. {search.query} - "
                f"{search.search_count} searches, "
                f"{search.click_count} clicks, "
                f"{ctr:.1f}% CTR"
            )
