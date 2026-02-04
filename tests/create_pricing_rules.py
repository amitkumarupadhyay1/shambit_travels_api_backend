#!/usr/bin/env python
import os
import sys
from datetime import datetime, timedelta

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from django.utils import timezone
from packages.models import Package
from pricing_engine.models import PricingRule


def create_pricing_rules():
    print("Creating pricing rules...")

    # Get packages
    mumbai_package = Package.objects.filter(slug="mumbai-explorer").first()

    # 1. Global markup for all packages (platform fee)
    platform_fee, created = PricingRule.objects.get_or_create(
        name="Platform Service Fee",
        defaults={
            "rule_type": "MARKUP",
            "value": 5.0,  # 5% platform fee
            "is_percentage": True,
            "target_package": None,  # Global rule
            "active_from": timezone.now(),
            "is_active": True,
        },
    )
    if created:
        print("✅ Created Platform Service Fee (5% markup)")

    # 2. Seasonal discount for Mumbai
    if mumbai_package:
        seasonal_discount, created = PricingRule.objects.get_or_create(
            name="Mumbai Winter Special",
            defaults={
                "rule_type": "DISCOUNT",
                "value": 10.0,  # 10% discount
                "is_percentage": True,
                "target_package": mumbai_package,
                "active_from": timezone.now(),
                "active_to": timezone.now() + timedelta(days=30),  # Valid for 30 days
                "is_active": True,
            },
        )
        if created:
            print("✅ Created Mumbai Winter Special (10% discount)")

    # 3. Early bird discount (global)
    early_bird, created = PricingRule.objects.get_or_create(
        name="Early Bird Discount",
        defaults={
            "rule_type": "DISCOUNT",
            "value": 500.00,  # Fixed ₹500 discount
            "is_percentage": False,
            "target_package": None,  # Global rule
            "active_from": timezone.now(),
            "active_to": timezone.now() + timedelta(days=15),  # Valid for 15 days
            "is_active": True,
        },
    )
    if created:
        print("✅ Created Early Bird Discount (₹500 off)")

    # 4. Premium service markup
    premium_markup, created = PricingRule.objects.get_or_create(
        name="Premium Service Upgrade",
        defaults={
            "rule_type": "MARKUP",
            "value": 1000.00,  # Fixed ₹1000 markup
            "is_percentage": False,
            "target_package": None,  # Global rule
            "active_from": timezone.now(),
            "is_active": False,  # Disabled by default
        },
    )
    if created:
        print("✅ Created Premium Service Upgrade (₹1000 markup, disabled)")

    # 5. Weekend surcharge for Mumbai
    if mumbai_package:
        weekend_surcharge, created = PricingRule.objects.get_or_create(
            name="Mumbai Weekend Surcharge",
            defaults={
                "rule_type": "MARKUP",
                "value": 15.0,  # 15% weekend surcharge
                "is_percentage": True,
                "target_package": mumbai_package,
                "active_from": timezone.now(),
                "is_active": False,  # Can be activated for weekends
            },
        )
        if created:
            print("✅ Created Mumbai Weekend Surcharge (15% markup, disabled)")

    print(f"\nTotal pricing rules: {PricingRule.objects.count()}")
    print(f"Active rules: {PricingRule.objects.filter(is_active=True).count()}")

    # Test pricing calculation
    print("\n" + "=" * 50)
    print("TESTING PRICING CALCULATION")
    print("=" * 50)

    if mumbai_package:
        from packages.models import Experience, HotelTier, TransportOption
        from pricing_engine.services.pricing_service import PricingService

        # Get sample components
        experiences = mumbai_package.experiences.all()[:2]  # First 2 experiences
        hotel_tier = mumbai_package.hotel_tiers.filter(name="Standard").first()
        transport = mumbai_package.transport_options.filter(name="Train").first()

        if experiences and hotel_tier and transport:
            breakdown = PricingService.get_price_breakdown(
                mumbai_package, experiences, hotel_tier, transport
            )

            print(f"Package: {mumbai_package.name}")
            print(f"Experiences: {[exp.name for exp in experiences]}")
            print(f"Hotel: {hotel_tier.name}")
            print(f"Transport: {transport.name}")
            print("\nPRICE BREAKDOWN:")
            print(f"Base experiences: ₹{breakdown['base_experience_total']}")
            print(f"Transport: ₹{breakdown['transport_cost']}")
            print(f"Subtotal: ₹{breakdown['subtotal_before_hotel']}")
            print(f"Hotel multiplier: {breakdown['hotel_multiplier']}x")
            print(f"After hotel: ₹{breakdown['subtotal_after_hotel']}")
            print(f"Total markup: ₹{breakdown['total_markup']}")
            print(f"Total discount: ₹{breakdown['total_discount']}")
            print(f"FINAL TOTAL: ₹{breakdown['final_total']}")

            print(f"\nApplied rules: {len(breakdown['applied_rules'])}")
            for rule in breakdown["applied_rules"]:
                print(
                    f"  - {rule['name']}: {rule['type']} {rule['value']}{'%' if rule['is_percentage'] else ''} = ₹{rule['amount_applied']}"
                )


if __name__ == "__main__":
    create_pricing_rules()
