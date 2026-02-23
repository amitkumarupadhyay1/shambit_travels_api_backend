#!/usr/bin/env python
"""
Test script for vehicle suggestions API endpoint
"""

import requests

BASE_URL = "http://localhost:8000/api"


def test_vehicle_suggestions():
    """Test the vehicle suggestions endpoint"""

    print("=" * 60)
    print("Testing Vehicle Suggestions API")
    print("=" * 60)

    # Test case 1: 10 passengers, 3 days
    print("\n1. Testing with 10 passengers, 3 days...")
    response = requests.post(
        f"{BASE_URL}/packages/vehicle-suggestions/",
        json={"passenger_count": 10, "num_days": 3, "max_solutions": 5},
        headers={"Content-Type": "application/json"},
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Found {len(data['solutions'])} solutions")

        for i, solution in enumerate(data["solutions"], 1):
            print(f"\n  Solution {i}:")
            for vehicle in solution["vehicles"]:
                print(
                    f"    - {vehicle['count']} × {vehicle['name']} ({vehicle['capacity']} seats)"
                )
            print(
                f"    Total: {solution['total_vehicle_count']} vehicles, {solution['total_capacity']} seats"
            )
            print(f"    Unused: {solution['unused_seats']} seats")
            print(
                f"    Cost: ₹{solution['total_cost']} (₹{solution['cost_per_day']}/day)"
            )
            if solution.get("recommended"):
                print("    ⭐ RECOMMENDED")
    else:
        print(f"✗ Error: {response.text}")

    # Test case 2: 1 passenger, 2 days
    print("\n2. Testing with 1 passenger, 2 days...")
    response = requests.post(
        f"{BASE_URL}/packages/vehicle-suggestions/",
        json={"passenger_count": 1, "num_days": 2},
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Found {len(data['solutions'])} solutions")
        if data["solutions"]:
            solution = data["solutions"][0]
            print(
                f"  Best: {solution['vehicles'][0]['name']} - ₹{solution['total_cost']}"
            )
    else:
        print(f"✗ Error: {response.text}")

    # Test case 3: Invalid input
    print("\n3. Testing with invalid input (0 passengers)...")
    response = requests.post(
        f"{BASE_URL}/packages/vehicle-suggestions/",
        json={"passenger_count": 0, "num_days": 3},
        headers={"Content-Type": "application/json"},
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 400:
        print("✓ Correctly rejected invalid input")
        print("  Error: {}".format(response.json().get("error")))
    else:
        print("✗ Should have returned 400 error")

    print("\n" + "=" * 60)
    print("✅ API Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_vehicle_suggestions()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server")
        print("   Make sure the Django server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
