#!/usr/bin/env python
"""
Payment Integrity Test Script
Tests the complete payment flow to ensure amount consistency.
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.bookings.models import Booking
from apps.bookings.services.booking_service import BookingService
from apps.packages.models import Experience, HotelTier, Package, TransportOption
from apps.payments.services.payment_service import RazorpayService

User = get_user_model()


def test_payment_integrity():
    """Test payment amount consistency across the system."""

    print("=" * 80)
    print("PAYMENT INTEGRITY TEST")
    print("=" * 80)

    # Get test data
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found. Please create a user first.")
            return False

        package = Package.objects.filter(is_active=True).first()
        if not package:
            print("❌ No active packages found.")
            return False

        experiences = package.experiences.all()[:2]
        hotel_tier = package.hotel_tiers.first()
        transport = package.transport_options.first()

        if not experiences or not hotel_tier or not transport:
            print("❌ Package missing required components.")
            return False

        print(f"\n✅ Test data loaded:")
        print(f"   User: {user.email}")
        print(f"   Package: {package.name}")
        print(f"   Experiences: {[e.name for e in experiences]}")
        print(f"   Hotel: {hotel_tier.name}")
        print(f"   Transport: {transport.name}")

    except Exception as e:
        print(f"❌ Failed to load test data: {e}")
        return False

    # Test Case 1: Booking without traveler details (all adults)
    print("\n" + "-" * 80)
    print("TEST CASE 1: Booking without traveler details (all adults)")
    print("-" * 80)

    try:
        booking1 = BookingService.calculate_and_create_booking(
            package=package,
            experience_ids=[e.id for e in experiences],
            hotel_tier_id=hotel_tier.id,
            transport_option_id=transport.id,
            user=user,
            booking_date="2026-03-01",
            num_travelers=3,
            customer_name="Test User",
            customer_email="test@example.com",
            customer_phone="1234567890",
            traveler_details=None,
        )

        print(f"\n✅ Booking created: #{booking1.id}")
        print(f"   Per-person price: ₹{booking1.total_price}")
        print(f"   Number of travelers: {booking1.num_travelers}")
        print(f"   Chargeable travelers: {booking1.get_chargeable_travelers_count()}")
        print(f"   Total amount paid: ₹{booking1.total_amount_paid}")

        # Verify calculation
        expected_total = booking1.total_price * booking1.num_travelers
        if booking1.total_amount_paid == expected_total:
            print(
                f"   ✅ Amount calculation correct: ₹{booking1.total_price} × {booking1.num_travelers} = ₹{expected_total}"
            )
        else:
            print(
                f"   ❌ Amount mismatch: Expected ₹{expected_total}, got ₹{booking1.total_amount_paid}"
            )
            return False

        # Test payment order creation
        razorpay_service = RazorpayService()
        order = razorpay_service.create_order(booking1)

        expected_paise = int(booking1.total_amount_paid * 100)
        if order["amount"] == expected_paise:
            print(
                f"   ✅ Razorpay order amount correct: {order['amount']} paise (₹{order['amount']/100})"
            )
        else:
            print(
                f"   ❌ Razorpay amount mismatch: Expected {expected_paise}, got {order['amount']}"
            )
            return False

        # Cleanup
        booking1.delete()

    except Exception as e:
        print(f"❌ Test Case 1 failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test Case 2: Booking with traveler details (mixed ages)
    print("\n" + "-" * 80)
    print("TEST CASE 2: Booking with traveler details (mixed ages)")
    print("-" * 80)

    try:
        traveler_details = [
            {"name": "Adult 1", "age": 30, "gender": "male"},
            {"name": "Adult 2", "age": 28, "gender": "female"},
            {"name": "Child 1", "age": 7, "gender": "male"},
            {"name": "Child 2", "age": 3, "gender": "female"},  # Free (under 5)
        ]

        booking2 = BookingService.calculate_and_create_booking(
            package=package,
            experience_ids=[e.id for e in experiences],
            hotel_tier_id=hotel_tier.id,
            transport_option_id=transport.id,
            user=user,
            booking_date="2026-03-01",
            num_travelers=4,
            customer_name="Test Family",
            customer_email="family@example.com",
            customer_phone="1234567890",
            traveler_details=traveler_details,
        )

        print(f"\n✅ Booking created: #{booking2.id}")
        print(f"   Per-person price: ₹{booking2.total_price}")
        print(f"   Number of travelers: {booking2.num_travelers}")
        print(f"   Traveler ages: {[t['age'] for t in traveler_details]}")
        print(
            f"   Chargeable travelers (age ≥ 5): {booking2.get_chargeable_travelers_count()}"
        )
        print(f"   Total amount paid: ₹{booking2.total_amount_paid}")

        # Verify calculation (3 chargeable travelers)
        expected_chargeable = 3
        expected_total = booking2.total_price * expected_chargeable

        if booking2.get_chargeable_travelers_count() == expected_chargeable:
            print(f"   ✅ Chargeable travelers correct: {expected_chargeable}")
        else:
            print(
                f"   ❌ Chargeable travelers mismatch: Expected {expected_chargeable}, got {booking2.get_chargeable_travelers_count()}"
            )
            return False

        if booking2.total_amount_paid == expected_total:
            print(
                f"   ✅ Amount calculation correct: ₹{booking2.total_price} × {expected_chargeable} = ₹{expected_total}"
            )
        else:
            print(
                f"   ❌ Amount mismatch: Expected ₹{expected_total}, got ₹{booking2.total_amount_paid}"
            )
            return False

        # Test payment order creation
        razorpay_service = RazorpayService()
        order = razorpay_service.create_order(booking2)

        expected_paise = int(booking2.total_amount_paid * 100)
        if order["amount"] == expected_paise:
            print(
                f"   ✅ Razorpay order amount correct: {order['amount']} paise (₹{order['amount']/100})"
            )
        else:
            print(
                f"   ❌ Razorpay amount mismatch: Expected {expected_paise}, got {order['amount']}"
            )
            return False

        # Test price validation
        is_valid, error_msg = BookingService.validate_price(booking2)
        if is_valid:
            print(f"   ✅ Price validation passed")
        else:
            print(f"   ❌ Price validation failed: {error_msg}")
            return False

        # Cleanup
        booking2.delete()

    except Exception as e:
        print(f"❌ Test Case 2 failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Payment integrity verified!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_payment_integrity()
    sys.exit(0 if success else 1)
