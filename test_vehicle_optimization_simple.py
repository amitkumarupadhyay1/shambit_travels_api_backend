"""
Simple standalone test for vehicle optimization engine.
Run with: python test_vehicle_optimization_simple.py
"""

import logging
import sys
from decimal import Decimal
from pathlib import Path

# Add apps directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "apps"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from pricing_engine.services.vehicle_optimization import (  # noqa: E402
    VehicleOptimizationEngine,
    VehicleType,
    calculate_vehicle_price,
)


def test_basic_optimization():
    """Test basic vehicle optimization"""
    print("Testing basic vehicle optimization...")

    vehicle_types = [
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

    # Test 1: Single passenger
    print("\n1. Testing P=1 (single passenger)...")
    engine = VehicleOptimizationEngine(vehicle_types, passenger_count=1, num_days=1)
    solutions = engine.optimize(max_solutions=10)
    print(f"   DEBUG: Found {len(solutions)} solutions")
    for i, sol in enumerate(solutions):
        print(
            f"   DEBUG: Solution {i+1}: {[(v.name, c) for v, c in sol.vehicles]}, "
            f"vehicles={sol.total_vehicle_count}, unused={sol.unused_seats}, cost=₹{sol.total_cost}"
        )
    assert len(solutions) > 0, "Should find solutions"
    best = solutions[0]
    assert best.total_vehicle_count == 1, "Should use 1 vehicle"
    # The best solution should minimize vehicle count first, then unused seats, then cost
    # For P=1, all single vehicles work, so it should pick the one with minimum unused seats
    # Sedan (4 capacity) has 3 unused, SUV (7) has 6 unused, Van (12) has 11 unused
    # So Sedan should win
    assert (
        best.vehicles[0][0].name == "Sedan"
    ), f"Should select Sedan but got {best.vehicles[0][0].name}"
    print(
        f"   ✓ Best: {best.vehicles[0][0].name} x{best.vehicles[0][1]}, Cost: ₹{best.total_cost}"
    )

    # Test 2: Exact capacity match
    print("\n2. Testing P=12 (exact van capacity)...")
    engine = VehicleOptimizationEngine(vehicle_types, passenger_count=12, num_days=1)
    solutions = engine.optimize()
    best = solutions[0]
    assert best.total_vehicle_count == 1, "Should use 1 vehicle"
    assert best.total_capacity == 12, "Should match exactly"
    assert best.unused_seats == 0, "Should have no unused seats"
    print(
        f"   ✓ Best: {best.vehicles[0][0].name} x{best.vehicles[0][1]}, Unused: {best.unused_seats}, Cost: ₹{best.total_cost}"
    )

    # Test 3: Capacity + 1
    print("\n3. Testing P=13 (capacity + 1)...")
    engine = VehicleOptimizationEngine(vehicle_types, passenger_count=13, num_days=1)
    solutions = engine.optimize()
    best = solutions[0]
    assert best.total_capacity >= 13, "Must meet capacity"
    assert best.total_vehicle_count >= 2, "Should need at least 2 vehicles"
    print(
        f"   ✓ Best: {[(v.name, c) for v, c in best.vehicles]}, Capacity: {best.total_capacity}, Cost: ₹{best.total_cost}"
    )

    # Test 4: Large passenger count
    print("\n4. Testing P=120 (large group)...")
    engine = VehicleOptimizationEngine(vehicle_types, passenger_count=120, num_days=1)
    solutions = engine.optimize()
    best = solutions[0]
    assert best.total_capacity >= 120, "Must meet capacity"
    van_count = sum(count for vehicle, count in best.vehicles if vehicle.name == "Van")
    assert van_count >= 10, "Should prefer vans for efficiency"
    print(
        f"   ✓ Best: {[(v.name, c) for v, c in best.vehicles]}, Capacity: {best.total_capacity}, Cost: ₹{best.total_cost}"
    )

    # Test 5: No under-capacity solutions
    print("\n5. Testing no under-capacity solutions...")
    engine = VehicleOptimizationEngine(vehicle_types, passenger_count=20, num_days=1)
    solutions = engine.optimize()
    for solution in solutions:
        assert (
            solution.total_capacity >= 20
        ), f"Under-capacity solution found: {solution.total_capacity}"
    print(f"   ✓ All {len(solutions)} solutions meet capacity requirement")

    # Test 6: Pricing calculation
    print("\n6. Testing pricing calculation...")
    engine = VehicleOptimizationEngine(vehicle_types, passenger_count=10, num_days=3)
    solutions = engine.optimize()
    best = solutions[0]
    expected_cost_per_day = sum(
        vehicle.base_price_per_day * count for vehicle, count in best.vehicles
    )
    expected_total = expected_cost_per_day * 3
    assert best.cost_per_day == expected_cost_per_day, "Cost per day mismatch"
    assert best.total_cost == expected_total, "Total cost mismatch"
    print(
        f"   ✓ Cost per day: ₹{best.cost_per_day}, Total (3 days): ₹{best.total_cost}"
    )

    # Test 7: Inactive vehicles excluded
    print("\n7. Testing inactive vehicles excluded...")
    vehicles_with_inactive = [
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
    engine = VehicleOptimizationEngine(
        vehicles_with_inactive, passenger_count=10, num_days=1
    )
    solutions = engine.optimize()
    for solution in solutions:
        for vehicle, count in solution.vehicles:
            assert vehicle.is_active, "Inactive vehicle used!"
            assert vehicle.name == "Active Sedan", "Should only use active sedan"
    print("   ✓ Only active vehicles used")

    # Test 8: Calculate vehicle price function
    print("\n8. Testing calculate_vehicle_price function...")
    vehicle_map = {v.id: v for v in vehicle_types}
    allocation = [
        {"transport_option_id": 1, "count": 2},  # 2 sedans
        {"transport_option_id": 2, "count": 1},  # 1 SUV
    ]
    price = calculate_vehicle_price(
        allocation, num_days=3, vehicle_types_map=vehicle_map
    )
    expected = (
        Decimal("1000") * 2 + Decimal("1500") * 1
    ) * 3  # (2000 + 1500) * 3 = 10500
    assert price == expected, f"Price mismatch: {price} != {expected}"
    print(f"   ✓ Calculated price: ₹{price}")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_basic_optimization()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
