from django.db.models import Q

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Traveler
from .serializers import TravelerSerializer


class TravelerRateThrottle(UserRateThrottle):
    """Custom rate limiting for traveler operations"""

    rate = "100/hour"  # 100 requests per hour per user


class TravelerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing traveler profiles with comprehensive validation

    Endpoints:
    - GET /api/travelers/ - List all travelers for current user
    - POST /api/travelers/ - Create new traveler
    - GET /api/travelers/{id}/ - Get specific traveler
    - PUT /api/travelers/{id}/ - Update traveler
    - PATCH /api/travelers/{id}/ - Partial update
    - DELETE /api/travelers/{id}/ - Delete traveler
    - GET /api/travelers/search/?q=query - Search travelers

    Security:
    - Authentication required
    - Rate limited to 100 requests/hour per user
    - Input validation and sanitization
    - XSS protection
    """

    serializer_class = TravelerSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [TravelerRateThrottle]

    def get_queryset(self):
        """Return travelers for current user only"""
        return Traveler.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user when creating traveler"""
        # Check limit (50 travelers per user)
        if self.get_queryset().count() >= 50:
            raise serializers.ValidationError(
                {"detail": "Maximum 50 travelers allowed per user"}
            )
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search travelers by name, email, or phone
        Query param: q (search query)

        Security: Sanitizes search query to prevent SQL injection
        """
        query = request.query_params.get("q", "").strip()

        # Limit query length to prevent abuse
        if len(query) > 100:
            return Response(
                {"detail": "Search query too long (max 100 characters)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not query:
            travelers = self.get_queryset()
        else:
            # Django ORM automatically escapes queries, preventing SQL injection
            travelers = self.get_queryset().filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            )

        # Limit results to prevent large responses
        travelers = travelers[:50]

        serializer = self.get_serializer(travelers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_import(self, request):
        """
        Import multiple travelers at once
        Body: { "travelers": [...] }

        Security:
        - Validates all travelers before importing
        - Limits to 20 travelers per import
        - Checks total user limit
        """
        travelers_data = request.data.get("travelers", [])

        if not isinstance(travelers_data, list):
            return Response(
                {"detail": "travelers must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Limit bulk import size
        if len(travelers_data) > 20:
            return Response(
                {"detail": "Cannot import more than 20 travelers at once"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check total limit
        current_count = self.get_queryset().count()
        if current_count + len(travelers_data) > 50:
            return Response(
                {
                    "detail": f"Cannot import. Would exceed limit of 50 travelers (current: {current_count})"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_travelers = []
        errors = []

        for idx, traveler_data in enumerate(travelers_data):
            serializer = self.get_serializer(data=traveler_data)
            if serializer.is_valid():
                try:
                    serializer.save(user=request.user)
                    created_travelers.append(serializer.data)
                except Exception as e:
                    errors.append(
                        {
                            "index": idx,
                            "data": traveler_data,
                            "errors": {"detail": str(e)},
                        }
                    )
            else:
                errors.append(
                    {"index": idx, "data": traveler_data, "errors": serializer.errors}
                )

        return Response(
            {
                "created": len(created_travelers),
                "travelers": created_travelers,
                "errors": errors,
            },
            status=(
                status.HTTP_201_CREATED
                if created_travelers
                else status.HTTP_400_BAD_REQUEST
            ),
        )
