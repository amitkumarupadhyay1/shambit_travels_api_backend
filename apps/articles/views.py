from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Article
from .serializers import ArticleListSerializer, ArticleSerializer


@extend_schema(tags=["Articles"])
class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        return ArticleSerializer

    def get_queryset(self):
        # Optimized queryset with select_related for ForeignKey relationships
        queryset = Article.objects.select_related("city").filter(status="PUBLISHED")

        city_param = self.request.query_params.get("city", None)
        if city_param:
            # Support both city ID and city slug for flexibility
            if city_param.isdigit():
                queryset = queryset.filter(city_id=city_param)
            else:
                queryset = queryset.filter(city__slug=city_param)

        return queryset.order_by("-created_at")  # Explicit ordering for consistency

    @extend_schema(
        operation_id="list_articles",
        summary="List all articles",
        description="Retrieve a paginated list of published travel articles. Filter by city using the city query parameter.",
        parameters=[
            OpenApiParameter(
                name="city",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter articles by city ID or city slug",
                required=False,
                examples=[
                    OpenApiExample("Mumbai articles by ID", value="1"),
                    OpenApiExample("Mumbai articles by slug", value="mumbai"),
                    OpenApiExample("Delhi articles by slug", value="delhi"),
                ],
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search articles by title or content",
                required=False,
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number for pagination",
                required=False,
            ),
        ],
        responses={200: ArticleListSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Article list response",
                value={
                    "count": 25,
                    "next": "http://api.example.com/api/articles/?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "Top 10 Places to Visit in Mumbai",
                            "slug": "top-10-places-mumbai",
                            "excerpt": "Mumbai, the financial capital of India, offers a perfect blend of modernity and tradition...",
                            "author": "Travel Expert",
                            "city_name": "Mumbai",
                            "meta_title": "Top 10 Places to Visit in Mumbai - Travel Guide",
                            "meta_description": "Discover the best places to visit in Mumbai...",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                        }
                    ],
                },
                response_only=True,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="get_article",
        summary="Get article details",
        description="Retrieve detailed information about a specific article by its slug.",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Article slug identifier",
                examples=[
                    OpenApiExample("Mumbai article", value="top-10-places-mumbai"),
                    OpenApiExample("Delhi article", value="delhi-food-guide"),
                ],
            ),
        ],
        responses={
            200: ArticleSerializer,
            404: OpenApiExample(
                "Article not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Article detail response",
                value={
                    "id": 1,
                    "title": "Top 10 Places to Visit in Mumbai",
                    "slug": "top-10-places-mumbai",
                    "content": "Mumbai, the financial capital of India, offers a perfect blend of modernity and tradition. Here are the top 10 places you must visit...",
                    "author": "Travel Expert",
                    "city_name": "Mumbai",
                    "city_slug": "mumbai",
                    "meta_title": "Top 10 Places to Visit in Mumbai - Travel Guide",
                    "meta_description": "Discover the best places to visit in Mumbai with our comprehensive guide.",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                },
                response_only=True,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
