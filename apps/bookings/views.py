import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from payments.services.payment_service import RazorpayService
from pricing_engine.services.pricing_service import PricingService
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
from .services.voucher_service import VoucherService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Bookings"])
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.none()  # Default queryset for schema generation

    def get_permissions(self):
        """
        Override permissions for specific actions.
        Preview, recommend_rooms, and verify_booking endpoints should be public.
        """
        if self.action in ["preview", "recommend_rooms", "verify_booking"]:
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
        description=(
            "Create a new booking for a travel package with selected "
            "components. Requires Idempotency-Key header to prevent "
            "duplicate bookings."
        ),
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
                f"Idempotent request detected: {idempotency_key} "
                f"for user {request.user.id}"
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
        description=("Update booking details. CONFIRMED bookings cannot be modified."),
        request=BookingUpdateSerializer,
        responses={
            200: BookingSerializer,
            403: OpenApiExample(
                "Cannot modify confirmed booking",
                value={
                    "error": (
                        "Confirmed bookings cannot be modified. "
                        "Please contact support."
                    )
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
                    "error": (
                        "Confirmed bookings cannot be modified. "
                        "Please contact support."
                    )
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
        description=(
            "Partially update booking details. "
            "CONFIRMED bookings cannot be modified."
        ),
        request=BookingUpdateSerializer,
        responses={
            200: BookingSerializer,
            403: OpenApiExample(
                "Cannot modify confirmed booking",
                value={
                    "error": (
                        "Confirmed bookings cannot be modified. "
                        "Please contact support."
                    )
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
                    "error": (
                        "Confirmed bookings cannot be modified. "
                        "Please contact support."
                    )
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
        description=(
            "Create a Razorpay order for the booking and transition it to "
            "pending payment status. Validates that the booking price has "
            "not changed."
        ),
        request=None,
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
                {
                    "error": (
                        f"Payment cannot be initiated for " f"{booking.status} bookings"
                    )
                },
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
                    "error": (
                        f"Booking validation failed: {error_message}. "
                        f"Please refresh and try again."
                    )
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
        operation_id="validate_booking_payment",
        summary="Validate booking before payment",
        description=(
            "Validates booking data and returns exact payment amount to be "
            "charged. Call this before initiating payment for final "
            "confirmation."
        ),
        request=None,
        responses={
            200: inline_serializer(
                name="PaymentValidationResponse",
                fields={
                    "booking_id": serializers.IntegerField(),
                    "per_person_price": serializers.CharField(),
                    "chargeable_travelers": serializers.IntegerField(),
                    "total_amount": serializers.CharField(),
                    "amount_in_paise": serializers.IntegerField(),
                    "currency": serializers.CharField(),
                    "validated_at": serializers.DateTimeField(),
                },
            ),
            400: OpenApiExample(
                "Validation failed",
                value={"error": "Booking validation failed"},
                response_only=True,
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def validate_payment(self, request, pk=None):
        """
        Pre-payment validation endpoint.
        Returns exact amount that will be charged.
        Frontend should call this before initiating payment.
        """
        booking = self.get_object()

        if booking.status not in ["DRAFT", "PENDING_PAYMENT"]:
            return Response(
                {"error": f"Cannot initiate payment for {booking.status} bookings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate price
        is_valid, error_message = BookingService.validate_price(booking)
        if not is_valid:
            return Response(
                {"error": (f"Booking validation failed: {error_message}")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Recalculate with booking context to derive canonical payable amount
        recalculated = PricingService.get_price_breakdown(
            booking.package,
            booking.selected_experiences.all(),
            booking.selected_hotel_tier,
            booking.selected_transport,
            booking.traveler_details if booking.traveler_details else None,
            start_date=booking.booking_start_date or booking.booking_date,
            end_date=booking.booking_end_date,
            num_rooms=booking.num_rooms_required,
            num_travelers=booking.num_travelers,
        )
        amounts = BookingService.get_canonical_amounts(
            booking, recalculated_total=recalculated["final_total"]
        )
        total_amount = amounts["total_amount"]
        per_person_price = amounts["per_person_amount"]
        chargeable_travelers = amounts["chargeable_travelers"]

        amount_in_paise = int(total_amount * 100)

        logger.info(
            f"Payment validation for booking {booking.id}: "
            f"total_amount=${total_amount}, amount_in_paise={amount_in_paise}"
        )

        return Response(
            {
                "booking_id": booking.id,
                "per_person_price": str(per_person_price),
                "chargeable_travelers": chargeable_travelers,
                "total_amount": str(total_amount),
                "amount_in_paise": amount_in_paise,
                "currency": "INR",
                "validated_at": timezone.now().isoformat(),
            }
        )

    @extend_schema(
        operation_id="verify_payment",
        summary="Verify payment after Razorpay success",
        description=(
            "Verifies payment with Razorpay API and updates booking status. "
            "Call this after receiving payment success from Razorpay frontend. "
            "This is a fallback mechanism in case webhook fails."
        ),
        request=inline_serializer(
            name="VerifyPaymentRequest",
            fields={
                "razorpay_payment_id": serializers.CharField(),
                "razorpay_order_id": serializers.CharField(),
                "razorpay_signature": serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="VerifyPaymentResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "booking_status": serializers.CharField(),
                    "booking_reference": serializers.CharField(),
                },
            ),
            400: OpenApiExample(
                "Verification failed",
                value={"error": "Payment verification failed"},
                response_only=True,
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def verify_payment(self, request, pk=None):
        """
        Verify payment with Razorpay and update booking status.

        SECURITY: Multiple layers of verification ensure payment is ACTUALLY deducted:
        1. Signature verification (prevents fake payments)
        2. Fetch from Razorpay API (confirms payment exists)
        3. Status check (must be "captured" - money deducted)
        4. Amount validation (exact match required)
        5. Refund check (rejects refunded payments)
        """
        booking = self.get_object()

        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_signature = request.data.get("razorpay_signature")

        # Security Check 1: All parameters present
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            logger.error(f"Missing payment parameters for booking {booking.id}")
            return Response(
                {"error": "Missing required payment parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Security Check 2: Booking belongs to requesting user
        if booking.user != request.user:
            logger.error(
                f"User {request.user.id} attempted to verify booking {booking.id} "
                f"belonging to user {booking.user.id}"
            )
            return Response(
                {"error": "Unauthorized access"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Security Check 3: Check if booking is already confirmed
        if booking.status == "CONFIRMED":
            logger.info(
                f"Booking {booking.id} already confirmed, skipping verification"
            )
            return Response(
                {
                    "success": True,
                    "message": "Booking already confirmed",
                    "booking_status": booking.status,
                    "booking_reference": booking.booking_reference,
                }
            )

        # Security Check 4: Booking is in correct state
        if booking.status not in ["PENDING_PAYMENT", "DRAFT"]:
            logger.error(
                f"Cannot verify payment for booking {booking.id} "
                f"with status {booking.status}"
            )
            return Response(
                {"error": f"Cannot verify payment for {booking.status} bookings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Security Check 5: Booking not expired
        if booking.expires_at and booking.expires_at < timezone.now():
            logger.error(f"Booking {booking.id} has expired")
            return Response(
                {"error": "Booking has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Get payment record
                from payments.models import Payment

                try:
                    payment = Payment.objects.select_for_update().get(
                        booking=booking, razorpay_order_id=razorpay_order_id
                    )
                except Payment.DoesNotExist:
                    logger.error(
                        f"Payment not found for booking {booking.id}, "
                        f"order_id={razorpay_order_id}"
                    )
                    return Response(
                        {"error": "Payment record not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Security Check 6: Payment not already processed
                if payment.status == "SUCCESS":
                    logger.warning(
                        f"Payment {payment.id} already marked as SUCCESS, "
                        f"possible duplicate request"
                    )
                    return Response(
                        {
                            "success": True,
                            "message": "Payment already processed",
                            "booking_status": booking.status,
                            "booking_reference": booking.booking_reference,
                        }
                    )

                # Security Check 7: Verify signature with Razorpay
                razorpay_service = RazorpayService()
                try:
                    params_dict = {
                        "razorpay_order_id": razorpay_order_id,
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature,
                    }
                    razorpay_service.client.utility.verify_payment_signature(
                        params_dict
                    )
                    logger.info(
                        f"✅ Payment signature verified for booking {booking.id}"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Payment signature verification FAILED "
                        f"for booking {booking.id}: {str(e)}"
                    )
                    return Response(
                        {
                            "error": "Payment signature verification failed",
                            "details": "Payment authenticity could not be verified",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Security Check 8: Fetch payment details from Razorpay API
                try:
                    payment_details = razorpay_service.client.payment.fetch(
                        razorpay_payment_id
                    )
                    logger.info(
                        f"Fetched payment from Razorpay: "
                        f"status={payment_details.get('status')}, "
                        f"amount={payment_details.get('amount')}"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to fetch payment from Razorpay API: {str(e)}"
                    )
                    return Response(
                        {
                            "error": "Failed to verify payment with Razorpay",
                            "details": (
                                "Could not fetch payment details "
                                "from payment gateway"
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Security Check 9: Payment status is "captured" (money deducted)
                payment_status = payment_details.get("status")
                if payment_status != "captured":
                    logger.error(
                        f"❌ Payment {razorpay_payment_id} NOT CAPTURED! "
                        f"Status: {payment_status}"
                    )
                    return Response(
                        {
                            "error": "Payment not captured",
                            "payment_status": payment_status,
                            "details": "Money has not been deducted yet",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                logger.info(f"✅ Payment {razorpay_payment_id} is CAPTURED")

                # Security Check 10: Amount matches exactly
                payment_amount_paise = payment_details.get("amount", 0)
                expected_amount_paise = int(payment.amount * 100)

                if payment_amount_paise != expected_amount_paise:
                    logger.error(
                        f"❌ AMOUNT MISMATCH for booking {booking.id}! "
                        f"Received: ₹{payment_amount_paise/100}, "
                        f"Expected: ₹{expected_amount_paise/100}"
                    )
                    return Response(
                        {
                            "error": "Payment amount mismatch",
                            "received_amount": payment_amount_paise / 100,
                            "expected_amount": expected_amount_paise / 100,
                            "details": "Payment amount does not match booking amount",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                logger.info(
                    f"✅ Amount verified: ₹{payment_amount_paise/100} matches expected"
                )

                # Security Check 11: Payment is not refunded
                amount_refunded = payment_details.get("amount_refunded", 0)
                if amount_refunded > 0:
                    logger.error(
                        f"❌ Payment {razorpay_payment_id} has been REFUNDED! "
                        f"Refunded amount: ₹{amount_refunded/100}"
                    )
                    return Response(
                        {
                            "error": "Payment has been refunded",
                            "details": (
                                "This payment has been refunded " "and cannot be used"
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Security Check 12: Order ID matches
                razorpay_order_id_from_payment = payment_details.get("order_id")
                if razorpay_order_id_from_payment != razorpay_order_id:
                    logger.error(
                        f"❌ Order ID mismatch! "
                        f"Payment has: {razorpay_order_id_from_payment}, "
                        f"Expected: {razorpay_order_id}"
                    )
                    return Response(
                        {"error": "Order ID mismatch"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # ALL SECURITY CHECKS PASSED ✅
                logger.info(f"✅ ALL SECURITY CHECKS PASSED for booking {booking.id}")

                # Update payment record
                payment.razorpay_payment_id = razorpay_payment_id
                payment.status = "SUCCESS"
                payment.save(update_fields=["razorpay_payment_id", "status"])

                # Transition booking to CONFIRMED
                success = BookingService.transition_status(booking, "CONFIRMED")

                if not success:
                    logger.error(
                        f"❌ Failed to transition booking {booking.id} to CONFIRMED"
                    )
                    return Response(
                        {"error": "Failed to confirm booking"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                logger.info(
                    f"✅✅✅ BOOKING CONFIRMED: "
                    f"booking={booking.id}, "
                    f"payment={razorpay_payment_id}, "
                    f"reference={booking.booking_reference}, "
                    f"amount=₹{payment_amount_paise/100}"
                )

                return Response(
                    {
                        "success": True,
                        "message": "Payment verified and booking confirmed",
                        "booking_status": booking.status,
                        "booking_reference": booking.booking_reference,
                    }
                )

        except Exception as e:
            logger.error(
                f"Payment verification error for booking {booking.id}: {str(e)}"
            )
            return Response(
                {"error": f"Payment verification failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        operation_id="preview_booking",
        summary="Preview booking price",
        description=(
            "Calculate booking price with traveler details WITHOUT creating "
            "a booking. Used on review page to show accurate age-based "
            "pricing."
        ),
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
                    "chargeable_age_threshold": serializers.IntegerField(),
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

        PHASE 1 UPDATE: Now supports date range and room count for accurate hotel pricing.
        """
        serializer = BookingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from datetime import datetime

        from packages.models import Experience, HotelTier, Package, TransportOption
        from pricing_engine.services.pricing_service import PricingService

        # Get validated data
        data = serializer.validated_data
        package = Package.objects.get(id=data["package_id"])
        experiences = Experience.objects.filter(id__in=data["selected_experience_ids"])
        hotel_tier = HotelTier.objects.get(id=data["hotel_tier_id"])
        transport_option = TransportOption.objects.get(id=data["transport_option_id"])
        traveler_details = data.get("traveler_details", [])

        # PHASE 1: Get date range and room count if provided
        start_date = data.get("booking_start_date")
        end_date = data.get("booking_end_date")
        num_rooms = data.get("num_rooms", 1)

        # Convert string dates to date objects if provided
        if start_date and isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date and isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Calculate price with traveler details and date range
        breakdown = PricingService.get_price_breakdown(
            package=package,
            experiences=experiences,
            hotel_tier=hotel_tier,
            transport_option=transport_option,
            travelers=traveler_details if traveler_details else None,
            start_date=start_date,
            end_date=end_date,
            num_rooms=num_rooms,
            num_travelers=data["num_travelers"],
        )

        # Canonical amount fields from backend breakdown
        num_travelers = data["num_travelers"]
        chargeable_count = breakdown.get("chargeable_travelers", num_travelers)
        total_amount = Decimal(
            str(breakdown.get("total_amount", breakdown["final_total"]))
        )
        if chargeable_count > 0:
            per_person_price = (total_amount / Decimal(str(chargeable_count))).quantize(
                Decimal("0.01")
            )
        else:
            per_person_price = total_amount

        logger.info(
            f"Preview calculated: per_person={per_person_price}, "
            f"num_travelers={num_travelers}, chargeable={chargeable_count}, "
            f"total={total_amount}, nights={breakdown.get('hotel_num_nights')}, "
            f"rooms={breakdown.get('hotel_num_rooms')}, uses_new_pricing={breakdown.get('uses_new_hotel_pricing')}"
        )

        return Response(
            {
                "per_person_price": str(per_person_price),
                "num_travelers": num_travelers,
                "chargeable_travelers": chargeable_count,
                "total_amount": str(total_amount),
                "chargeable_age_threshold": breakdown.get(
                    "chargeable_age_threshold",
                    PricingService.get_chargeable_age_threshold(),
                ),
                "price_breakdown": {
                    "base_experience_total": str(breakdown["base_experience_total"]),
                    "base_experience_per_person": str(
                        breakdown.get(
                            "base_experience_per_person",
                            breakdown["base_experience_total"],
                        )
                    ),
                    "transport_cost": str(breakdown["transport_cost"]),
                    "subtotal_before_hotel": str(breakdown["subtotal_before_hotel"]),
                    "hotel_multiplier": str(breakdown["hotel_multiplier"]),
                    "subtotal_after_hotel": str(breakdown["subtotal_after_hotel"]),
                    # PHASE 1: New hotel cost fields
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
                    # End PHASE 1
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
        operation_id="recommend_rooms",
        summary="Get room recommendations",
        description=(
            "PHASE 3: Get intelligent room allocation recommendations based on "
            "traveler composition (age, gender). Analyzes group dynamics and "
            "suggests optimal room configurations."
        ),
        request=inline_serializer(
            name="RoomRecommendationRequest",
            fields={
                "hotel_tier_id": serializers.IntegerField(help_text="Hotel tier ID"),
                "traveler_details": serializers.ListField(
                    child=inline_serializer(
                        name="TravelerDetail",
                        fields={
                            "name": serializers.CharField(),
                            "age": serializers.IntegerField(),
                            "gender": serializers.CharField(required=False),
                        },
                    ),
                    help_text="List of traveler details with name, age, and optional gender",
                ),
                "preference": serializers.ChoiceField(
                    choices=[
                        "auto",
                        "budget",
                        "comfort",
                        "privacy",
                        "family",
                        "gender_separated",
                    ],
                    default="auto",
                    required=False,
                    help_text="Preferred allocation type (default: auto)",
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name="RoomRecommendationResponse",
                fields={
                    "recommendations": serializers.ListField(
                        child=serializers.DictField(),
                        help_text="List of room allocation recommendations",
                    ),
                    "composition": serializers.DictField(
                        help_text="Traveler composition analysis"
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Family with children",
                value={
                    "hotel_tier_id": 1,
                    "traveler_details": [
                        {"name": "John", "age": 35, "gender": "M"},
                        {"name": "Jane", "age": 32, "gender": "F"},
                        {"name": "Child 1", "age": 8, "gender": "M"},
                        {"name": "Child 2", "age": 5, "gender": "F"},
                    ],
                    "preference": "auto",
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"])
    def recommend_rooms(self, request):
        """
        PHASE 3: Get intelligent room recommendations based on traveler composition.
        """
        from packages.models import HotelTier
        from pricing_engine.services.room_recommendation_service import (
            RoomRecommendationService,
        )

        # Validate input
        hotel_tier_id = request.data.get("hotel_tier_id")
        traveler_details = request.data.get("traveler_details", [])
        request.data.get("preference", "auto")

        if not hotel_tier_id:
            return Response(
                {"error": "hotel_tier_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not traveler_details:
            return Response(
                {"error": "traveler_details is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            hotel_tier = HotelTier.objects.get(id=hotel_tier_id)
        except HotelTier.DoesNotExist:
            return Response(
                {"error": "Hotel tier not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get composition analysis
        composition = RoomRecommendationService.analyze_traveler_composition(
            traveler_details
        )

        # Get recommendations
        recommendations = RoomRecommendationService.recommend_rooms(
            travelers=traveler_details, hotel_tier=hotel_tier
        )

        # Convert Decimal to string for JSON serialization
        for rec in recommendations:
            rec["cost_per_night"] = str(rec["cost_per_night"])

        logger.info(
            f"Room recommendations generated: {len(recommendations)} options for "
            f"{composition['total']} travelers (hotel_tier={hotel_tier_id})"
        )

        return Response(
            {
                "recommendations": recommendations,
                "composition": composition,
                "hotel_tier": {
                    "id": hotel_tier.id,
                    "name": hotel_tier.name,
                    "max_occupancy_per_room": hotel_tier.max_occupancy_per_room,
                    "base_price_per_night": (
                        str(hotel_tier.base_price_per_night)
                        if hotel_tier.base_price_per_night
                        else None
                    ),
                },
            }
        )

    @extend_schema(
        operation_id="verify_booking_by_reference",
        summary="Verify booking by reference number",
        description="Public endpoint to verify booking authenticity. Returns limited information for security. Rate limited to 10 requests per minute per IP.",
        parameters=[
            OpenApiParameter(
                name="reference",
                type=str,
                location=OpenApiParameter.PATH,
                description="Booking reference number (e.g., SB-2024-000123)",
            )
        ],
        responses={
            200: OpenApiExample(
                "Booking verified",
                value={
                    "booking_reference": "SB-2024-000123",
                    "status": "CONFIRMED",
                    "package_name": "Divine Varanasi Experience",
                    "destination": "Varanasi",
                    "booking_date": "2024-03-15",
                    "num_travelers": 4,
                    "customer_name": "John Doe",
                    "total_amount": "45000.00",
                    "created_at": "2024-02-20T10:30:00Z",
                },
                response_only=True,
            ),
            404: OpenApiExample(
                "Booking not found",
                value={"error": "Booking not found"},
                response_only=True,
            ),
            429: OpenApiExample(
                "Rate limit exceeded",
                value={
                    "error": "Too many verification attempts. Please try again later."
                },
                response_only=True,
            ),
        },
    )
    @action(detail=False, methods=["get"], url_path="verify/(?P<reference>[^/.]+)")
    def verify_booking(self, request, reference=None):
        """
        Public endpoint to verify booking by reference number.
        Returns limited booking information for security.
        Rate limited to prevent enumeration attacks.
        """
        from django.core.cache import cache

        # Rate limiting: 10 requests per minute per IP
        ip_address = request.META.get("REMOTE_ADDR", "unknown")
        cache_key = f"booking_verify_rate_limit_{ip_address}"
        request_count = cache.get(cache_key, 0)

        if request_count >= 10:
            logger.warning(
                f"Rate limit exceeded for booking verification from IP {ip_address}"
            )
            return Response(
                {"error": "Too many verification attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Increment rate limit counter
        cache.set(cache_key, request_count + 1, 60)  # 60 seconds TTL

        try:
            # Parse booking reference to extract ID
            # Format: SB-YYYY-NNNNNN (e.g., SB-2026-000044)
            try:
                parts = reference.split("-")
                if len(parts) != 3 or parts[0] != "SB":
                    raise ValueError("Invalid reference format")
                booking_id = int(parts[2])  # Extract the numeric ID
            except (ValueError, IndexError):
                logger.warning(
                    f"Invalid booking reference format: {reference}, ip={ip_address}"
                )
                return Response(
                    {"error": "Invalid booking reference format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Find booking by ID and verify the reference matches
            booking = Booking.objects.select_related("package", "package__city").get(
                id=booking_id
            )

            # Verify the reference matches (year check)
            if booking.booking_reference != reference:
                raise Booking.DoesNotExist()

            # Log verification attempt
            logger.info(
                f"Booking verification: reference={reference}, "
                f"booking_id={booking.id}, ip={ip_address}"
            )

            # Return limited information for security
            verification_data = {
                "booking_reference": booking.booking_reference,
                "status": booking.status,
                "package_name": booking.package.name,
                "destination": booking.package.city.name,
                "booking_date": booking.booking_date.isoformat(),
                "num_travelers": booking.num_travelers,
                "customer_name": booking.customer_name,
                "total_amount": str(booking.total_amount_paid or booking.total_price),
                "created_at": booking.created_at.isoformat(),
            }

            return Response(verification_data, status=status.HTTP_200_OK)

        except Booking.DoesNotExist:
            # Log failed verification attempt
            logger.warning(
                f"Booking verification failed: reference={reference}, ip={ip_address}"
            )
            return Response(
                {"error": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Booking verification error: {str(e)}")
            return Response(
                {"error": "Verification failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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

    @extend_schema(
        operation_id="download_voucher",
        summary="Download booking voucher PDF",
        description="Generate and download a PDF voucher for a confirmed booking.",
        responses={
            200: OpenApiExample(
                "PDF voucher",
                value="Binary PDF content",
                response_only=True,
            ),
            400: OpenApiExample(
                "Cannot generate voucher",
                value={"error": "Voucher can only be generated for confirmed bookings"},
                response_only=True,
            ),
        },
    )
    @action(detail=True, methods=["get"])
    def voucher(self, request, pk=None):
        """
        Generate and download PDF voucher for confirmed booking
        """
        from django.http import HttpResponse

        booking = self.get_object()

        # Only allow voucher generation for confirmed bookings
        if booking.status != "CONFIRMED":
            return Response(
                {"error": "Voucher can only be generated for confirmed bookings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Generate PDF voucher
            pdf_content = VoucherService.generate_voucher(booking)

            # Create response with PDF
            response = HttpResponse(pdf_content, content_type="application/pdf")
            filename = f"ShamBit-Voucher-{booking.booking_reference or booking.id}.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(
                f"Voucher downloaded for booking {booking.id} by user {request.user.id}"
            )

            return response

        except Exception as e:
            logger.error(
                f"Voucher generation failed for booking {booking.id}: {str(e)}"
            )
            return Response(
                {"error": f"Failed to generate voucher: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
