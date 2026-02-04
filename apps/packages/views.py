import logging

from django.shortcuts import get_object_or_404

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from pricing_engine.services.pricing_service import PricingService
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Experience, HotelTier, Package, TransportOption
from .serializers import (
    ExperienceSerializer,
    HotelTierSerializer,
    PackageSerializer,
    TransportOptionSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Packages"])
class PackageViewSet(viewsets.ModelViewSet):
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        # Optimized queryset with select_related and prefetch_related
        return (
            Package.objects.select_related("city")
            .prefetch_related("experiences", "hotel_tiers", "transport_options")
            .filter(is_active=True)
            .order_by("-created_at")
        )

    @extend_schema(
        operation_id="list_packages",
        summary="List all packages",
        description="Retrieve a paginated list of active travel packages with their components.",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search packages by name or description",
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
        responses={200: PackageSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="get_package",
        summary="Get package details",
        description="Retrieve detailed information about a specific package including all available experiences, hotel tiers, and transport options.",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Package slug identifier",
                examples=[
                    OpenApiExample(
                        "Mumbai Heritage Tour", value="mumbai-heritage-tour"
                    ),
                    OpenApiExample("Goa Beach Package", value="goa-beach-package"),
                ],
            ),
        ],
        responses={
            200: PackageSerializer,
            404: OpenApiExample(
                "Package not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        operation_id="get_package_price_range",
        summary="Get package price range",
        description="Get estimated price range for a package based on available components.",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Package slug identifier",
            ),
        ],
        responses={
            200: inline_serializer(
                name="PriceRangeResponse",
                fields={
                    "package": serializers.CharField(),
                    "price_range": inline_serializer(
                        name="PriceRange",
                        fields={
                            "min_price": serializers.DecimalField(
                                max_digits=10, decimal_places=2
                            ),
                            "max_price": serializers.DecimalField(
                                max_digits=10, decimal_places=2
                            ),
                            "currency": serializers.CharField(),
                        },
                    ),
                    "note": serializers.CharField(),
                },
            ),
            500: OpenApiExample(
                "Price calculation error",
                value={"error": "Unable to calculate price range"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Price range response",
                value={
                    "package": "Mumbai Heritage Tour",
                    "price_range": {
                        "min_price": "15000.00",
                        "max_price": "45000.00",
                        "currency": "INR",
                    },
                    "note": "Prices are estimates and may vary based on selected components and active promotions",
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["get"])
    def price_range(self, request, slug=None):
        """
        Get price range estimate for a package
        """
        package = self.get_object()

        try:
            price_range = PricingService.get_price_estimate_range(package)

            return Response(
                {
                    "package": package.name,
                    "price_range": price_range,
                    "note": "Prices are estimates and may vary based on selected components and active promotions",
                }
            )
        except Exception as e:
            logger.error(f"Price range calculation failed for {package.slug}: {str(e)}")
            return Response(
                {"error": "Unable to calculate price range"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        operation_id="calculate_package_price",
        summary="Calculate package price",
        description="Calculate total price for selected package components. This endpoint provides accurate pricing for the frontend to display.",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Package slug identifier",
            ),
        ],
        request=inline_serializer(
            name="PriceCalculationRequest",
            fields={
                "experience_ids": serializers.ListField(
                    child=serializers.IntegerField(),
                    help_text="List of experience IDs to include in the package",
                ),
                "hotel_tier_id": serializers.IntegerField(
                    help_text="Selected hotel tier ID"
                ),
                "transport_option_id": serializers.IntegerField(
                    help_text="Selected transport option ID"
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name="PriceCalculationResponse",
                fields={
                    "total_price": serializers.CharField(),
                    "currency": serializers.CharField(),
                    "breakdown": inline_serializer(
                        name="PriceBreakdown",
                        fields={
                            "experiences": serializers.ListField(
                                child=inline_serializer(
                                    name="ExperiencePrice",
                                    fields={
                                        "id": serializers.IntegerField(),
                                        "name": serializers.CharField(),
                                        "price": serializers.CharField(),
                                    },
                                )
                            ),
                            "hotel_tier": inline_serializer(
                                name="HotelTierPrice",
                                fields={
                                    "id": serializers.IntegerField(),
                                    "name": serializers.CharField(),
                                    "price_multiplier": serializers.CharField(),
                                },
                            ),
                            "transport": inline_serializer(
                                name="TransportPrice",
                                fields={
                                    "id": serializers.IntegerField(),
                                    "name": serializers.CharField(),
                                    "price": serializers.CharField(),
                                },
                            ),
                        },
                    ),
                    "pricing_note": serializers.CharField(),
                },
            ),
            400: OpenApiExample(
                "Invalid request",
                value={"error": "One or more experiences not found"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Price calculation request",
                value={
                    "experience_ids": [1, 3, 5],
                    "hotel_tier_id": 2,
                    "transport_option_id": 1,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Price calculation response",
                value={
                    "total_price": "28500.00",
                    "currency": "INR",
                    "breakdown": {
                        "experiences": [
                            {
                                "id": 1,
                                "name": "Gateway of India Tour",
                                "price": "2500.00",
                            },
                            {"id": 3, "name": "Marine Drive Walk", "price": "1500.00"},
                            {
                                "id": 5,
                                "name": "Bollywood Studio Visit",
                                "price": "4000.00",
                            },
                        ],
                        "hotel_tier": {
                            "id": 2,
                            "name": "4-Star Hotels",
                            "price_multiplier": "2.5",
                        },
                        "transport": {"id": 1, "name": "AC Cab", "price": "3000.00"},
                    },
                    "pricing_note": "This is an estimate. Final price calculated at checkout.",
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def calculate_price(self, request, slug=None):
        """
        Calculate total price for selected package components.
        Frontend uses this to DISPLAY price, never trusts its own calculation.
        """
        package = self.get_object()
        data = request.data

        try:
            experience_ids = data.get("experience_ids", [])
            hotel_tier_id = data.get("hotel_tier_id")
            transport_option_id = data.get("transport_option_id")

            # Get components
            experiences = Experience.objects.filter(id__in=experience_ids)
            hotel_tier = get_object_or_404(HotelTier, id=hotel_tier_id)
            transport_option = get_object_or_404(
                TransportOption, id=transport_option_id
            )

            # Validate all experiences found
            if len(experiences) != len(experience_ids):
                return Response(
                    {"error": "One or more experiences not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate price
            total_price = PricingService.calculate_total(
                package, experiences, hotel_tier, transport_option
            )

            # Break down pricing
            base_experience_price = sum(e.base_price for e in experiences)
            transport_price = transport_option.base_price
            hotel_multiplied = (
                base_experience_price + transport_price
            ) * hotel_tier.price_multiplier

            logger.info(
                f"Price calculated for user {request.user.id}: "
                f"package={package.slug}, total=${total_price}"
            )

            return Response(
                {
                    "total_price": str(total_price),
                    "currency": "INR",
                    "breakdown": {
                        "experiences": [
                            {
                                "id": exp.id,
                                "name": exp.name,
                                "price": str(exp.base_price),
                            }
                            for exp in experiences
                        ],
                        "hotel_tier": {
                            "id": hotel_tier.id,
                            "name": hotel_tier.name,
                            "price_multiplier": str(hotel_tier.price_multiplier),
                        },
                        "transport": {
                            "id": transport_option.id,
                            "name": transport_option.name,
                            "price": str(transport_option.base_price),
                        },
                    },
                    "pricing_note": "This is an estimate. Final price calculated at checkout.",
                }
            )
        except Exception as e:
            logger.error(f"Price calculation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Packages"])
class ExperienceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Experience.objects.all().order_by("name")  # Explicit ordering
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        operation_id="list_experiences",
        summary="List all experiences",
        description="Retrieve a list of all available travel experiences.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(tags=["Packages"])
class HotelTierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HotelTier.objects.all().order_by("price_multiplier")  # Explicit ordering
    serializer_class = HotelTierSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        operation_id="list_hotel_tiers",
        summary="List all hotel tiers",
        description="Retrieve a list of all available hotel tiers with their price multipliers.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(tags=["Packages"])
class TransportOptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TransportOption.objects.all().order_by("base_price")  # Explicit ordering
    serializer_class = TransportOptionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        operation_id="list_transport_options",
        summary="List all transport options",
        description="Retrieve a list of all available transport options with their base prices.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
