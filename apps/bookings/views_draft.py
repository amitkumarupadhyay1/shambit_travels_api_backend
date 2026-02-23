"""
PHASE 4: Booking Draft Views

Protocol Compliance:
- §6: Draft persistence with 24h TTL
- Pre-login drafts stored in localStorage
- Post-login drafts stored in database
- Automatic expiration after 24 hours
"""

import logging

from django.utils import timezone

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models_draft import BookingDraft
from .serializers_draft import (
    BookingDraftCreateSerializer,
    BookingDraftMigrateSerializer,
    BookingDraftSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Booking Drafts"])
class BookingDraftViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing booking drafts.

    Lifecycle:
    1. User starts booking (pre-login) → localStorage
    2. User logs in → POST /api/bookings/drafts/migrate/ (migrate from localStorage)
    3. User continues editing → PATCH /api/bookings/drafts/{id}/
    4. User completes booking → Convert to Booking, delete draft
    5. After 24h → Auto-expire and delete
    """

    serializer_class = BookingDraftSerializer
    permission_classes = [IsAuthenticated]
    queryset = BookingDraft.objects.none()  # Default for schema generation

    def get_queryset(self):
        """Get drafts for authenticated user, exclude expired by default"""
        if getattr(self, "swagger_fake_view", False):
            return BookingDraft.objects.none()

        return (
            BookingDraft.objects.filter(
                user=self.request.user, expires_at__gt=timezone.now()
            )
            .select_related("package")
            .order_by("-updated_at")
        )

    @extend_schema(
        operation_id="list_drafts",
        summary="List user drafts",
        description="Retrieve all active drafts for the authenticated user (excludes expired).",
        responses={200: BookingDraftSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List all active drafts for user"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="get_draft",
        summary="Get draft details",
        description="Retrieve detailed information about a specific draft.",
        responses={
            200: BookingDraftSerializer,
            404: OpenApiExample(
                "Draft not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Get specific draft"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        operation_id="create_draft",
        summary="Create new draft",
        description="Create a new booking draft. Use migrate endpoint for localStorage migration.",
        request=BookingDraftCreateSerializer,
        responses={
            201: BookingDraftSerializer,
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid draft data"},
                response_only=True,
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create new draft"""
        serializer = BookingDraftCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        draft = serializer.save()

        response_serializer = BookingDraftSerializer(draft)
        logger.info(f"Draft {draft.id} created for user {request.user.id}")

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="update_draft",
        summary="Update draft",
        description="Update an existing draft. Extends expiry to 24h from now.",
        request=BookingDraftSerializer,
        responses={
            200: BookingDraftSerializer,
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid draft data"},
                response_only=True,
            ),
            404: OpenApiExample(
                "Draft not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    def update(self, request, *args, **kwargs):
        """Full update of draft"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        operation_id="partial_update_draft",
        summary="Partially update draft",
        description="Partially update a draft. Extends expiry to 24h from now.",
        request=BookingDraftSerializer,
        responses={
            200: BookingDraftSerializer,
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid draft data"},
                response_only=True,
            ),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """Partial update of draft"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        operation_id="delete_draft",
        summary="Delete draft",
        description="Delete a draft. Cannot be undone.",
        responses={
            204: OpenApiExample(
                "Draft deleted",
                value=None,
                response_only=True,
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete draft"""
        draft = self.get_object()
        draft_id = draft.id
        draft.delete()

        logger.info(f"Draft {draft_id} deleted by user {request.user.id}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="migrate_draft",
        summary="Migrate localStorage draft to backend",
        description=(
            "Migrate a draft from localStorage to backend after user login. "
            "If user already has a draft for this package, it will be updated."
        ),
        request=BookingDraftMigrateSerializer,
        responses={
            200: BookingDraftSerializer,
            201: BookingDraftSerializer,
            400: OpenApiExample(
                "Validation error",
                value={"error": "Invalid draft data"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Migrate draft",
                value={
                    "draft_data": {
                        "packageId": 1,
                        "experiences": [1, 2],
                        "days": 3,
                        "dateRange": {"start": "2026-03-01", "end": "2026-03-04"},
                        "travellers": [
                            {
                                "id": "t1",
                                "name": "John",
                                "age": 30,
                                "gender": "M",
                                "isChild": False,
                            }
                        ],
                        "hotelTier": 2,
                        "rooms": [],
                        "vehicles": [],
                        "pricingEstimate": {
                            "base": 15000,
                            "experiences": 5000,
                            "totalEstimate": 20000,
                        },
                        "status": "builder",
                        "versionToken": None,
                    }
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"])
    def migrate(self, request):
        """
        Migrate localStorage draft to backend after login.

        Protocol Compliance:
        - §6: Pre-login → post-login migration
        - Updates existing draft if found
        - Creates new draft if not found
        """
        serializer = BookingDraftMigrateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        draft = serializer.save()

        response_serializer = BookingDraftSerializer(draft)

        # Determine if created or updated
        is_new = draft.version == 1
        status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK

        logger.info(
            f"Draft {'created' if is_new else 'updated'} from localStorage migration: "
            f"draft_id={draft.id}, user={request.user.id}, package={draft.package_id}"
        )

        return Response(response_serializer.data, status=status_code)

    @extend_schema(
        operation_id="extend_draft_expiry",
        summary="Extend draft expiry",
        description="Extend draft expiry by 24 hours from now.",
        responses={
            200: BookingDraftSerializer,
            404: OpenApiExample(
                "Draft not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def extend_expiry(self, request, pk=None):
        """Extend draft expiry by 24 hours"""
        draft = self.get_object()
        draft.extend_expiry(hours=24)

        serializer = BookingDraftSerializer(draft)
        logger.info(f"Draft {draft.id} expiry extended to {draft.expires_at}")

        return Response(serializer.data)

    @extend_schema(
        operation_id="convert_draft_to_booking",
        summary="Convert draft to booking",
        description=(
            "Convert a draft to a booking. Returns booking creation data "
            "that can be used with the booking creation endpoint."
        ),
        responses={
            200: inline_serializer(
                name="DraftToBookingResponse",
                fields={
                    "booking_data": serializers.DictField(),
                    "draft_id": serializers.IntegerField(),
                },
            ),
            404: OpenApiExample(
                "Draft not found",
                value={"detail": "Not found."},
                response_only=True,
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def convert_to_booking(self, request, pk=None):
        """
        Convert draft to booking data.

        Returns booking creation data that can be used with POST /api/bookings/
        Frontend should then delete the draft after successful booking creation.
        """
        draft = self.get_object()

        if draft.is_expired():
            return Response(
                {"error": "Draft has expired"}, status=status.HTTP_400_BAD_REQUEST
            )

        booking_data = draft.to_booking_data()

        logger.info(f"Draft {draft.id} converted to booking data")

        return Response(
            {
                "booking_data": booking_data,
                "draft_id": draft.id,
            }
        )
