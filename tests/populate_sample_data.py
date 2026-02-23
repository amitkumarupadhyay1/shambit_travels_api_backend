#!/usr/bin/env python
import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from cities.models import City, Highlight, TravelTip
from packages.models import Experience, HotelTier, Package, TransportOption


def create_sample_data():
    print("Creating sample data...")

    # Create cities
    mumbai, created = City.objects.get_or_create(
        slug="mumbai",
        defaults={
            "name": "Mumbai",
            "description": "The financial capital of India, known for Bollywood, street food, and vibrant culture.",
            "status": "PUBLISHED",
            "meta_title": "Mumbai Travel Guide - Best Places to Visit",
            "meta_description": "Discover Mumbai's best attractions, food, and experiences in our comprehensive travel guide.",
        },
    )

    goa, created = City.objects.get_or_create(
        slug="goa",
        defaults={
            "name": "Goa",
            "description": "Famous for its beaches, nightlife, and Portuguese heritage.",
            "status": "PUBLISHED",
            "meta_title": "Goa Travel Guide - Beaches, Culture & More",
            "meta_description": "Plan your perfect Goa vacation with our guide to beaches, culture, and attractions.",
        },
    )

    # Create highlights for Mumbai
    Highlight.objects.get_or_create(
        city=mumbai,
        title="Gateway of India",
        defaults={
            "description": "Iconic monument overlooking the Arabian Sea",
            "icon": "landmark",
        },
    )

    Highlight.objects.get_or_create(
        city=mumbai,
        title="Marine Drive",
        defaults={
            "description": "Beautiful seafront promenade perfect for evening walks",
            "icon": "waves",
        },
    )

    # Create travel tips
    TravelTip.objects.get_or_create(
        city=mumbai,
        title="Best Time to Visit",
        defaults={
            "content": "October to March offers pleasant weather with minimal rainfall."
        },
    )

    # Create experiences
    exp1, created = Experience.objects.get_or_create(
        name="City Walking Tour",
        defaults={
            "description": "Guided walking tour of historical landmarks",
            "base_price": 1500.00,
        },
    )

    exp2, created = Experience.objects.get_or_create(
        name="Food Street Tour",
        defaults={
            "description": "Taste authentic local street food",
            "base_price": 2000.00,
        },
    )

    exp3, created = Experience.objects.get_or_create(
        name="Bollywood Studio Visit",
        defaults={
            "description": "Behind-the-scenes tour of film studios",
            "base_price": 3500.00,
        },
    )

    # Create hotel tiers
    budget, created = HotelTier.objects.get_or_create(
        name="Budget",
        defaults={
            "description": "Clean and comfortable budget accommodations",
            "price_multiplier": 1.0,
        },
    )

    standard, created = HotelTier.objects.get_or_create(
        name="Standard",
        defaults={
            "description": "3-star hotels with good amenities",
            "price_multiplier": 1.5,
        },
    )

    luxury, created = HotelTier.objects.get_or_create(
        name="Luxury",
        defaults={
            "description": "5-star luxury hotels with premium services",
            "price_multiplier": 2.5,
        },
    )

    # Create transport options
    bus, created = TransportOption.objects.get_or_create(
        name="AC Bus",
        defaults={
            "description": "Comfortable air-conditioned bus travel",
            "base_price": 500.00,
        },
    )

    train, created = TransportOption.objects.get_or_create(
        name="Train",
        defaults={
            "description": "Railway travel with reserved seating",
            "base_price": 800.00,
        },
    )

    flight, created = TransportOption.objects.get_or_create(
        name="Flight",
        defaults={
            "description": "Quick and convenient air travel",
            "base_price": 5000.00,
        },
    )

    # Create packages
    mumbai_package, created = Package.objects.get_or_create(
        slug="mumbai-explorer",
        defaults={
            "city": mumbai,
            "name": "Mumbai Explorer",
            "description": "Comprehensive Mumbai experience with culture, food, and entertainment",
            "is_active": True,
        },
    )

    # Add experiences to package
    mumbai_package.experiences.add(exp1, exp2, exp3)
    mumbai_package.hotel_tiers.add(budget, standard, luxury)
    mumbai_package.transport_options.add(bus, train, flight)

    goa_package, created = Package.objects.get_or_create(
        slug="goa-beaches",
        defaults={
            "city": goa,
            "name": "Goa Beach Paradise",
            "description": "Relax on pristine beaches and enjoy Goan culture",
            "is_active": True,
        },
    )

    goa_package.experiences.add(exp1, exp2)
    goa_package.hotel_tiers.add(budget, standard, luxury)
    goa_package.transport_options.add(bus, train, flight)

    print("Sample data created successfully!")
    print(f"Cities: {City.objects.count()}")
    print(f"Packages: {Package.objects.count()}")
    print(f"Experiences: {Experience.objects.count()}")
    print(f"Hotel Tiers: {HotelTier.objects.count()}")
    print(f"Transport Options: {TransportOption.objects.count()}")


if __name__ == "__main__":
    create_sample_data()
