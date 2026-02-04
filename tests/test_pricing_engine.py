#!/usr/bin/env python
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from decimal import Decimal

from packages.models import Experience, HotelTier, Package, TransportOption
from pricing_engine.models import PricingRule
from pricing_engine.services.pricing_service import PricingService


def test_pricing_engine():
    print("🧮 COMPREHENSIVE PRICING ENGINE TEST")
    print("=" * 60)

    # Test 1: Basic pricing calculation
    print("\n1. BASIC PRICING CALCULATION")
    print("-" * 30)

    mumbai_package = Package.objects.filter(slug="mumbai-explorer").first()
    if not mumbai_package:
        print("❌ Mumbai package not found")
        return

    # Get components
    experiences = list(mumbai_package.experiences.all()[:2])  # First 2 experiences
    hotel_tier = mumbai_package.hotel_tiers.filter(name="Budget").first()
    transport = mumbai_package.transport_options.filter(name="AC Bus").first()

    if not all([experiences, hotel_tier, transport]):
        print("❌ Required components not found")
        return

    # Calculate price
    total_price = PricingService.calculate_total(
        mumbai_package, experiences, hotel_tier, transport
    )
    print(f"✅ Total Price: ₹{total_price}")

    # Test 2: Price breakdown
    print("\n2. DETAILED PRICE BREAKDOWN")
    print("-" * 30)

    breakdown = PricingService.get_price_breakdown(
        mumbai_package, experiences, hotel_tier, transport
    )

    print(f"Base experiences: ₹{breakdown['base_experience_total']}")
    print(f"Transport cost: ₹{breakdown['transport_cost']}")
    print(f"Subtotal before hotel: ₹{breakdown['subtotal_before_hotel']}")
    print(f"Hotel multiplier: {breakdown['hotel_multiplier']}x")
    print(f"Subtotal after hotel: ₹{breakdown['subtotal_after_hotel']}")
    print(f"Total markup: ₹{breakdown['total_markup']}")
    print(f"Total discount: ₹{breakdown['total_discount']}")
    print(f"FINAL TOTAL: ₹{breakdown['final_total']}")

    print(f"\nApplied Rules ({len(breakdown['applied_rules'])}):")
    for rule in breakdown["applied_rules"]:
        symbol = "%" if rule["is_percentage"] == "True" else ""
        print(
            f"  • {rule['name']}: {rule['type']} {rule['value']}{symbol} = ₹{rule['amount_applied']}"
        )

    # Test 3: Price range estimation
    print("\n3. PRICE RANGE ESTIMATION")
    print("-" * 30)

    price_range = PricingService.get_price_estimate_range(mumbai_package)
    print(f"Min Price: ₹{price_range['min_price']}")
    print(f"Max Price: ₹{price_range['max_price']}")
    print(f"Currency: {price_range['currency']}")

    # Test 4: Component validation
    print("\n4. COMPONENT VALIDATION")
    print("-" * 30)

    errors = PricingService.validate_price_components(
        mumbai_package, experiences, hotel_tier, transport
    )
    if errors:
        print("❌ Validation errors:")
        for error in errors:
            print(f"  • {error}")
    else:
        print("✅ All components valid")

    # Test 5: Different hotel tiers
    print("\n5. HOTEL TIER COMPARISON")
    print("-" * 30)

    for tier in mumbai_package.hotel_tiers.all():
        tier_price = PricingService.calculate_total(
            mumbai_package, experiences, tier, transport
        )
        print(f"{tier.name} ({tier.price_multiplier}x): ₹{tier_price}")

    # Test 6: Different transport options
    print("\n6. TRANSPORT OPTION COMPARISON")
    print("-" * 30)

    budget_hotel = mumbai_package.hotel_tiers.filter(name="Budget").first()
    for transport_opt in mumbai_package.transport_options.all():
        transport_price = PricingService.calculate_total(
            mumbai_package, experiences, budget_hotel, transport_opt
        )
        print(f"{transport_opt.name} (₹{transport_opt.base_price}): ₹{transport_price}")

    # Test 7: Active pricing rules
    print("\n7. ACTIVE PRICING RULES")
    print("-" * 30)

    active_rules = PricingService.get_applicable_rules(mumbai_package)
    print(f"Total active rules: {len(active_rules)}")

    for rule in active_rules:
        target = rule.target_package.name if rule.target_package else "All Packages"
        print(f"• {rule.name}")
        print(f"  Type: {rule.rule_type}")
        print(f"  Value: {rule.value}{'%' if rule.is_percentage else ''}")
        print(f"  Target: {target}")
        print(f"  Active: {rule.active_from} to {rule.active_to or 'Indefinite'}")
        print()

    # Test 8: Edge cases
    print("\n8. EDGE CASE TESTING")
    print("-" * 30)

    # Test with no experiences
    try:
        no_exp_price = PricingService.calculate_total(
            mumbai_package, [], hotel_tier, transport
        )
        print(f"✅ No experiences: ₹{no_exp_price}")
    except Exception as e:
        print(f"❌ No experiences error: {e}")

    # Test with all experiences
    try:
        all_exp_price = PricingService.calculate_total(
            mumbai_package, mumbai_package.experiences.all(), hotel_tier, transport
        )
        print(f"✅ All experiences: ₹{all_exp_price}")
    except Exception as e:
        print(f"❌ All experiences error: {e}")

    # Test 9: Performance check
    print("\n9. PERFORMANCE TEST")
    print("-" * 30)

    import time

    start_time = time.time()

    for i in range(100):
        PricingService.calculate_total(
            mumbai_package, experiences, hotel_tier, transport
        )

    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    print(f"✅ Average calculation time: {avg_time:.2f}ms (100 iterations)")

    print("\n" + "=" * 60)
    print("🎉 PRICING ENGINE TEST COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    test_pricing_engine()
