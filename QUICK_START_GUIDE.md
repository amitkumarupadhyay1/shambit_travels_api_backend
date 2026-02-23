# Vehicle Optimization - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### 1. Apply Migrations
```bash
cd backend
python manage.py migrate packages
python manage.py migrate bookings
```

### 2. Populate Vehicle Data (Optional)
If you have existing TransportOptions without the new fields:

```python
python manage.py shell

from packages.models import TransportOption

# Set base_price_per_day for existing vehicles
for transport in TransportOption.objects.all():
    if not transport.base_price_per_day:
        transport.base_price_per_day = transport.base_price
    if not hasattr(transport, 'passenger_capacity') or transport.passenger_capacity == 4:
        # Set appropriate capacities based on vehicle type
        if 'sedan' in transport.name.lower():
            transport.passenger_capacity = 4
        elif 'suv' in transport.name.lower():
            transport.passenger_capacity = 7
        elif 'van' in transport.name.lower():
            transport.passenger_capacity = 12
    transport.save()
```

### 3. Test the API
```bash
# Start the server
python manage.py runserver

# In another terminal, test the endpoint
curl -X POST http://localhost:8000/api/vehicle-suggestions/ \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_count": 10,
    "num_days": 3,
    "max_solutions": 5
  }'
```

### 4. Run Tests
```bash
python test_vehicle_optimization_simple.py
```

Expected output:
```
✅ ALL TESTS PASSED!
```

## 📖 Usage Examples

### Example 1: Get Vehicle Suggestions
```python
import requests

response = requests.post(
    'http://localhost:8000/api/vehicle-suggestions/',
    json={
        'passenger_count': 15,
        'num_days': 2,
        'max_solutions': 10
    }
)

data = response.json()
print(f"Found {len(data['solutions'])} solutions")
print(f"Best: {data['solutions'][0]['vehicles']}")
```

### Example 2: Create Booking with Vehicle Allocation
```python
import requests

# First, get suggestions
suggestions = requests.post(
    'http://localhost:8000/api/vehicle-suggestions/',
    json={'passenger_count': 10, 'num_days': 3}
).json()

# Select the recommended solution
recommended = suggestions['solutions'][0]
vehicle_allocation = [
    {
        'transport_option_id': v['transport_option_id'],
        'count': v['count']
    }
    for v in recommended['vehicles']
]

# Create booking with vehicle allocation
booking = requests.post(
    'http://localhost:8000/api/bookings/',
    headers={
        'Authorization': 'Bearer YOUR_TOKEN',
        'Idempotency-Key': 'unique-key-123'
    },
    json={
        'package_id': 1,
        'experience_ids': [1, 2],
        'hotel_tier_id': 1,
        'transport_option_id': recommended['vehicles'][0]['transport_option_id'],
        'vehicle_allocation': vehicle_allocation,
        'num_travelers': 10,
        'booking_date': '2024-06-01',
        'booking_end_date': '2024-06-04',
        'customer_name': 'John Doe',
        'customer_email': 'john@example.com',
        'customer_phone': '+1234567890'
    }
).json()

print(f"Booking created: {booking['id']}")
```

### Example 3: Check Vehicle Optimization in Admin
```python
from packages.models import TransportOption
from pricing_engine.services.vehicle_optimization import (
    VehicleOptimizationEngine,
    VehicleType
)
from decimal import Decimal

# Get active vehicles
vehicles = [
    VehicleType(
        id=t.id,
        name=t.name,
        passenger_capacity=t.passenger_capacity,
        luggage_capacity=t.luggage_capacity,
        base_price_per_day=t.get_effective_price_per_day(),
        is_active=t.is_active
    )
    for t in TransportOption.objects.filter(is_active=True)
]

# Run optimization
engine = VehicleOptimizationEngine(
    vehicle_types=vehicles,
    passenger_count=25,
    num_days=5
)

solutions = engine.optimize(max_solutions=5)

for i, sol in enumerate(solutions, 1):
    print(f"\nSolution {i}:")
    for vehicle, count in sol.vehicles:
        print(f"  - {vehicle.name} x{count}")
    print(f"  Total vehicles: {sol.total_vehicle_count}")
    print(f"  Capacity: {sol.total_capacity} (unused: {sol.unused_seats})")
    print(f"  Cost: ₹{sol.total_cost}")
```

## 🔍 Troubleshooting

### Issue: No solutions returned
**Cause:** No active vehicles or passenger count is 0
**Solution:**
```python
from packages.models import TransportOption

# Check active vehicles
active = TransportOption.objects.filter(is_active=True)
print(f"Active vehicles: {active.count()}")

# Activate vehicles if needed
TransportOption.objects.all().update(is_active=True)
```

### Issue: Price mismatch
**Cause:** `base_price_per_day` not set
**Solution:**
```python
from packages.models import TransportOption

# Set base_price_per_day
for t in TransportOption.objects.filter(base_price_per_day__isnull=True):
    t.base_price_per_day = t.base_price
    t.save()
```

### Issue: Under-capacity error
**Cause:** Total vehicle capacity < passenger count
**Solution:** The optimization engine prevents this automatically. If you see this error, check:
1. Are there enough active vehicles?
2. Is the passenger count reasonable?
3. Are vehicle capacities set correctly?

## 📊 Monitoring

### Check Optimization Performance
```python
import time
from pricing_engine.services.vehicle_optimization import VehicleOptimizationEngine

# Time the optimization
start = time.time()
engine = VehicleOptimizationEngine(vehicles, passenger_count=100, num_days=3)
solutions = engine.optimize()
elapsed = time.time() - start

print(f"Optimization took {elapsed*1000:.2f}ms")
print(f"Generated {len(solutions)} solutions")
```

### Monitor API Usage
```bash
# Check logs for optimization requests
tail -f logs/django.log | grep "vehicle-suggestions"
```

## 🎯 Best Practices

### 1. Always Use Suggestions Endpoint
Don't manually create vehicle allocations. Always call `/api/vehicle-suggestions/` first.

### 2. Validate on Backend
Never trust client-sent vehicle allocations. The backend always validates and recalculates.

### 3. Handle Passenger Count Changes
If passenger count changes, invalidate previous suggestions and call the endpoint again.

### 4. Set Reasonable max_solutions
Default is 10. For most cases, 5-10 solutions are sufficient.

### 5. Cache Common Queries
Consider caching suggestions for common passenger counts (e.g., 5, 10, 15, 20).

## 📚 Additional Resources

- **Full Documentation:** `VEHICLE_OPTIMIZATION_README.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **API Endpoint:** `/api/vehicle-suggestions/`
- **Test File:** `test_vehicle_optimization_simple.py`

## ✅ Verification Checklist

- [ ] Migrations applied successfully
- [ ] Vehicle data populated
- [ ] API endpoint responds correctly
- [ ] Tests pass
- [ ] Frontend can call the endpoint
- [ ] Bookings can be created with vehicle_allocation
- [ ] Pricing calculates correctly

---

**Need Help?** Check the full documentation or contact the backend team.
