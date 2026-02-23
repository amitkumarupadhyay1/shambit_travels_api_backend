"""
Vehicle Selection Optimization Engine

Implements mathematical optimization for multi-vehicle combinations:
- Integer linear programming approach
- Lexicographic ranking (vehicle count > unused seats > cost)
- Dominance elimination
- Pruning for performance
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from math import ceil
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class VehicleType:
    """Represents a vehicle type with its properties"""

    id: int
    name: str
    passenger_capacity: int
    luggage_capacity: int
    base_price_per_day: Decimal
    is_active: bool


@dataclass
class VehicleCombination:
    """Represents a specific vehicle combination solution"""

    vehicles: List[Tuple[VehicleType, int]]  # List of (vehicle_type, count)
    total_vehicle_count: int
    total_capacity: int
    unused_seats: int
    cost_per_day: Decimal
    total_cost: Decimal
    num_days: int

    def __lt__(self, other):
        """
        Lexicographic comparison for ranking.
        Priority: vehicle_count < unused_seats < total_cost
        """
        if self.total_vehicle_count != other.total_vehicle_count:
            return self.total_vehicle_count < other.total_vehicle_count
        if self.unused_seats != other.unused_seats:
            return self.unused_seats < other.unused_seats
        return self.total_cost < other.total_cost

    def dominates(self, other) -> bool:
        """
        Check if this solution dominates another.
        A dominates B if A is better or equal in all dimensions with at least one strictly better.
        """
        vehicles_better_or_equal = self.total_vehicle_count <= other.total_vehicle_count
        unused_better_or_equal = self.unused_seats <= other.unused_seats
        cost_better_or_equal = self.total_cost <= other.total_cost

        at_least_one_strictly_better = (
            self.total_vehicle_count < other.total_vehicle_count
            or self.unused_seats < other.unused_seats
            or self.total_cost < other.total_cost
        )

        return (
            vehicles_better_or_equal
            and unused_better_or_equal
            and cost_better_or_equal
            and at_least_one_strictly_better
        )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "vehicles": [
                {
                    "transport_option_id": vehicle.id,
                    "name": vehicle.name,
                    "count": count,
                    "capacity": vehicle.passenger_capacity,
                    "price_per_day": str(vehicle.base_price_per_day),
                }
                for vehicle, count in self.vehicles
            ],
            "total_vehicle_count": self.total_vehicle_count,
            "total_capacity": self.total_capacity,
            "unused_seats": self.unused_seats,
            "cost_per_day": str(self.cost_per_day),
            "total_cost": str(self.total_cost),
            "num_days": self.num_days,
        }


class VehicleOptimizationEngine:
    """
    Mathematical optimization engine for vehicle selection.
    Implements integer linear programming with pruning and dominance elimination.
    """

    def __init__(self, vehicle_types: List[VehicleType], passenger_count: int, num_days: int):
        """
        Initialize optimization engine.

        Args:
            vehicle_types: List of available active vehicle types
            passenger_count: Number of passengers to accommodate
            num_days: Number of days for pricing calculation
        """
        self.vehicle_types = [v for v in vehicle_types if v.is_active]
        self.passenger_count = passenger_count
        self.num_days = max(1, ceil(num_days))
        self.best_vehicle_count = float("inf")
        self.solutions: List[VehicleCombination] = []

        # Calculate upper bounds for each vehicle type
        self.max_counts = {
            v.id: ceil(passenger_count / v.passenger_capacity) for v in self.vehicle_types
        }

    def optimize(self, max_solutions: int = 10) -> List[VehicleCombination]:
        """
        Find optimal vehicle combinations.

        Args:
            max_solutions: Maximum number of solutions to return

        Returns:
            List of VehicleCombination sorted by priority (best first)
        """
        if not self.vehicle_types:
            logger.warning("No active vehicle types available for optimization")
            return []

        if self.passenger_count <= 0:
            logger.warning("Invalid passenger count: %d", self.passenger_count)
            return []

        # Generate all valid combinations using recursive backtracking
        self._generate_combinations([], 0, 0, Decimal("0"))

        # Remove dominated solutions
        self.solutions = self._eliminate_dominated(self.solutions)

        # Sort by lexicographic priority
        self.solutions.sort()

        # Return top N solutions
        return self.solutions[:max_solutions]

    def _generate_combinations(
        self,
        current_allocation: List[Tuple[VehicleType, int]],
        vehicle_index: int,
        current_capacity: int,
        current_cost: Decimal,
    ):
        """
        Recursive backtracking to generate valid combinations.

        Args:
            current_allocation: Current vehicle allocation
            vehicle_index: Index of vehicle type being considered
            current_capacity: Current total capacity
            current_cost: Current total cost per day
        """
        # Base case: checked all vehicle types
        if vehicle_index >= len(self.vehicle_types):
            # Check if capacity constraint is satisfied
            if current_capacity >= self.passenger_count:
                total_vehicle_count = sum(count for _, count in current_allocation)
                unused_seats = current_capacity - self.passenger_count
                total_cost = current_cost * self.num_days

                combination = VehicleCombination(
                    vehicles=list(current_allocation),
                    total_vehicle_count=total_vehicle_count,
                    total_capacity=current_capacity,
                    unused_seats=unused_seats,
                    cost_per_day=current_cost,
                    total_cost=total_cost,
                    num_days=self.num_days,
                )

                self.solutions.append(combination)

                # Update best vehicle count for pruning
                if total_vehicle_count < self.best_vehicle_count:
                    self.best_vehicle_count = total_vehicle_count

            return

        vehicle = self.vehicle_types[vehicle_index]
        max_count = self.max_counts[vehicle.id]

        # Try different counts of this vehicle type (0 to max_count)
        for count in range(max_count + 1):
            new_capacity = current_capacity + (count * vehicle.passenger_capacity)
            new_cost = current_cost + (count * vehicle.base_price_per_day)
            new_vehicle_count = sum(c for _, c in current_allocation) + count

            # Pruning: skip if already worse than best known solution
            if new_vehicle_count > self.best_vehicle_count:
                continue

            # Pruning: skip if capacity is way over and vehicle count is WORSE than best
            if (
                new_capacity > self.passenger_count * 2
                and new_vehicle_count > self.best_vehicle_count
            ):
                continue

            # Add to allocation if count > 0
            if count > 0:
                current_allocation.append((vehicle, count))

            # Recurse to next vehicle type
            self._generate_combinations(
                current_allocation, vehicle_index + 1, new_capacity, new_cost
            )

            # Backtrack
            if count > 0:
                current_allocation.pop()

    def _eliminate_dominated(
        self, solutions: List[VehicleCombination]
    ) -> List[VehicleCombination]:
        """
        Remove dominated solutions from the list.

        Args:
            solutions: List of solutions to filter

        Returns:
            List of non-dominated solutions
        """
        if not solutions:
            return []

        non_dominated = []

        for i, solution_a in enumerate(solutions):
            is_dominated = False

            for j, solution_b in enumerate(solutions):
                if i != j and solution_b.dominates(solution_a):
                    is_dominated = True
                    break

            if not is_dominated:
                non_dominated.append(solution_a)

        logger.info(
            f"Eliminated {len(solutions) - len(non_dominated)} dominated solutions "
            f"({len(non_dominated)} remaining)"
        )

        return non_dominated

    def get_recommended_combination(self) -> Optional[VehicleCombination]:
        """
        Get the top-ranked (recommended) combination.

        Returns:
            Best VehicleCombination or None if no solutions found
        """
        solutions = self.optimize(max_solutions=1)
        return solutions[0] if solutions else None


def calculate_vehicle_price(
    vehicle_allocation: List[dict], num_days: int, vehicle_types_map: dict
) -> Decimal:
    """
    Calculate total price for a vehicle allocation.

    Args:
        vehicle_allocation: List of {"transport_option_id": int, "count": int}
        num_days: Number of days
        vehicle_types_map: Dict mapping transport_option_id to VehicleType

    Returns:
        Total price as Decimal
    """
    days = max(1, ceil(num_days))
    total_cost = Decimal("0")

    for allocation in vehicle_allocation:
        transport_id = allocation["transport_option_id"]
        count = allocation["count"]

        if transport_id in vehicle_types_map:
            vehicle = vehicle_types_map[transport_id]
            total_cost += vehicle.base_price_per_day * count

    return total_cost * days
