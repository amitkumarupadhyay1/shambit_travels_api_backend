import logging

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

import bleach
from django_ratelimit.decorators import ratelimit
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
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .cache import cache_response
from .logging import AuditLogger, get_client_ip
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
        queryset = (
            Package.objects.select_related("city")
            .prefetch_related("experiences", "hotel_tiers", "transport_options")
            .filter(is_active=True)
            .order_by("-created_at")
        )

        # Filter by city if provided
        city_id = self.request.query_params.get("city", None)
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        return queryset

    @extend_schema(
        operation_id="list_packages",
        summary="List all packages",
        description="Retrieve a paginated list of active travel packages with their components. Filter by city using the city query parameter. Rate limited to 100 requests per minute per IP. Cached for 5 minutes.",
        parameters=[
            OpenApiParameter(
                name="city",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter packages by city ID",
                required=False,
                examples=[
                    OpenApiExample("Mumbai packages", value=1),
                    OpenApiExample("Delhi packages", value=2),
                ],
            ),
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
        responses={
            200: PackageSerializer(many=True),
            400: inline_serializer(
                name="BadRequest",
                fields={"error": serializers.CharField()},
            ),
            429: inline_serializer(
                name="RateLimitExceeded",
                fields={"error": serializers.CharField()},
            ),
            500: inline_serializer(
                name="ServerError",
                fields={"error": serializers.CharField()},
            ),
        },
    )
    @method_decorator(ratelimit(key="ip", rate="100/m", method="GET", block=True))
    @cache_response(
        timeout=300, key_prefix="packages", vary_on_params=["city", "search", "page"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="get_package",
        summary="Get package details",
        description="Retrieve detailed information about a specific package including all available experiences, hotel tiers, and transport options. Cached for 10 minutes.",
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
    @cache_response(timeout=600, key_prefix="package")
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
                    help_text="Selected transport option ID",
                    required=False,
                    allow_null=True,
                ),
                "start_date": serializers.DateField(
                    required=False, help_text="Trip start date (YYYY-MM-DD)"
                ),
                "end_date": serializers.DateField(
                    required=False, help_text="Trip end date (YYYY-MM-DD)"
                ),
                "num_rooms": serializers.IntegerField(
                    required=False, min_value=1, help_text="Number of rooms"
                ),
                "num_travelers": serializers.IntegerField(
                    required=False, min_value=1, help_text="Number of travelers"
                ),
                "travelers": serializers.ListField(
                    required=False,
                    child=inline_serializer(
                        name="PriceCalculationTraveler",
                        fields={
                            "name": serializers.CharField(),
                            "age": serializers.IntegerField(),
                            "gender": serializers.CharField(required=False),
                        },
                    ),
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
                            "base_experience_total": serializers.CharField(
                                required=False
                            ),
                            "transport_cost": serializers.CharField(required=False),
                            "hotel_multiplier": serializers.CharField(required=False),
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
                                    "base_price_per_night": serializers.CharField(
                                        required=False, allow_null=True
                                    ),
                                },
                            ),
                            "transport": inline_serializer(
                                name="TransportPrice",
                                fields={
                                    "id": serializers.IntegerField(),
                                    "name": serializers.CharField(),
                                    "price": serializers.CharField(),
                                },
                                allow_null=True,
                            ),
                            "subtotal_before_hotel": serializers.CharField(
                                required=False
                            ),
                            "subtotal_after_hotel": serializers.CharField(
                                required=False
                            ),
                            "hotel_cost": serializers.CharField(
                                required=False, allow_null=True
                            ),
                            "hotel_cost_per_night": serializers.CharField(
                                required=False, allow_null=True
                            ),
                            "hotel_num_nights": serializers.IntegerField(
                                required=False
                            ),
                            "hotel_num_rooms": serializers.IntegerField(required=False),
                            "uses_new_hotel_pricing": serializers.BooleanField(
                                required=False
                            ),
                            "num_travelers": serializers.IntegerField(required=False),
                            "base_experience_per_person": serializers.CharField(
                                required=False
                            ),
                            "per_person_price": serializers.CharField(required=False),
                            "total_amount": serializers.CharField(required=False),
                            "chargeable_travelers": serializers.IntegerField(
                                required=False
                            ),
                            "chargeable_age_threshold": serializers.IntegerField(
                                required=False
                            ),
                            "applied_rules": serializers.ListField(
                                required=False,
                                child=inline_serializer(
                                    name="AppliedPriceRule",
                                    fields={
                                        "name": serializers.CharField(),
                                        "type": serializers.CharField(),
                                        "value": serializers.CharField(),
                                        "is_percentage": serializers.BooleanField(),
                                        "amount_applied": serializers.CharField(),
                                    },
                                ),
                            ),
                            "total_markup": serializers.CharField(required=False),
                            "total_discount": serializers.CharField(required=False),
                        },
                    ),
                    "pricing_note": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="PriceCalculationError",
                fields={
                    "error": serializers.CharField(),
                },
            ),
            429: inline_serializer(
                name="RateLimitError",
                fields={
                    "error": serializers.CharField(),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Valid price calculation request",
                value={
                    "experience_ids": [1, 3, 5],
                    "hotel_tier_id": 2,
                    "transport_option_id": 1,
                    "start_date": "2026-03-10",
                    "end_date": "2026-03-12",
                    "num_rooms": 2,
                    "num_travelers": 3,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Successful price calculation",
                value={
                    "total_price": "12543.08",
                    "currency": "INR",
                    "breakdown": {
                        "base_experience_total": "2600.00",
                        "transport_cost": "3000.00",
                        "hotel_multiplier": "2.5",
                        "experiences": [
                            {
                                "id": 1,
                                "name": "Gateway of India Tour",
                                "price": "800.00",
                            },
                            {"id": 3, "name": "Marine Drive Walk", "price": "500.00"},
                        ],
                        "hotel_tier": {
                            "id": 2,
                            "name": "4-Star Hotels",
                            "price_multiplier": "2.5",
                            "base_price_per_night": "2000.00",
                        },
                        "transport": {"id": 1, "name": "AC Cab", "price": "3000.00"},
                        "subtotal_before_hotel": "2600.00",
                        "subtotal_after_hotel": "10800.00",
                        "hotel_cost": "8000.00",
                        "hotel_cost_per_night": "4000.00",
                        "hotel_num_nights": 2,
                        "hotel_num_rooms": 2,
                        "uses_new_hotel_pricing": True,
                        "num_travelers": 3,
                        "base_experience_per_person": "1300.00",
                        "per_person_price": "6271.54",
                        "total_amount": "12543.08",
                        "chargeable_travelers": 2,
                        "chargeable_age_threshold": 5,
                        "applied_rules": [
                            {
                                "name": "GST (18%)",
                                "type": "MARKUP",
                                "value": "18.00",
                                "is_percentage": True,
                                "amount_applied": "1837.08",
                            }
                        ],
                        "total_markup": "2877.08",
                        "total_discount": "1134.00",
                    },
                    "pricing_note": "Price includes all applicable taxes and charges. No hidden fees.",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Error: Empty experience list",
                value={"error": "Please select at least 1 experience"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Too many experiences",
                value={"error": "Maximum 10 experiences can be selected"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Duplicate experience IDs",
                value={"error": "Duplicate experience IDs are not allowed"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Invalid experience ID format",
                value={"error": "All experience IDs must be valid integers"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Missing hotel tier",
                value={"error": "hotel_tier_id is required"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Missing transport option",
                value={"error": "transport_option_id is required"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Experience not found",
                value={"error": "One or more experiences not found or inactive"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Experience not in package",
                value={"error": "Experience ID 99 does not belong to this package"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Rate limit exceeded",
                value={"error": "Rate limit exceeded. Please try again later."},
                response_only=True,
                status_codes=["429"],
            ),
        ],
    )
    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def calculate_price(self, request, slug=None):
        """
        Calculate total price for selected package components.
        Frontend uses this to DISPLAY price, never trusts its own calculation.
        Rate limited to 10 requests per minute per IP to prevent abuse.
        """
        package = self.get_object()
        data = request.data
        ip_address = get_client_ip(request)
        user_id = request.user.id if request.user.is_authenticated else None

        try:
            experience_ids = data.get("experience_ids", [])
            hotel_tier_id = data.get("hotel_tier_id")
            transport_option_id = data.get("transport_option_id")

            # PHASE 2: Optional date range, room count, and traveler count for accurate pricing
            start_date_str = data.get("start_date")
            end_date_str = data.get("end_date")
            num_rooms = data.get("num_rooms", 1)
            num_travelers = data.get(
                "num_travelers", 1
            )  # PHASE 2: Traveler count for experience pricing
            travelers = data.get(
                "travelers"
            )  # PHASE 3: Traveler details with age for age-based pricing

            # Validation 1: Check experience_ids is a list
            if not isinstance(experience_ids, list):
                AuditLogger.log_validation_failure(
                    endpoint="calculate_price",
                    error_type="invalid_type",
                    error_message="experience_ids must be a list",
                    user_id=user_id,
                    ip_address=ip_address,
                    request_data=data,
                )
                return Response(
                    {"error": "experience_ids must be a list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validation 2: Check experience_ids length (1-10)
            if len(experience_ids) < 1:
                AuditLogger.log_validation_failure(
                    endpoint="calculate_price",
                    error_type="min_length",
                    error_message="Please select at least 1 experience",
                    user_id=user_id,
                    ip_address=ip_address,
                    request_data=data,
                )
                return Response(
                    {"error": "Please select at least 1 experience"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(experience_ids) > 10:
                AuditLogger.log_validation_failure(
                    endpoint="calculate_price",
                    error_type="max_length",
                    error_message="Maximum 10 experiences can be selected",
                    user_id=user_id,
                    ip_address=ip_address,
                    request_data=data,
                )
                return Response(
                    {"error": "Maximum 10 experiences can be selected"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validation 3: Check for duplicate experience IDs
            if len(experience_ids) != len(set(experience_ids)):
                AuditLogger.log_validation_failure(
                    endpoint="calculate_price",
                    error_type="duplicate_ids",
                    error_message="Duplicate experience IDs are not allowed",
                    user_id=user_id,
                    ip_address=ip_address,
                    request_data=data,
                )
                return Response(
                    {"error": "Duplicate experience IDs are not allowed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validation 4: Check all IDs are integers
            try:
                experience_ids = [int(id) for id in experience_ids]
            except (ValueError, TypeError):
                AuditLogger.log_validation_failure(
                    endpoint="calculate_price",
                    error_type="invalid_format",
                    error_message="All experience IDs must be valid integers",
                    user_id=user_id,
                    ip_address=ip_address,
                    request_data=data,
                )
                return Response(
                    {"error": "All experience IDs must be valid integers"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validation 5: Check required fields
            if hotel_tier_id is None:
                AuditLogger.log_validation_failure(
                    endpoint="calculate_price",
                    error_type="missing_field",
                    error_message="hotel_tier_id is required",
                    user_id=user_id,
                    ip_address=ip_address,
                    request_data=data,
                )
                return Response(
                    {"error": "hotel_tier_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Get components
            experiences = Experience.objects.filter(
                id__in=experience_ids, is_active=True
            )
            hotel_tier = get_object_or_404(HotelTier, id=hotel_tier_id)

            # Transport is optional - will be selected on review page
            if transport_option_id is None:
                transport_option = None
            else:
                transport_option = get_object_or_404(
                    TransportOption, id=transport_option_id
                )

            # Validation 6: Validate all experiences found and active
            if len(experiences) != len(experience_ids):
                return Response(
                    {"error": "One or more experiences not found or inactive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validation 7: Validate experiences belong to this package
            package_experience_ids = set(
                package.experiences.values_list("id", flat=True)
            )
            for exp_id in experience_ids:
                if exp_id not in package_experience_ids:
                    return Response(
                        {
                            "error": f"Experience ID {exp_id} does not belong to this package"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Calculate price with detailed breakdown
            # PHASE 2: Pass date range and room count if provided
            start_date = None
            end_date = None

            if start_date_str and end_date_str:
                from datetime import datetime

                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                    # Validate date range
                    if end_date <= start_date:
                        return Response(
                            {"error": "End date must be after start date"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                except ValueError:
                    return Response(
                        {"error": "Invalid date format. Use YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            breakdown = PricingService.get_price_breakdown(
                package,
                experiences,
                hotel_tier,
                transport_option,
                travelers=travelers,  # PHASE 3: Pass traveler details for age-based pricing
                start_date=start_date,
                end_date=end_date,
                num_rooms=num_rooms,
                num_travelers=num_travelers,  # PHASE 2: Pass traveler count
            )

            total_price = breakdown["final_total"]

            # Audit log successful price calculation
            AuditLogger.log_price_calculation(
                user_id=user_id,
                package_slug=package.slug,
                experience_count=len(experience_ids),
                total_price=float(total_price),
                ip_address=ip_address,
                success=True,
            )

            logger.info(
                f"Price calculated for user {user_id or 'anonymous'}: "
                f"package={package.slug}, experiences={len(experience_ids)}, total={total_price}"
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
                            # PHASE 2: Add new pricing fields
                            "base_price_per_night": (
                                str(hotel_tier.base_price_per_night)
                                if hotel_tier.base_price_per_night
                                else None
                            ),
                        },
                        "transport": (
                            {
                                "id": transport_option.id,
                                "name": transport_option.name,
                                "price": str(transport_option.base_price),
                            }
                            if transport_option
                            else None
                        ),
                        "base_experience_total": str(
                            breakdown["base_experience_total"]
                        ),
                        "transport_cost": str(breakdown["transport_cost"]),
                        "hotel_multiplier": str(breakdown["hotel_multiplier"]),
                        # NEW: Detailed pricing breakdown including taxes
                        "subtotal_before_hotel": str(
                            breakdown["subtotal_before_hotel"]
                        ),
                        "subtotal_after_hotel": str(breakdown["subtotal_after_hotel"]),
                        # PHASE 2: Hotel cost breakdown
                        "hotel_cost": (
                            str(breakdown["hotel_cost"])
                            if breakdown.get("hotel_cost")
                            else None
                        ),
                        "hotel_cost_per_night": (
                            str(breakdown["hotel_cost_per_night"])
                            if breakdown.get("hotel_cost_per_night")
                            else None
                        ),
                        "hotel_num_nights": breakdown.get("hotel_num_nights", 1),
                        "hotel_num_rooms": breakdown.get("hotel_num_rooms", 1),
                        "uses_new_hotel_pricing": breakdown.get(
                            "uses_new_hotel_pricing", False
                        ),
                        # PHASE 2: Traveler count
                        "num_travelers": breakdown.get("num_travelers", 1),
                        "base_experience_per_person": str(
                            breakdown.get("base_experience_per_person", "0.00")
                        ),
                        "per_person_price": str(
                            breakdown.get("per_person_price", "0.00")
                        ),
                        "total_amount": str(
                            breakdown.get("total_amount", breakdown["final_total"])
                        ),
                        # PHASE 3: Age-based pricing
                        "chargeable_travelers": breakdown.get(
                            "chargeable_travelers", breakdown.get("num_travelers", 1)
                        ),
                        "chargeable_age_threshold": breakdown.get(
                            "chargeable_age_threshold",
                            PricingService.get_chargeable_age_threshold(),
                        ),
                        # End PHASE 2
                        "applied_rules": breakdown["applied_rules"],
                        "total_markup": str(breakdown["total_markup"]),
                        "total_discount": str(breakdown["total_discount"]),
                    },
                    "pricing_note": "Price includes all applicable taxes and charges. No hidden fees.",
                }
            )
        except Exception as e:
            # Audit log failed price calculation
            AuditLogger.log_price_calculation(
                user_id=user_id,
                package_slug=package.slug,
                experience_count=len(data.get("experience_ids", [])),
                total_price=0,
                ip_address=ip_address,
                success=False,
                error=str(e),
            )
            logger.error(f"Price calculation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExperienceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["city", "category", "difficulty_level", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "base_price", "created_at", "duration_hours"]
    ordering = ["name"]

    def get_queryset(self):
        # Optimized queryset with select_related and filter active by default
        queryset = Experience.objects.select_related("city", "featured_image").filter(
            is_active=True
        )

        # Sanitize search query to prevent XSS/SQL injection
        search_query = self.request.query_params.get("search", "")
        if search_query:
            # Sanitize the search input
            search_query = bleach.clean(
                search_query, tags=[], attributes={}, strip=True
            ).strip()
            # Limit search query length
            search_query = search_query[:100]
            if search_query:
                # Store sanitized query back for DRF's search filter
                self.request.query_params._mutable = True
                self.request.query_params["search"] = search_query
                self.request.query_params._mutable = False

        # Allow filtering by price range
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        return queryset.order_by(self.ordering[0])

    @extend_schema(
        operation_id="list_experiences",
        summary="List all experiences",
        description="""
        Retrieve a paginated list of active travel experiences.
          # noqa: W293
        **Filtering:**
        - `city`: Filter by city ID
        - `category`: Filter by category (CULTURAL, ADVENTURE, FOOD, SPIRITUAL, NATURE, ENTERTAINMENT, EDUCATIONAL)
        - `difficulty_level`: Filter by difficulty (EASY, MODERATE, HARD)
        - `min_price`: Minimum price filter
        - `max_price`: Maximum price filter
        - `search`: Search in name and description
          # noqa: W293
        **Sorting:**
        - `ordering`: Sort by field (name, base_price, created_at, duration_hours)
        - Prefix with `-` for descending order (e.g., `-base_price`)
          # noqa: W293
        **Caching:** Responses cached for 5 minutes
        """,
        parameters=[
            OpenApiParameter(
                name="city",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by city ID",
                required=False,
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by category",
                required=False,
            ),
            OpenApiParameter(
                name="difficulty_level",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by difficulty level",
                required=False,
            ),
            OpenApiParameter(
                name="min_price",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                description="Minimum price",
                required=False,
            ),
            OpenApiParameter(
                name="max_price",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                description="Maximum price",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search in name and description",
                required=False,
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort field (name, base_price, created_at, duration_hours)",
                required=False,
            ),
        ],
        responses={
            200: ExperienceSerializer(many=True),
            429: OpenApiExample(
                "Rate limit exceeded",
                value={"error": "Rate limit exceeded. Please try again later."},
                response_only=True,
            ),
        },
    )
    @method_decorator(ratelimit(key="ip", rate="100/m", method="GET", block=True))
    @cache_response(
        timeout=300,
        key_prefix="experiences",
        vary_on_params=[
            "city",
            "category",
            "difficulty_level",
            "min_price",
            "max_price",
            "search",
            "ordering",
            "page",
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="get_experience",
        summary="Get experience details",
        description="Retrieve detailed information about a specific experience.",
        responses={
            200: ExperienceSerializer,
            404: OpenApiExample(
                "Experience not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


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
