#!/usr/bin/env python
import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def test_api_endpoints():
    print("Testing Travel Platform API Endpoints...")
    print("=" * 50)

    # Test 1: City Context API
    print("\n1. Testing City Context API")
    try:
        response = requests.get(f"{BASE_URL}/api/cities/city-context/mumbai/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ City: {data['name']}")
            print(f"   Highlights: {len(data['highlights'])}")
            print(f"   Travel Tips: {len(data['travel_tips'])}")
            print(f"   Packages: {len(data['packages'])}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Packages API
    print("\n2. Testing Packages API")
    try:
        response = requests.get(f"{BASE_URL}/api/packages/packages/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total Packages: {data['count']}")
            for package in data["results"]:
                print(f"   - {package['name']} ({package['city_name']})")
                print(f"     Experiences: {len(package['experiences'])}")
                print(f"     Hotel Tiers: {len(package['hotel_tiers'])}")
                print(f"     Transport Options: {len(package['transport_options'])}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Individual Package
    print("\n3. Testing Individual Package API")
    try:
        response = requests.get(f"{BASE_URL}/api/packages/packages/mumbai-explorer/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Package: {data['name']}")
            print(f"   City: {data['city_name']}")
            print(f"   Active: {data['is_active']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: Experiences API
    print("\n4. Testing Experiences API")
    try:
        response = requests.get(f"{BASE_URL}/api/packages/experiences/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total Experiences: {data['count']}")
            for exp in data["results"][:3]:  # Show first 3
                print(f"   - {exp['name']}: ₹{exp['base_price']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 5: Hotel Tiers API
    print("\n5. Testing Hotel Tiers API")
    try:
        response = requests.get(f"{BASE_URL}/api/packages/hotel-tiers/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total Hotel Tiers: {data['count']}")
            for tier in data["results"]:
                print(f"   - {tier['name']}: {tier['price_multiplier']}x multiplier")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 6: Transport Options API
    print("\n6. Testing Transport Options API")
    try:
        response = requests.get(f"{BASE_URL}/api/packages/transport-options/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total Transport Options: {data['count']}")
            for transport in data["results"]:
                print(f"   - {transport['name']}: ₹{transport['base_price']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 7: Admin Interface
    print("\n7. Testing Admin Interface")
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        if response.status_code == 200:
            print("✅ Admin interface accessible")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("API Testing Complete!")


if __name__ == "__main__":
    test_api_endpoints()
