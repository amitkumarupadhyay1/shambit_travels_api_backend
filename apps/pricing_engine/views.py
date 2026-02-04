import logging

from django.db import models
from django.utils import timezone
from packages.models import Package
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import PricingRule
from .serializers import PricingRuleSerializer
from .services.pricing_service import PricingService

logger = logging.getLogger(__name__)


class PricingRuleViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing pricing rules
    """

    queryset = PricingRule.objects.all()
    serializer_class = PricingRuleSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by rule type
        rule_type = self.request.query_params.get("rule_type")
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type.upper())

        # Filter by package
        package_id = self.request.query_params.get("package_id")
        if package_id:
            queryset = queryset.filter(target_package_id=package_id)

        return queryset.select_related("target_package")

    @action(detail=False, methods=["get"])
    def active_rules(self, request):
        """
        Get all currently active pricing rules
        """
        now = timezone.now()
        active_rules = (
            PricingRule.objects.filter(is_active=True, active_from__lte=now)
            .filter(models.Q(active_to__gte=now) | models.Q(active_to__isnull=True))
            .select_related("target_package")
        )

        serializer = self.get_serializer(active_rules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def test_pricing(self, request):
        """
        Test pricing calculation for given components
        """
        data = request.data
        try:
            package_id = data.get("package_id")
            experience_ids = data.get("experience_ids", [])
            hotel_tier_id = data.get("hotel_tier_id")
            transport_option_id = data.get("transport_option_id")

            # Validate inputs
            from packages.models import (Experience, HotelTier, Package,
                                         TransportOption)

            package = Package.objects.get(id=package_id)
            experiences = Experience.objects.filter(id__in=experience_ids)
            hotel_tier = HotelTier.objects.get(id=hotel_tier_id)
            transport_option = TransportOption.objects.get(id=transport_option_id)

            # Calculate price
            total_price = PricingService.calculate_total(
                package, experiences, hotel_tier, transport_option
            )

            # Get applied rules
            applied_rules = PricingService.get_applicable_rules(package)

            return Response(
                {
                    "total_price": str(total_price),
                    "applied_rules": [
                        {
                            "name": rule.name,
                            "type": rule.rule_type,
                            "value": str(rule.value),
                            "is_percentage": rule.is_percentage,
                        }
                        for rule in applied_rules
                    ],
                    "breakdown": PricingService.get_price_breakdown(
                        package, experiences, hotel_tier, transport_option
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Pricing test failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
