#!/bin/bash
# Payment Integrity Test using Django shell

python manage.py shell << 'EOF'
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.bookings.services.booking_service import BookingService
from apps.payments.services.payment_service import RazorpayService
from apps.packages.models import Package

User = get_user_model()

print("=" * 80)
print("PAYMENT INTEGRITY TEST")
print("=" * 80)

# Get test data
user = User.objects.first()
package = Package.objects.filter(is_active=True).first()

if not user or not package:
    print("❌ Missing test data")
    exit(1)

experiences = package.experiences.all()[:2]
hotel_tier = package.hotel_tiers.first()
transport = package.transport_options.first()

print(f"\n✅ Test data loaded:")
print(f"   User: {user.email}")
print(f"   Package: {package.name}")

# Test Case 1: Booking with mixed ages
print("\n" + "-" * 80)
print("TEST CASE: Booking with mixed ages (age-based pricing)")
print("-" * 80)

traveler_details = [
    {"name": "Adult 1", "age": 30, "gender": "male"},
    {"name": "Adult 2", "age": 28, "gender": "female"},
    {"name": "Child 1", "age": 7, "gender": "male"},
    {"name": "Child 2", "age": 3, "gender": "female"},  # Free (under 5)
]

booking = BookingService.calculate_and_create_booking(
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

print(f"\n✅ Booking created: #{booking.id}")
print(f"   Per-person price: ₹{booking.total_price}")
print(f"   Number of travelers: {booking.num_travelers}")
print(f"   Traveler ages: {[t['age'] for t in traveler_details]}")
print(f"   Chargeable travelers (age ≥ 5): {booking.get_chargeable_travelers_count()}")
print(f"   Total amount paid (STORED): ₹{booking.total_amount_paid}")

# Verify calculation
expected_chargeable = 3
expected_total = booking.total_price * expected_chargeable

if booking.get_chargeable_travelers_count() == expected_chargeable:
    print(f"   ✅ Chargeable travelers correct: {expected_chargeable}")
else:
    print(f"   ❌ Chargeable travelers mismatch")

if booking.total_amount_paid == expected_total:
    print(f"   ✅ Amount calculation correct: ₹{booking.total_price} × {expected_chargeable} = ₹{expected_total}")
else:
    print(f"   ❌ Amount mismatch: Expected ₹{expected_total}, got ₹{booking.total_amount_paid}")

# Test payment order creation
razorpay_service = RazorpayService()
order = razorpay_service.create_order(booking)

expected_paise = int(booking.total_amount_paid * 100)
if order["amount"] == expected_paise:
    print(f"   ✅ Razorpay order amount correct: {order['amount']} paise (₹{order['amount']/100})")
else:
    print(f"   ❌ Razorpay amount mismatch")

# Test price validation
is_valid, error_msg = BookingService.validate_price(booking)
if is_valid:
    print(f"   ✅ Price validation passed")
else:
    print(f"   ❌ Price validation failed: {error_msg}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETED - Check results above")
print("=" * 80)
print(f"\nBooking ID: {booking.id} (not deleted for manual inspection)")

EOF
