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
from .serializers import BookingCreateSerializer, BookingSerializer
from .services.booking_service import BookingService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Bookings"])
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
        description="Create a new booking for a travel package with selected components.",
        request=BookingCreateSerializer,
        responses={
            201: BookingSerializer,
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid booking data"},
                response_only=True,
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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
        """
        booking = self.get_object()

        if booking.status != "DRAFT":
            return Response(
                {"error": "Payment can only be initiated for draft bookings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # VALIDATE PRICE HAS NOT CHANGED
        if not BookingService.validate_price(booking, booking.total_price):
            logger.error(
                f"Price validation failed for booking {booking.id}. "
                f"Possible tampering or pricing rule change."
            )
            return Response(
                {"error": "Booking price has changed. Please refresh and try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                razorpay_service = RazorpayService()
                order = razorpay_service.create_order(booking)

                # Update booking status
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
