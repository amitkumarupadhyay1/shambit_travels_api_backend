#!/usr/bin/env python
"""
Test script to verify Phase 3 pricing configuration
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")
django.setup()

from pricing_engine.models import PricingConfiguration


def test_phase3_config():
    """Test Phase 3 configuration fields"""
    print("=" * 60)
    print("PHASE 3 PRICING CONFIGURATION TEST")
    print("=" * 60)

    try:
        # Get configuration
        config = PricingConfiguration.get_config()

        print("\n✅ Configuration Retrieved Successfully\n")

        # Test Phase 3 fields
        print("Phase 3 Fields:")
        print(f"  • GST Rate: {config.gst_rate}%")
        print(f"  • Platform Fee Rate: {config.platform_fee_rate}%")
        print(f"  • Price Lock Duration: {config.price_lock_duration_minutes} minutes")
        print(
            f"  • Price Change Alert Threshold: {config.price_change_alert_threshold}%"
        )
        print(f"  • Enable Price Change Alerts: {config.enable_price_change_alerts}")

        print("\nExisting Fields:")
        print(f"  • Chargeable Age Threshold: {config.chargeable_age_threshold} years")
        print(f"  • Weekend Multiplier: {config.default_weekend_multiplier}x")
        print(f"  • Min Advance Booking: {config.min_advance_booking_days} days")
        print(f"  • Max Advance Booking: {config.max_advance_booking_days} days")

        print("\n" + "=" * 60)
        print("✅ ALL PHASE 3 FIELDS ACCESSIBLE")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_phase3_config()
    exit(0 if success else 1)
