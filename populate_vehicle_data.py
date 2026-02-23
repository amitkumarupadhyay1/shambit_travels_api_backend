#!/usr/bin/env python
"""
Populate vehicle optimization data for existing TransportOptions
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.local')
django.setup()

from packages.models import TransportOption
from decimal import Decimal

def populate_vehicle_data():
    """Populate base_price_per_day and capacity data for existing vehicles"""
    
    print("=" * 60)
    print("Populating Vehicle Optimization Data")
    print("=" * 60)
    
    # Define vehicle data mapping
    vehicle_data = {
        'Local Transport': {
            'base_price_per_day': Decimal('600.00'),
            'passenger_capacity': 4,
            'luggage_capacity': 2,
        },
        'Private Car': {
            'base_price_per_day': Decimal('1000.00'),
            'passenger_capacity': 4,
            'luggage_capacity': 3,
        },
        'AC Bus': {
            'base_price_per_day': Decimal('3500.00'),
            'passenger_capacity': 25,
            'luggage_capacity': 20,
        },
        'Train': {
            'base_price_per_day': Decimal('500.00'),
            'passenger_capacity': 50,
            'luggage_capacity': 30,
        },
        'Rental Bike': {
            'base_price_per_day': Decimal('300.00'),
            'passenger_capacity': 2,
            'luggage_capacity': 1,
        },
        'Flight': {
            'base_price_per_day': Decimal('5000.00'),
            'passenger_capacity': 150,
            'luggage_capacity': 100,
        },
    }
    
    # Add common vehicle types if they don't exist
    common_vehicles = [
        {
            'name': 'Sedan',
            'description': 'Comfortable 4-seater car with AC',
            'base_price': Decimal('800.00'),
            'base_price_per_day': Decimal('800.00'),
            'passenger_capacity': 4,
            'luggage_capacity': 2,
            'is_active': True,
        },
        {
            'name': 'SUV',
            'description': 'Spacious 7-seater SUV with AC',
            'base_price': Decimal('1500.00'),
            'base_price_per_day': Decimal('1500.00'),
            'passenger_capacity': 7,
            'luggage_capacity': 4,
            'is_active': True,
        },
        {
            'name': 'Van',
            'description': '12-seater van with AC',
            'base_price': Decimal('2500.00'),
            'base_price_per_day': Decimal('2500.00'),
            'passenger_capacity': 12,
            'luggage_capacity': 8,
            'is_active': True,
        },
        {
            'name': 'Tempo Traveller',
            'description': '14-seater tempo traveller with push-back seats',
            'base_price': Decimal('3000.00'),
            'base_price_per_day': Decimal('3000.00'),
            'passenger_capacity': 14,
            'luggage_capacity': 10,
            'is_active': True,
        },
    ]
    
    # Update existing vehicles
    updated_count = 0
    for transport in TransportOption.objects.all():
        if transport.name in vehicle_data:
            data = vehicle_data[transport.name]
            transport.base_price_per_day = data['base_price_per_day']
            transport.passenger_capacity = data['passenger_capacity']
            transport.luggage_capacity = data['luggage_capacity']
            transport.is_active = True
            transport.save()
            print(f"✓ Updated: {transport.name}")
            updated_count += 1
        elif not transport.base_price_per_day:
            # Fallback: use base_price as base_price_per_day
            transport.base_price_per_day = transport.base_price
            transport.save()
            print(f"✓ Set base_price_per_day from base_price: {transport.name}")
            updated_count += 1
    
    # Create common vehicles if they don't exist
    created_count = 0
    for vehicle in common_vehicles:
        if not TransportOption.objects.filter(name=vehicle['name']).exists():
            TransportOption.objects.create(**vehicle)
            print(f"✓ Created: {vehicle['name']}")
            created_count += 1
        else:
            # Update if exists
            transport = TransportOption.objects.get(name=vehicle['name'])
            for key, value in vehicle.items():
                if key != 'name':
                    setattr(transport, key, value)
            transport.save()
            print(f"✓ Updated: {vehicle['name']}")
            updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Complete! Updated: {updated_count}, Created: {created_count}")
    print("=" * 60)
    
    # Display all active vehicles
    print("\nActive Vehicles:")
    for transport in TransportOption.objects.filter(is_active=True).order_by('passenger_capacity'):
        print(f"  {transport.name}: {transport.passenger_capacity} seats, ₹{transport.base_price_per_day}/day")

if __name__ == "__main__":
    populate_vehicle_data()
