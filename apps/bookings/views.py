import logging

from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from payments.services.payment_service import RazorpayService
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking
from .serializers import (
    BookingCreateResponseSerializer,
    BookingCreateSerializer,
    BookingPreviewSerializer,
    BookingSerializer,
    BookingUpdateSerializer,
)
from .services.booking_service import BookingService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Bookings"])
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.none()  # Default queryset for schema generation

    def get_permissions(self):
        """
        Override permissions for specific actions.
        Preview endpoint should be public (like calculate_price).
        """
        if self.action == "preview":
            from rest_framework.permissions import AllowAny

            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        # Prevent errors during schema generation
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        return (
            Booking.objects.select_related(
                "user", "package__city", "selected_hotel_tier", "selected_transport"
            )
            .prefetch_related(
                "selected_experiences",
                "package__experiences",
                "package__hotel_tiers",
                "package__transport_options",
            )
            .filter(user=self.request.user)
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        elif self.action in ["update", "partial_update", "update_draft"]:
            return BookingUpdateSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        operation_id="list_bookings",
        summary="List user bookings",
        description="Retrieve a paginated list of bookings for the authenticated user.",
        responses={200: BookingSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="create_booking",
        summary="Create new booking",
        description="Create a new booking for a travel package with selected components. Requires Idempotency-Key header to prevent duplicate bookings.",
        request=BookingCreateSerializer,
        responses={
            201: BookingCreateResponseSerializer,
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid booking data"},
                response_only=True,
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create booking with idempotency enforcement"""
        from django.core.cache import cache

        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {"error": "Idempotency-Key header is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already processed
        cache_key = f"booking_idempotency:{idempotency_key}:{request.user.id}"
        cached_response = cache.get(cache_key)

        if cached_response:
            logger.info(
                f"Idempotent request detected: {idempotency_key} for user {request.user.id}"
            )
            return Response(cached_response, status=status.HTTP_200_OK)

        # Process booking
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save(user=request.user)
        response_serializer = BookingCreateResponseSerializer(booking)
        response_data = response_serializer.data

        # Cache for 24 hours
        cache.set(cache_key, response_data, timeout=86400)

        logger.info(
            f"Booking {booking.id} created with idempotency key: {idempotency_key}"
        )

        return Response(response_data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="get_booking",
        summary="Get booking details",
        description="Retrieve detailed information about a specific booking.",
        responses={
            200: BookingSerializer,
            404: OpenApiExample(
                "Booking not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        operation_id="update_booking",
        summary="Update booking (PREVENTED for CONFIRMED)",
        description="Update booking details. CONFIRMED bookings cannot be modified.",
        request=BookingUpdateSerializer,
        responses={
            200: BookingSerializer,
            403: OpenApiExample(
                "Cannot modify confirmed booking",
                value={
                    "error": "Confirmed bookings cannot be modified. Please contact support."
                },
                response_only=True,
            ),
        },
    )
    def update(self, request, *args, **kwargs):
        """Prevent updates to CONFIRMED bookings"""
        booking = self.get_object()

        if booking.status == "CONFIRMED":
            return Response(
                {
                    "error": "Confirmed bookings cannot be modified. Please contact support."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status != "DRAFT":
            return Response(
                {"error": "Only DRAFT bookings can be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)

    @extend_schema(
        operation_id="partial_update_booking",
        summary="Partially update booking (PREVENTED for CONFIRMED)",
        description="Partially update booking details. CONFIRMED bookings cannot be modified.",
        request=BookingUpdateSerializer,
        responses={
            200: BookingSerializer,
            403: OpenApiExample(
                "Cannot modify confirmed booking",
                value={
                    "error": "Confirmed bookings cannot be modified. Please contact support."
                },
                response_only=True,
            ),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """Prevent partial updates to CONFIRMED bookings"""
        booking = self.get_object()

        if booking.status == "CONFIRMED":
            return Response(
                {
                    "error": "Confirmed bookings cannot be modified. Please contact support."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status != "DRAFT":
            return Response(
                {"error": "Only DRAFT bookings can be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        operation_id="delete_booking",
        summary="Delete DRAFT booking",
        description="Delete a DRAFT booking. Only DRAFT bookings can be deleted.",
        responses={
            204: OpenApiExample(
                "Booking deleted",
                value=None,
                response_only=True,
            ),
            403: OpenApiExample(
                "Cannot delete",
                value={"error": "Only DRAFT bookings can be deleted"},
                response_only=True,
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete DRAFT booking only"""
        booking = self.get_object()

        if not booking.is_deletable():
            return Response(
                {"error": "Only DRAFT bookings can be deleted"},
                status=status.HTTP_403_FORBIDDEN,
            )

        booking_id = booking.id
        booking.delete()
        logger.info(f"Booking {booking_id} deleted by user {request.user.id}")

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="initiate_booking_payment",
        summary="Initiate payment for booking",
        description="Create a Razorpay order for the booking and transition it to pending payment status. Validates that the booking price has not changed.",
        responses={
            200: inline_serializer(
                name="PaymentInitiationResponse",
                fields={
                    "razorpay_order_id": serializers.CharField(),
                    "amount": serializers.IntegerField(
                        help_text="Amount in paise (INR)"
                    ),
                    "currency": serializers.CharField(),
                    "booking_id": serializers.IntegerField(),
                },
            ),
            400: OpenApiExample(
                "Payment initiation failed",
                value={"error": "Payment can only be initiated for draft bookings"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Payment initiation response",
                value={
                    "razorpay_order_id": "order_ABC123XYZ",
                    "amount": 2850000,  # 28,500 INR in paise
                    "currency": "INR",
                    "booking_id": 123,
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    def initiate_payment(self, request, pk=None):
        """
        Create Razorpay order for the booking.
        NOW VALIDATES PRICE BEFORE CREATING ORDER.
        Allows retry for PENDING_PAYMENT bookings.
        """
        booking = self.get_object()

        # Allow DRAFT and PENDING_PAYMENT (for retries)
        if booking.status not in ["DRAFT", "PENDING_PAYMENT"]:
            return Response(
                {"error": f"Payment cannot be initiated for {booking.status} bookings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # COMPREHENSIVE PRICE VALIDATION
        is_valid, error_message = BookingService.validate_price(booking)
        if not is_valid:
            logger.error(
                f"Price validation failed for booking {booking.id}: {error_message}"
            )
            return Response(
                {
                    "error": f"Booking validation failed: {error_message}. Please refresh and try again."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                razorpay_service = RazorpayService()
                order = razorpay_service.create_order(booking)

                # Update booking status only if it's DRAFT
                if booking.status == "DRAFT":
                    BookingService.transition_status(booking, "PENDING_PAYMENT")

            logger.info(
                f"Payment initiated for booking {booking.id}: "
                f"razorpay_order_id={order['id']}, amount={order['amount']}"
            )

            return Response(
                {
                    "razorpay_order_id": order["id"],
                    "amount": order["amount"],
                    "currency": order["currency"],
                    "booking_id": booking.id,
                }
            )
        except Exception as e:
            logger.error(
                f"Payment initiation failed for booking {booking.id}: {str(e)}"
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="preview_booking",
        summary="Preview booking price",
        description="Calculate booking price with traveler details WITHOUT creating a booking. Used on review page to show accurate age-based pricing.",
        request=BookingPreviewSerializer,
        responses={
            200: inline_serializer(
                name="BookingPreviewResponse",
                fields={
                    "per_person_price": serializers.DecimalField(
                        max_digits=12, decimal_places=2
                    ),
                    "num_travelers": serializers.IntegerField(),
                    "chargeable_travelers": serializers.IntegerField(),
                    "total_amount": serializers.DecimalField(
                        max_digits=12, decimal_places=2
                    ),
                    "price_breakdown": serializers.DictField(),
                },
            ),
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid preview data"},
                response_only=True,
            ),
        },
    )
    @action(detail=False, methods=["post"])
    def preview(self, request):
        """
        Preview booking price with traveler details.
        Does NOT create booking - only calculates price.
        """
        serializer = BookingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from packages.models import Experience, HotelTier, Package, TransportOption
        from pricing_engine.services.pricing_service import PricingService

        # Get validated data
        data = serializer.validated_data
        package = Package.objects.get(id=data["package_id"])
        experiences = Experience.objects.filter(id__in=data["selected_experience_ids"])
        hotel_tier = HotelTier.objects.get(id=data["hotel_tier_id"])
        transport_option = TransportOption.objects.get(id=data["transport_option_id"])
        traveler_details = data.get("traveler_details", [])

        # Calculate price with traveler details
        breakdown = PricingService.get_price_breakdown(
            package=package,
            experiences=experiences,
            hotel_tier=hotel_tier,
            transport_option=transport_option,
            travelers=traveler_details if traveler_details else None,
        )

        # Get per-person price (final_total from breakdown)
        per_person_price = breakdown["final_total"]

        # Get total amount and chargeable travelers from breakdown
        num_travelers = data["num_travelers"]
        chargeable_count = breakdown.get("chargeable_travelers", num_travelers)
        total_amount = breakdown.get("total_amount", per_person_price * num_travelers)

        logger.info(
            f"Preview calculated: per_person={per_person_price}, "
            f"num_travelers={num_travelers}, chargeable={chargeable_count}, "
            f"total={total_amount}"
        )

        return Response(
            {
                "per_person_price": str(per_person_price),
                "num_travelers": num_travelers,
                "chargeable_travelers": chargeable_count,
                "total_amount": str(total_amount),
                "chargeable_age_threshold": breakdown.get(
                    "chargeable_age_threshold", 5
                ),
                "price_breakdown": {
                    "base_experience_total": str(breakdown["base_experience_total"]),
                    "transport_cost": str(breakdown["transport_cost"]),
                    "subtotal_before_hotel": str(breakdown["subtotal_before_hotel"]),
                    "hotel_multiplier": str(breakdown["hotel_multiplier"]),
                    "subtotal_after_hotel": str(breakdown["subtotal_after_hotel"]),
                    "total_markup": str(breakdown["total_markup"]),
                    "total_discount": str(breakdown["total_discount"]),
                    "applied_rules": breakdown["applied_rules"],
                    "experiences": [
                        {
                            "id": exp.id,
                            "name": exp.name,
                            "price": str(exp.base_price),
                        }
                        for exp in experiences
                    ],
                    "hotel_tier": {
                        "name": hotel_tier.name,
                        "multiplier": str(hotel_tier.price_multiplier),
                    },
                    "transport": {
                        "name": transport_option.name,
                        "price": str(transport_option.base_price),
                    },
                    "currency": "INR",
                    "currency_symbol": "₹",
                },
            }
        )

    @extend_schema(
        operation_id="cancel_booking",
        summary="Cancel booking",
        description="Cancel a booking if it is in a cancellable status.",
        responses={
            200: OpenApiExample(
                "Booking cancelled",
                value={"message": "Booking cancelled successfully"},
                response_only=True,
            ),
            400: OpenApiExample(
                "Cannot cancel",
                value={"error": "Cannot cancel booking in current status"},
                response_only=True,
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()

        if BookingService.transition_status(booking, "CANCELLED"):
            logger.info(f"Booking {booking.id} cancelled by user {request.user.id}")
            return Response({"message": "Booking cancelled successfully"})
        else:
            return Response(
                {"error": "Cannot cancel booking in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
