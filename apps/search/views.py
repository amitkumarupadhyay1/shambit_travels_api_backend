"""
Universal search view with PostgreSQL full-text search and ILIKE fallback
Enhanced with natural language query parsing and analytics tracking
"""

import logging
import re
import time
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, Q
from django.utils import timezone

from articles.models import Article
from cities.models import City
from packages.models import Experience, Package
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PopularSearch, SearchClick, SearchQuery
from .serializers import (
    ArticleSearchSerializer,
    CitySearchSerializer,
    ExperienceSearchSerializer,
    PackageSearchSerializer,
)

logger = logging.getLogger(__name__)


class QueryParser:
    """
    Parse natural language search queries
    Examples:
    - "packages in ayodhya" -> intent: packages, location: ayodhya
    - "hotels in mumbai" -> intent: packages/hotels, location: mumbai
    - "ayodhya packages" -> intent: packages, location: ayodhya
    - "things to do in delhi" -> intent: experiences, location: delhi
    """

    # Location prepositions
    LOCATION_PATTERNS = [
        r"\bin\s+(\w+)",  # "in ayodhya"
        r"\bat\s+(\w+)",  # "at mumbai"
        r"\bnear\s+(\w+)",  # "near delhi"
        r"\baround\s+(\w+)",  # "around varanasi"
        r"(\w+)\s+packages?",  # "ayodhya packages"
        r"(\w+)\s+hotels?",  # "mumbai hotels"
        r"(\w+)\s+tours?",  # "delhi tours"
    ]

    # Intent keywords
    INTENT_KEYWORDS = {
        "packages": [
            "package",
            "packages",
            "tour",
            "tours",
            "trip",
            "trips",
            "hotel",
            "hotels",
        ],
        "experiences": [
            "experience",
            "experiences",
            "activity",
            "activities",
            "things to do",
            "what to do",
        ],
        "cities": ["city", "cities", "destination", "destinations", "place", "places"],
        "articles": [
            "article",
            "articles",
            "blog",
            "blogs",
            "guide",
            "guides",
            "read",
            "reading",
        ],
    }

    @classmethod
    def parse(cls, query):
        """
        Parse query and extract intent and location
        Returns: {
            'original_query': str,
            'location': str or None,
            'intent': str or None (packages, experiences, cities, articles),
            'search_terms': list of str
        }
        """
        query_lower = query.lower().strip()

        # Extract location
        location = None
        for pattern in cls.LOCATION_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1)
                break

        # Extract intent
        intent = None
        for category, keywords in cls.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent = category
                    break
            if intent:
                break

        # Extract search terms (remove common words)
        stop_words = {
            "in",
            "at",
            "near",
            "around",
            "the",
            "a",
            "an",
            "to",
            "do",
            "what",
            "how",
        }
        words = query_lower.split()
        search_terms = [w for w in words if w not in stop_words and len(w) > 2]

        return {
            "original_query": query,
            "location": location,
            "intent": intent,
            "search_terms": search_terms,
        }


class UnifiedSearchView(APIView):
    """
    Universal search across all content types
    Uses ILIKE for simple, reliable search
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Handle search requests with natural language parsing"""
        start_time = time.time()

        # Get query parameters
        query = request.query_params.get("q", "").strip()
        categories = request.query_params.get("categories", "all")
        limit = min(int(request.query_params.get("limit", 10)), 50)

        # Validate query
        if not query:
            return Response(
                {
                    "query": query,
                    "results": {},
                    "total_count": 0,
                    "search_time_ms": 0,
                    "message": 'Query parameter "q" is required.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) < 2:
            return Response(
                {
                    "query": query,
                    "results": {},
                    "total_count": 0,
                    "search_time_ms": 0,
                    "message": "Query too short. Minimum 2 characters required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) > 100:
            return Response(
                {
                    "query": query,
                    "results": {},
                    "total_count": 0,
                    "search_time_ms": 0,
                    "message": "Query too long. Maximum 100 characters allowed.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse natural language query
        parsed_query = QueryParser.parse(query)
        logger.info(f"Parsed query: {parsed_query}")

        # Check cache first
        cache_key = f"search:{query}:{categories}:{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f'Cache hit for search query: "{query}"')
            return Response(cached_result)

        # Perform search across categories
        try:
            results = {}

            if categories in ["all", "packages"]:
                results["packages"] = self._search_packages(query, limit, parsed_query)
            else:
                results["packages"] = []

            if categories in ["all", "cities"]:
                results["cities"] = self._search_cities(query, limit, parsed_query)
            else:
                results["cities"] = []

            if categories in ["all", "articles"]:
                results["articles"] = self._search_articles(query, limit, parsed_query)
            else:
                results["articles"] = []

            if categories in ["all", "experiences"]:
                results["experiences"] = self._search_experiences(
                    query, limit, parsed_query
                )
            else:
                results["experiences"] = []

            total_count = sum(len(v) for v in results.values())
            search_time_ms = round((time.time() - start_time) * 1000, 2)

            response_data = {
                "query": query,
                "parsed_query": parsed_query,  # Include parsed query info
                "results": results,
                "total_count": total_count,
                "search_time_ms": search_time_ms,
                "metadata": {
                    "content_scope": "website_only",
                    "indexed_content_types": [
                        "packages",
                        "cities",
                        "articles",
                        "experiences",
                    ],
                    "natural_language_enabled": True,
                },
            }

            # Cache for 5 minutes
            cache.set(cache_key, response_data, 300)

            # Track search query for analytics
            self._track_search_query(
                request, query, total_count, search_time_ms, categories
            )

            # Log search metrics
            logger.info(
                f'Search: query="{query}" location={parsed_query.get("location")} '
                f'intent={parsed_query.get("intent")} results={total_count} time={search_time_ms}ms'
            )

            return Response(response_data)

        except Exception as e:
            logger.error(f'Search error for query "{query}": {str(e)}', exc_info=True)
            return Response(
                {
                    "query": query,
                    "results": {},
                    "total_count": 0,
                    "search_time_ms": round((time.time() - start_time) * 1000, 2),
                    "error": "An error occurred while searching. Please try again.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _track_search_query(
        self, request, query, result_count, search_time_ms, categories
    ):
        """Track search query for analytics"""
        try:
            # Get user if authenticated
            user = request.user if request.user.is_authenticated else None

            # Get IP address
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0]
            else:
                ip_address = request.META.get("REMOTE_ADDR")

            # Get user agent
            user_agent = request.META.get("HTTP_USER_AGENT", "")

            # Create search query record
            SearchQuery.objects.create(
                query=query,
                user=user,
                result_count=result_count,
                search_time_ms=search_time_ms,
                categories=categories,
                ip_address=ip_address,
                user_agent=user_agent[:500],  # Truncate to avoid overflow
            )

        except Exception as e:
            # Don't fail the search if analytics tracking fails
            logger.error(f"Error tracking search query: {str(e)}")

    def _search_packages(self, query, limit, parsed_query):
        """
        Search packages using ILIKE with natural language support
        Supports queries like "packages in ayodhya" or "hotels in mumbai"
        """
        try:
            # Build base query
            q_filter = Q(name__icontains=query) | Q(description__icontains=query)

            # If location is detected, filter by city
            if parsed_query.get("location"):
                location = parsed_query["location"]
                # Try to find matching city
                city_match = City.objects.filter(
                    name__icontains=location, status="PUBLISHED"
                ).first()

                if city_match:
                    logger.info(f"Filtering packages by city: {city_match.name}")
                    # Filter packages by city AND search terms
                    packages = Package.objects.filter(
                        q_filter, city=city_match, is_active=True
                    )[:limit]
                else:
                    # City not found, search normally but include city name in search
                    packages = Package.objects.filter(
                        Q(name__icontains=query)
                        | Q(description__icontains=query)
                        | Q(city__name__icontains=location),
                        is_active=True,
                    )[:limit]
            else:
                # No location specified, search normally
                packages = Package.objects.filter(q_filter, is_active=True)[:limit]

            # Add fake rank for consistency
            for pkg in packages:
                pkg.rank = 0.5

            serializer = PackageSearchSerializer(
                packages, many=True, context={"query": query}
            )
            return serializer.data

        except Exception as e:
            logger.error(f"Error searching packages: {str(e)}")
            return []

    def _search_cities(self, query, limit, parsed_query):
        """Search cities using ILIKE with natural language support"""
        try:
            # If location is detected, prioritize it
            if parsed_query.get("location"):
                location = parsed_query["location"]
                cities = City.objects.filter(
                    Q(name__icontains=location) | Q(description__icontains=location),
                    status="PUBLISHED",
                )[:limit]
            else:
                cities = City.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query),
                    status="PUBLISHED",
                )[:limit]

            # Add fake rank for consistency
            for city in cities:
                city.rank = 0.5

            serializer = CitySearchSerializer(
                cities, many=True, context={"query": query}
            )
            return serializer.data

        except Exception as e:
            logger.error(f"Error searching cities: {str(e)}")
            return []

    def _search_articles(self, query, limit, parsed_query):
        """Search articles using ILIKE with natural language support"""
        try:
            # Build base query
            q_filter = (
                Q(title__icontains=query)
                | Q(content__icontains=query)
                | Q(author__icontains=query)
            )

            # If location is detected, include it in search
            if parsed_query.get("location"):
                location = parsed_query["location"]
                q_filter |= Q(title__icontains=location) | Q(
                    content__icontains=location
                )

            articles = Article.objects.filter(q_filter, status="PUBLISHED").order_by(
                "-created_at"
            )[:limit]

            # Add fake rank for consistency
            for article in articles:
                article.rank = 0.5

            serializer = ArticleSearchSerializer(
                articles, many=True, context={"query": query}
            )
            return serializer.data

        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            return []

    def _search_experiences(self, query, limit, parsed_query):
        """
        Search experiences using ILIKE with natural language support
        Supports queries like "things to do in delhi"
        """
        try:
            # Build base query
            q_filter = Q(name__icontains=query) | Q(description__icontains=query)

            # If location is detected, filter by city
            if parsed_query.get("location"):
                location = parsed_query["location"]
                # Try to find matching city
                city_match = City.objects.filter(
                    name__icontains=location, status="PUBLISHED"
                ).first()

                if city_match:
                    logger.info(f"Filtering experiences by city: {city_match.name}")
                    experiences = Experience.objects.filter(q_filter, city=city_match)[
                        :limit
                    ]
                else:
                    # City not found, search normally but include city name
                    experiences = Experience.objects.filter(
                        Q(name__icontains=query)
                        | Q(description__icontains=query)
                        | Q(city__name__icontains=location)
                    )[:limit]
            else:
                # No location specified, search normally
                experiences = Experience.objects.filter(q_filter)[:limit]

            # Add fake rank for consistency
            for exp in experiences:
                exp.rank = 0.5

            serializer = ExperienceSearchSerializer(
                experiences, many=True, context={"query": query}
            )
            return serializer.data

        except Exception as e:
            logger.error(f"Error searching experiences: {str(e)}")
            return []


class SearchStatsView(APIView):
    """
    Admin endpoint for search statistics
    GET /api/search/stats/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Get search statistics"""
        try:
            stats = {
                "content_counts": {
                    "packages": Package.objects.filter(is_active=True).count(),
                    "cities": City.objects.filter(status="PUBLISHED").count(),
                    "articles": Article.objects.filter(status="PUBLISHED").count(),
                    "experiences": Experience.objects.count(),
                },
                "total_searchable_items": (
                    Package.objects.filter(is_active=True).count()
                    + City.objects.filter(status="PUBLISHED").count()
                    + Article.objects.filter(status="PUBLISHED").count()
                    + Experience.objects.count()
                ),
                "status": "healthy",
            }

            return Response(stats)

        except Exception as e:
            logger.error(f"Error getting search stats: {str(e)}")
            return Response(
                {"error": "Failed to retrieve search statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SearchAnalyticsView(APIView):
    """
    Admin endpoint for search analytics
    GET /api/search/analytics/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get comprehensive search analytics"""
        try:
            # Get time period from query params (default: last 30 days)
            days = int(request.query_params.get("days", 30))
            date_threshold = timezone.now() - timedelta(days=days)

            # Total searches
            total_searches = SearchQuery.objects.filter(
                timestamp__gte=date_threshold
            ).count()

            # Zero result searches
            zero_results = SearchQuery.objects.filter(
                timestamp__gte=date_threshold, result_count=0
            ).count()

            # Average results per search
            avg_results = (
                SearchQuery.objects.filter(timestamp__gte=date_threshold).aggregate(
                    Avg("result_count")
                )["result_count__avg"]
                or 0
            )

            # Average search time
            avg_time = (
                SearchQuery.objects.filter(timestamp__gte=date_threshold).aggregate(
                    Avg("search_time_ms")
                )["search_time_ms__avg"]
                or 0
            )

            # Total clicks
            total_clicks = SearchClick.objects.filter(
                timestamp__gte=date_threshold
            ).count()

            # Click-through rate
            ctr = (total_clicks / total_searches * 100) if total_searches > 0 else 0

            # Top 20 popular searches
            popular_searches = list(
                SearchQuery.objects.filter(timestamp__gte=date_threshold)
                .values("query")
                .annotate(count=Count("id"), avg_results=Avg("result_count"))
                .order_by("-count")[:20]
            )

            # Zero result queries (top 20)
            zero_result_queries = list(
                SearchQuery.objects.filter(
                    timestamp__gte=date_threshold, result_count=0
                )
                .values("query")
                .annotate(count=Count("id"))
                .order_by("-count")[:20]
            )

            # Searches by category
            searches_by_category = list(
                SearchQuery.objects.filter(timestamp__gte=date_threshold)
                .values("categories")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

            # Clicks by result type
            clicks_by_type = list(
                SearchClick.objects.filter(timestamp__gte=date_threshold)
                .values("result_type")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

            # Most clicked results
            most_clicked = list(
                SearchClick.objects.filter(timestamp__gte=date_threshold)
                .values("result_title", "result_type")
                .annotate(count=Count("id"))
                .order_by("-count")[:20]
            )

            # Search trends (daily counts for the period)
            daily_searches = list(
                SearchQuery.objects.filter(timestamp__gte=date_threshold)
                .extra(select={"day": "date(timestamp)"})
                .values("day")
                .annotate(count=Count("id"))
                .order_by("day")
            )

            analytics_data = {
                "period_days": days,
                "summary": {
                    "total_searches": total_searches,
                    "zero_results": zero_results,
                    "zero_results_percent": round(
                        (
                            (zero_results / total_searches * 100)
                            if total_searches > 0
                            else 0
                        ),
                        2,
                    ),
                    "avg_results_per_search": round(avg_results, 2),
                    "avg_search_time_ms": round(avg_time, 2),
                    "total_clicks": total_clicks,
                    "click_through_rate": round(ctr, 2),
                },
                "popular_searches": popular_searches,
                "zero_result_queries": zero_result_queries,
                "searches_by_category": searches_by_category,
                "clicks_by_type": clicks_by_type,
                "most_clicked_results": most_clicked,
                "daily_trends": daily_searches,
            }

            return Response(analytics_data)

        except Exception as e:
            logger.error(f"Error getting search analytics: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve search analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PopularSearchesView(APIView):
    """
    Public endpoint for popular searches (for autocomplete suggestions)
    GET /api/search/popular/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Get popular searches"""
        try:
            limit = min(int(request.query_params.get("limit", 10)), 50)

            # Get from PopularSearch table (pre-aggregated)
            popular = PopularSearch.objects.all()[:limit]

            results = [
                {
                    "query": p.query,
                    "search_count": p.search_count,
                    "avg_result_count": round(p.avg_result_count, 1),
                }
                for p in popular
            ]

            return Response({"popular_searches": results})

        except Exception as e:
            logger.error(f"Error getting popular searches: {str(e)}")
            return Response(
                {"error": "Failed to retrieve popular searches"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SearchClickTrackingView(APIView):
    """
    Track when users click on search results
    POST /api/search/track-click/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Track a search result click"""
        try:
            # Get data from request
            search_query_id = request.data.get("search_query_id")
            result_type = request.data.get("result_type")
            result_id = request.data.get("result_id")
            result_title = request.data.get("result_title")
            position = request.data.get("position", 0)

            # Validate required fields
            if not all([result_type, result_id, result_title]):
                return Response(
                    {"error": "Missing required fields"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # If search_query_id is provided, link to it
            search_query = None
            if search_query_id:
                try:
                    search_query = SearchQuery.objects.get(id=search_query_id)
                except SearchQuery.DoesNotExist:
                    pass

            # If no search_query_id, try to find recent search
            if not search_query:
                # Get user's most recent search (within last 5 minutes)
                recent_threshold = timezone.now() - timedelta(minutes=5)
                search_query = (
                    SearchQuery.objects.filter(timestamp__gte=recent_threshold)
                    .order_by("-timestamp")
                    .first()
                )

            # Create click record if we have a search query
            if search_query:
                SearchClick.objects.create(
                    search_query=search_query,
                    result_type=result_type,
                    result_id=result_id,
                    result_title=result_title,
                    position=position,
                )

                return Response({"status": "success"})
            else:
                # No search query found, but don't fail
                logger.warning("Click tracked without associated search query")
                return Response(
                    {"status": "success", "warning": "No search query found"}
                )

        except Exception as e:
            logger.error(f"Error tracking search click: {str(e)}")
            return Response(
                {"error": "Failed to track click"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
