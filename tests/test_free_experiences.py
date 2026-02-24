#!/usr/bin/env python
"""
Test script to verify free experiences (base_price = 0) are allowed.
"""

import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from decimal import Decimal

from packages.models import Experience
from packages.serializers import ExperienceSerializer


def test_free_experience_model():
    """Test that Experience model accepts base_price = 0"""
    print("\n🧪 Testing Free Experience Model Validation...")

    try:
        # Create a free experience
        free_exp = Experience(
            name="Free Walking Tour",
            description="A complimentary walking tour of the historic city center. "
            * 3,
            base_price=Decimal("0.00"),
            duration_hours=Decimal("2.0"),
            max_participants=20,
            difficulty_level="EASY",
            category="CULTURAL",
        )

        # Validate using full_clean (runs model validators)
        free_exp.full_clean()
        print("   ✅ Model validation passed for base_price = 0")

        # Test with negative price (should fail)
        try:
            negative_exp = Experience(
                name="Invalid Experience",
                description="This should fail validation" * 5,
                base_price=Decimal("-10.00"),
                duration_hours=Decimal("2.0"),
            )
            negative_exp.full_clean()
            print("   ❌ Negative price should have failed validation")
        except Exception as e:
            print(f"   ✅ Negative price correctly rejected: {str(e)[:50]}...")

        return True

    except Exception as e:
        print(f"   ❌ Model validation failed: {e}")
        return False


def test_free_experience_serializer():
    """Test that ExperienceSerializer accepts base_price = 0"""
    print("\n🧪 Testing Free Experience Serializer Validation...")

    try:
        # Test with free experience
        data = {
            "name": "Free Cultural Workshop",
            "description": "A free workshop introducing local cultural practices and traditions. "
            * 3,
            "base_price": "0.00",
            "duration_hours": "3.0",
            "max_participants": 15,
            "difficulty_level": "EASY",
            "category": "CULTURAL",
        }

        serializer = ExperienceSerializer(data=data)
        if serializer.is_valid():
            print("   ✅ Serializer validation passed for base_price = 0")
        else:
            print(f"   ❌ Serializer validation failed: {serializer.errors}")
            return False

        # Test with negative price (should fail)
        data_negative = data.copy()
        data_negative["base_price"] = "-5.00"
        serializer_negative = ExperienceSerializer(data=data_negative)

        if not serializer_negative.is_valid():
            print(f"   ✅ Negative price correctly rejected by serializer")
        else:
            print("   ❌ Negative price should have been rejected")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Serializer test failed: {e}")
        return False


def test_price_range():
    """Test various price points"""
    print("\n🧪 Testing Price Range Validation...")

    test_cases = [
        (Decimal("0.00"), True, "Free experience"),
        (Decimal("50.00"), True, "Low-cost experience"),
        (Decimal("1000.00"), True, "Mid-range experience"),
        (Decimal("100000.00"), True, "Maximum price"),
        (Decimal("-1.00"), False, "Negative price"),
        (Decimal("100001.00"), False, "Exceeds maximum"),
    ]

    all_passed = True

    for price, should_pass, description in test_cases:
        try:
            exp = Experience(
                name=f"Test Experience - {description}",
                description="Test description for validation purposes. " * 5,
                base_price=price,
                duration_hours=Decimal("2.0"),
            )
            exp.full_clean()

            if should_pass:
                print(f"   ✅ {description}: ₹{price} - Passed")
            else:
                print(f"   ❌ {description}: ₹{price} - Should have failed")
                all_passed = False

        except Exception as e:
            if not should_pass:
                print(f"   ✅ {description}: ₹{price} - Correctly rejected")
            else:
                print(f"   ❌ {description}: ₹{price} - Should have passed: {e}")
                all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("🚀 Testing Free Experiences Implementation")
    print("=" * 60)

    results = []

    results.append(("Model Validation", test_free_experience_model()))
    results.append(("Serializer Validation", test_free_experience_serializer()))
    results.append(("Price Range Validation", test_price_range()))

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("-" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("✅ All tests passed! Free experiences are now supported.")
        print("\n📝 Next Steps:")
        print("   1. Run migration: python manage.py migrate packages")
        print("   2. Test in Django admin or API")
        print("   3. Create free experiences with base_price = 0")
    else:
        print("❌ Some tests failed. Please review the implementation.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
