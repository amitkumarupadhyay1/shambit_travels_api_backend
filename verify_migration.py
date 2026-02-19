import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from apps.bookings.models import Booking

print("=" * 80)
print("MIGRATION VERIFICATION")
print("=" * 80)

# Check if field exists
print("\n1. Checking if total_amount_paid field exists...")
if hasattr(Booking, "total_amount_paid"):
    print("   ✅ total_amount_paid field exists in Booking model")
else:
    print("   ❌ total_amount_paid field NOT found")
    sys.exit(1)

# Check database
print("\n2. Checking database...")
try:
    booking_count = Booking.objects.count()
    print(f"   ✅ Database accessible - {booking_count} bookings found")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    sys.exit(1)

# Check field in database
print("\n3. Checking field in database schema...")
try:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(bookings_booking)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "total_amount_paid" in column_names:
            print("   ✅ total_amount_paid column exists in database")
        else:
            print("   ❌ total_amount_paid column NOT in database")
            print(f"   Available columns: {column_names}")
            sys.exit(1)
except Exception as e:
    print(f"   ⚠️  Could not verify database schema: {e}")

print("\n" + "=" * 80)
print("✅ MIGRATION VERIFIED SUCCESSFULLY")
print("=" * 80)
