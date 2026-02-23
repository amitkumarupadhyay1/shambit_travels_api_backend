"""
Vehicle Suggestions API Endpoint

Provides optimized vehicle combinations based on passenger count and trip duration.
"""

import logging
from math import ceil

from drf_spectacular.utils import extend_schema
from pricing_engine.services.vehicle_optimization import (
    VehicleOptimizationEngine,
    VehicleType,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TransportOption

logger = logging.getLogger(__name__)


class VehicleSuggestionsView(APIView):
    """
    POST /api/vehicle-suggestions/

    Returns optimized vehicle combinations for given passenger count and duration.
    """

    @extend_schema(
        tags=["Packages"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "passenger_count": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Number of passengers to accommodate",
                    },
                    "num_days": {
                        "type": "number",
                        "minimum": 0.5,
                        "description": "Trip duration in days (fractional allowed, will be ceiled)",
                    },
                    "max_solutions": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 10,
                        "description": "Maximum number of solutions to return",
                    },
                },
                "required": ["passenger_count", "num_days"],
            }
        },
        responses={
            200: {
                "description": "Optimized vehicle combinations",
                "content": {
                    "application/json": {
                        "example": {
                            "passenger_count": 10,
                            "num_days": 3,
                            "solutions": [
                                {
                                    "vehicles": [
                                        {
                                            "transport_option_id": 3,
                                            "name": "Van",
                                            "count": 1,
                                            "capacity": 12,
                                            "price_per_day": "2500.00",
                                        }
                                    ],
                                    "total_vehicle_count": 1,
                                    "total_capacity": 12,
                                    "unused_seats": 2,
                                    "cost_per_day": "2500.00",
                                    "total_cost": "7500.00",
                                    "num_days": 3,
                                    "recommended": True,
                                }
                            ],
                        }
                    }
                },
            },
            400: {"description": "Invalid input parameters"},
        },
    )
    def post(self, request):
        """
        Generate optimized vehicle combinations.

        Request body:
        {
            "passenger_count": 10,
            "num_days": 3,
            "max_solutions": 10  // optional
        }

        Response:
        {
            "passenger_count": 10,
            "num_days": 3,
            "solutions": [
                {
                    "vehicles": [...],
                    "total_vehicle_count": 1,
                    "total_capacity": 12,
                    "unused_seats": 2,
                    "cost_per_day": "2500.00",
                    "total_cost": "7500.00",
                    "num_days": 3,
                    "recommended": true  // Only first solution
                }
            ]
        }
        """
        # Validate input
        passenger_count = request.data.get("passenger_count")
        num_days = request.data.get("num_days")
        max_solutions = request.data.get("max_solutions", 10)

        if not passenger_count or passenger_count < 1:
            return Response(
                {"error": "passenger_count must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not num_days or num_days <= 0:
            return Response(
                {"error": "num_days must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if max_solutions < 1 or max_solutions > 20:
            return Response(
                {"error": "max_solutions must be between 1 and 20"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get active vehicle types from database
            transport_options = TransportOption.objects.filter(is_active=True)

            if not transport_options.exists():
                return Response(
                    {"error": "No active vehicle types available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Convert to VehicleType objects
            vehicle_types = [
                VehicleType(
                    id=t.id,
                    name=t.name,
                    passenger_capacity=t.passenger_capacity,
                    luggage_capacity=t.luggage_capacity,
                    base_price_per_day=t.get_effective_price_per_day(),
                    is_active=t.is_active,
                )
                for t in transport_options
            ]

            # Run optimization
            engine = VehicleOptimizationEngine(
                vehicle_types=vehicle_types,
                passenger_count=passenger_count,
                num_days=num_days,
            )

            solutions = engine.optimize(max_solutions=max_solutions)

            # Convert to response format
            response_data = {
                "passenger_count": passenger_count,
                "num_days": ceil(num_days),
                "solutions": [
                    {
                        **solution.to_dict(),
                        "recommended": i == 0,  # Mark first as recommended
                    }
                    for i, solution in enumerate(solutions)
                ],
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error generating vehicle suggestions: {str(e)}", exc_info=True
            )
            return Response(
                {"error": "Failed to generate vehicle suggestions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
