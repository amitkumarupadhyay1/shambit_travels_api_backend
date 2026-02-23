"""
Unit tests for vehicle optimization engine.
Tests mathematical correctness, edge cases, and performance.
"""

from decimal import Decimal

import pytest
from pricing_engine.services.vehicle_optimization import (
    VehicleCombination,
    VehicleOptimizationEngine,
    VehicleType,
    calculate_vehicle_price,
)


@pytest.fixture
def vehicle_types():
    """Standard set of vehicle types for testing"""
    return [
        VehicleType(
            id=1,
            name="Sedan",
            passenger_capacity=4,
            luggage_capacity=3,
            base_price_per_day=Decimal("1000"),
            is_active=True,
        ),
        VehicleType(
            id=2,
            name="SUV",
            passenger_capacity=7,
            luggage_capacity=5,
            base_price_per_day=Decimal("1500"),
            is_active=True,
        ),
        VehicleType(
            id=3,
            name="Van",
            passenger_capacity=12,
            luggage_capacity=10,
            base_price_per_day=Decimal("2500"),
            is_active=True,
        ),
    ]


class TestVehicleCombination:
    """Test VehicleCombination dataclass and methods"""

    def test_lexicographic_comparison(self, vehicle_types):
        """Test that combinations are compared lexicographically"""
        combo1 = VehicleCombination(
            vehicles=[(vehicle_types[0], 2)],
            total_vehicle_count=2,
            total_capacity=8,
            unused_seats=0,
            cost_per_day=Decimal("2000"),
            total_cost=Decimal("4000"),
            num_days=2,
        )

        combo2 = VehicleCombination(
            vehicles=[(vehicle_types[1], 2)],
            total_vehicle_count=2,
            total_capacity=14,
            unused_seats=6,
            cost_per_day=Decimal("3000"),
            total_cost=Decimal("6000"),
            num_days=2,
        )

        # Same vehicle count, combo1 has fewer unused seats
        assert combo1 < combo2

    def test_dominance_detection(self, vehicle_types):
        """Test dominance relationship between solutions"""
        # Solution A: 1 van (12 capacity, 2500/day)
        combo_a = VehicleCombination(
            vehicles=[(vehicle_types[2], 1)],
            total_vehicle_count=1,
            total_capacity=12,
            unused_seats=2,
            cost_per_day=Decimal("2500"),
            total_cost=Decimal("5000"),
            num_days=2,
        )

        # Solution B: 2 SUVs (14 capacity, 3000/day)
        combo_b = VehicleCombination(
            vehicles=[(vehicle_types[1], 2)],
            total_vehicle_count=2,
            total_capacity=14,
            unused_seats=4,
            cost_per_day=Decimal("3000"),
            total_cost=Decimal("6000"),
            num_days=2,
        )

        # A dominates B (fewer vehicles, fewer unused seats, lower cost)
        assert combo_a.dominates(combo_b)
        assert not combo_b.dominates(combo_a)

    def test_to_dict_serialization(self, vehicle_types):
        """Test dictionary serialization for JSON"""
        combo = VehicleCombination(
            vehicles=[(vehicle_types[0], 2), (vehicle_types[1], 1)],
            total_vehicle_count=3,
            total_capacity=15,
            unused_seats=5,
            cost_per_day=Decimal("3500"),
            total_cost=Decimal("7000"),
            num_days=2,
        )

        result = combo.to_dict()

        assert result["total_vehicle_count"] == 3
        assert result["total_capacity"] == 15
        assert result["unused_seats"] == 5
        assert result["cost_per_day"] == "3500"
        assert result["total_cost"] == "7000"
        assert len(result["vehicles"]) == 2


class TestVehicleOptimizationEngine:
    """Test optimization engine logic"""

    def test_single_passenger(self, vehicle_types):
        """Test P = 1 (minimum case)"""
        engine = VehicleOptimizationEngine(vehicle_types, passenger_count=1, num_days=1)
        solutions = engine.optimize()

        assert len(solutions) > 0
        best = solutions[0]

        # Should select 1 sedan (cheapest option)
        assert best.total_vehicle_count == 1
        assert best.total_capacity >= 1
        assert best.vehicles[0][0].name == "Sedan"

    def test_exact_capacity_match(self, vehicle_types):
        """Test P = exact capacity (e.g., 12 for van)"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=12, num_days=1
        )
        solutions = engine.optimize()

        assert len(solutions) > 0
        best = solutions[0]

        # Should select 1 van (exact match)
        assert best.total_vehicle_count == 1
        assert best.total_capacity == 12
        assert best.unused_seats == 0

    def test_capacity_plus_one(self, vehicle_types):
        """Test P = capacity + 1 (e.g., 13 passengers)"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=13, num_days=1
        )
        solutions = engine.optimize()

        assert len(solutions) > 0
        best = solutions[0]

        # Should select 2 vehicles minimum
        assert best.total_vehicle_count >= 2
        assert best.total_capacity >= 13

    def test_large_passenger_count(self, vehicle_types):
        """Test very large P (e.g., 120 passengers)"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=120, num_days=1
        )
        solutions = engine.optimize()

        assert len(solutions) > 0
        best = solutions[0]

        # Should find valid solution
        assert best.total_capacity >= 120
        assert best.unused_seats >= 0

        # Should prefer vans (most efficient)
        van_count = sum(
            count for vehicle, count in best.vehicles if vehicle.name == "Van"
        )
        assert van_count >= 10  # At least 10 vans for 120 passengers

    def test_single_vehicle_type_active(self, vehicle_types):
        """Test with only one vehicle type active"""
        # Only sedan active
        single_type = [vehicle_types[0]]

        engine = VehicleOptimizationEngine(single_type, passenger_count=10, num_days=1)
        solutions = engine.optimize()

        assert len(solutions) > 0
        best = solutions[0]

        # Should use 3 sedans (3 * 4 = 12 capacity)
        assert best.total_vehicle_count == 3
        assert best.total_capacity >= 10

    def test_tie_cases(self, vehicle_types):
        """Test tie-breaking in lexicographic ranking"""
        engine = VehicleOptimizationEngine(vehicle_types, passenger_count=8, num_days=1)
        solutions = engine.optimize()

        # Multiple solutions possible: 2 sedans, 1 SUV + 1 sedan, etc.
        assert len(solutions) > 0

        # Best should have minimum vehicle count
        best = solutions[0]
        for solution in solutions[1:]:
            assert best.total_vehicle_count <= solution.total_vehicle_count

    def test_no_under_capacity_solutions(self, vehicle_types):
        """Test that no under-capacity solutions are returned"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=20, num_days=1
        )
        solutions = engine.optimize()

        for solution in solutions:
            assert solution.total_capacity >= 20, "Under-capacity solution found!"

    def test_pricing_calculation(self, vehicle_types):
        """Test that pricing is calculated correctly"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=10, num_days=3
        )
        solutions = engine.optimize()

        best = solutions[0]

        # Verify cost calculation
        expected_cost_per_day = sum(
            vehicle.base_price_per_day * count for vehicle, count in best.vehicles
        )
        expected_total_cost = expected_cost_per_day * 3

        assert best.cost_per_day == expected_cost_per_day
        assert best.total_cost == expected_total_cost

    def test_dominance_elimination(self, vehicle_types):
        """Test that dominated solutions are removed"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=15, num_days=1
        )
        solutions = engine.optimize()

        # Check no solution dominates another
        for i, solution_a in enumerate(solutions):
            for j, solution_b in enumerate(solutions):
                if i != j:
                    assert not solution_a.dominates(
                        solution_b
                    ), f"Solution {i} dominates solution {j}"

    def test_empty_vehicle_types(self):
        """Test with no active vehicle types"""
        engine = VehicleOptimizationEngine([], passenger_count=10, num_days=1)
        solutions = engine.optimize()

        assert len(solutions) == 0

    def test_zero_passengers(self, vehicle_types):
        """Test with zero passengers"""
        engine = VehicleOptimizationEngine(vehicle_types, passenger_count=0, num_days=1)
        solutions = engine.optimize()

        assert len(solutions) == 0

    def test_inactive_vehicles_excluded(self):
        """Test that inactive vehicles are not used"""
        vehicles = [
            VehicleType(
                id=1,
                name="Active Sedan",
                passenger_capacity=4,
                luggage_capacity=3,
                base_price_per_day=Decimal("1000"),
                is_active=True,
            ),
            VehicleType(
                id=2,
                name="Inactive Van",
                passenger_capacity=12,
                luggage_capacity=10,
                base_price_per_day=Decimal("500"),  # Cheaper but inactive
                is_active=False,
            ),
        ]

        engine = VehicleOptimizationEngine(vehicles, passenger_count=10, num_days=1)
        solutions = engine.optimize()

        # Should only use active sedan
        for solution in solutions:
            for vehicle, count in solution.vehicles:
                assert vehicle.is_active
                assert vehicle.name == "Active Sedan"

    def test_get_recommended_combination(self, vehicle_types):
        """Test getting single recommended combination"""
        engine = VehicleOptimizationEngine(
            vehicle_types, passenger_count=10, num_days=1
        )
        recommended = engine.get_recommended_combination()

        assert recommended is not None
        assert recommended.total_capacity >= 10


class TestCalculateVehiclePrice:
    """Test vehicle price calculation function"""

    def test_price_calculation(self, vehicle_types):
        """Test price calculation from allocation"""
        vehicle_map = {v.id: v for v in vehicle_types}

        allocation = [
            {"transport_option_id": 1, "count": 2},  # 2 sedans
            {"transport_option_id": 2, "count": 1},  # 1 SUV
        ]

        price = calculate_vehicle_price(
            allocation, num_days=3, vehicle_types_map=vehicle_map
        )

        # Expected: (2 * 1000 + 1 * 1500) * 3 = 3500 * 3 = 10500
        assert price == Decimal("10500")

    def test_empty_allocation(self, vehicle_types):
        """Test with empty allocation"""
        vehicle_map = {v.id: v for v in vehicle_types}
        price = calculate_vehicle_price([], num_days=1, vehicle_types_map=vehicle_map)

        assert price == Decimal("0")

    def test_invalid_vehicle_id(self, vehicle_types):
        """Test with invalid vehicle ID in allocation"""
        vehicle_map = {v.id: v for v in vehicle_types}

        allocation = [
            {"transport_option_id": 999, "count": 1},  # Invalid ID
        ]

        price = calculate_vehicle_price(
            allocation, num_days=1, vehicle_types_map=vehicle_map
        )

        # Should ignore invalid ID
        assert price == Decimal("0")

    def test_fractional_days_ceiling(self, vehicle_types):
        """Test that fractional days are ceiled"""
        vehicle_map = {v.id: v for v in vehicle_types}

        allocation = [{"transport_option_id": 1, "count": 1}]

        # 1.5 days should be ceiled to 2
        price = calculate_vehicle_price(
            allocation, num_days=1.5, vehicle_types_map=vehicle_map
        )

        assert price == Decimal("2000")  # 1000 * 2 days
