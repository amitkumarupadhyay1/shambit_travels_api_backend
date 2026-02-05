from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import City
from .serializers import CityContextSerializer, CitySerializer


class CityListView(generics.ListAPIView):
    """
    List all published cities
    """

    queryset = City.objects.filter(status="PUBLISHED").order_by("name")
    serializer_class = CitySerializer
    permission_classes = []  # Allow public access
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    @extend_schema(
        operation_id="list_cities",
        summary="List all cities",
        description="Retrieve a list of all published cities available for travel packages.",
        tags=["Cities"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CityDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific city by ID
    """

    queryset = City.objects.filter(status="PUBLISHED")
    serializer_class = CitySerializer
    permission_classes = []  # Allow public access

    @extend_schema(
        operation_id="get_city",
        summary="Get city details",
        description="Retrieve details of a specific city by ID.",
        tags=["Cities"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CityContextView(APIView):
    permission_classes = []  # Allow public access for SEO/SSR

    @extend_schema(
        operation_id="get_city_context",
        summary="Get city context data",
        description="Retrieve comprehensive city information including highlights, travel tips, articles, and packages for a specific city.",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="City slug identifier",
                examples=[
                    OpenApiExample("Mumbai", value="mumbai"),
                    OpenApiExample("Delhi", value="delhi"),
                    OpenApiExample("Goa", value="goa"),
                ],
            ),
        ],
        responses={
            200: CityContextSerializer,
            404: OpenApiExample(
                "City not found",
                value={"error": "City not found"},
                response_only=True,
            ),
        },
        tags=["Cities"],
        examples=[
            OpenApiExample(
                "Successful response",
                value={
                    "name": "Mumbai",
                    "slug": "mumbai",
                    "description": "The financial capital of India...",
                    "hero_image": "/media/cities/mumbai-hero.jpg",
                    "highlights": [
                        {
                            "title": "Gateway of India",
                            "description": "Iconic monument and tourist attraction",
                            "icon": "landmark",
                        }
                    ],
                    "travel_tips": [
                        {
                            "title": "Best time to visit",
                            "content": "October to February for pleasant weather",
                        }
                    ],
                    "articles": [
                        {
                            "title": "Top 10 Places to Visit in Mumbai",
                            "slug": "top-10-places-mumbai",
                            "author": "Travel Expert",
                            "created_at": "2024-01-15T10:30:00Z",
                        }
                    ],
                    "packages": [
                        {
                            "name": "Mumbai Heritage Tour",
                            "slug": "mumbai-heritage-tour",
                            "description": "Explore the rich history of Mumbai",
                        }
                    ],
                    "gallery": [],
                    "meta_title": "Mumbai Travel Guide - Best Places to Visit",
                    "meta_description": "Discover Mumbai with our comprehensive travel guide...",
                },
                response_only=True,
            ),
        ],
    )
    def get(self, request, slug):
        try:
            # Optimized query with select_related for ForeignKey and prefetch_related for reverse ForeignKeys
            city = (
                City.objects.select_related()
                .prefetch_related(
                    "highlights",  # Reverse ForeignKey
                    "travel_tips",  # Reverse ForeignKey
                    "articles__city",  # Reverse ForeignKey with select_related on nested ForeignKey
                    "packages__city",  # Reverse ForeignKey with select_related on nested ForeignKey
                    "packages__experiences",  # ManyToMany through packages
                    "packages__hotel_tiers",  # ManyToMany through packages
                    "packages__transport_options",  # ManyToMany through packages
                )
                .get(slug=slug, status="PUBLISHED")
            )

            serializer = CityContextSerializer(city)
            return Response(serializer.data)
        except City.DoesNotExist:
            return Response({"error": "City not found"}, status=404)
