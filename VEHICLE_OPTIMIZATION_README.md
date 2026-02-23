# Vehicle Selection Optimization System

## Overview

This system implements intelligent vehicle suggestion and pricing optimization for multi-vehicle bookings. It uses mathematical optimization to find the best vehicle combinations based on passenger count and trip duration.

## Architecture

### Core Components

1. **Mathematical Optimization Engine** (`pricing_engine/services/vehicle_optimization.py`)
   - Integer linear programming approach
   - Lexicographic ranking (vehicle count > unused seats > cost)
   - Dominance elimination
   - Pruning for performance

2. **Vehicle Suggestions API** (`packages/views_vehicle_suggestions.py`)
   - Endpoint: `POST /api/vehicle-suggestions/`
   - Returns ranked vehicle combinations
   - Backend is source of truth

3. **Pricing Service Integration** (`pricing_engine/services/pricing_service.py`)
   - Updated to handle `vehicle_allocation` override
   - Maintains backward compatibility with `selected_transport`

4. **Database Models**
   - `TransportOption`: Added `base_price_per_day`, `passenger_capacity`, `luggage_capacity`, `is_active`
   - `Booking`: Added `vehicle_allocation` JSONField

## Mathematical Model

### Variables
For each active vehicle type `i`:
- `xᵢ` = number of vehicles of type `i` (integer ≥ 0)

### Constraints
1. **Capacity Constraint**: `Σ (cᵢ × xᵢ) ≥ P`
   - Where `cᵢ` = passenger capacity, `P` = passenger count
   - Under-capacity combinations are invalid

2. **Upper Bound**: `max_xᵢ = ceil(P / cᵢ)`
   - Prevents unnecessary recursion

### Objective Function
Lexicographic minimization (strict priority order):
1. Minimize total vehicle count
2. Minimize unused seats
3. Minimize total cost

### Cost Calculation
```
Total Daily Cost = Σ (pᵢ × xᵢ)
Total Price = Total Daily Cost × ceil(num_days)
```

Where `pᵢ` = base_price_per_day

## API Usage

### Get Vehicle Suggestions

```http
POST /api/vehicle-suggestions/
Content-Type: application/json

{
  "passenger_count": 10,
  "num_days": 3,
  "max_solutions": 10
}
```

Response:
```json
{
  "passenger_count": 10,
  "num_days": 3,
  "solutions": [
    {
      "vehicles": [
        {
          "transport_option_id": 3,
          "name": "Van",
          "count": 1,
          "capacity": 12,
          "price_per_day": "2500.00"
        }
      ],
      "total_vehicle_count": 1,
      "total_capacity": 12,
      "unused_seats": 2,
      "cost_per_day": "2500.00",
      "total_cost": "7500.00",
      "num_days": 3,
      "recommended": true
    }
  ]
}
```

### Create Booking with Vehicle Allocation

```http
POST /api/bookings/
Content-Type: application/json

{
  "package_id": 1,
  "experience_ids": [1, 2],
  "hotel_tier_id": 1,
  "transport_option_id": 3,
  "vehicle_allocation": [
    {"transport_option_id": 3, "count": 1}
  ],
  "num_travelers": 10,
  "booking_date": "2024-06-01",
  "booking_end_date": "2024-06-04",
  ...
}
```

## Pricing Resolution Rules

### Priority Order
1. If `vehicle_allocation` exists and not empty:
   - Use combination pricing (sum of all vehicles × days)
2. Else:
   - Use legacy `selected_transport` pricing

### Backward Compatibility
- `selected_transport` remains required
- If `vehicle_allocation` is provided, `selected_transport` should be the primary (highest-ranked) vehicle
- Legacy bookings without `vehicle_allocation` continue working unchanged

## Validation Rules

### Server-Side Validation
When `vehicle_allocation` is submitted:
1. Validate structure (list of dicts with required fields)
2. Validate all transport IDs exist
3. Validate all are active
4. Validate no duplicate IDs
5. Validate total capacity ≥ passenger_count
6. Recalculate price server-side (ignore client-sent pricing)

### Passenger Count Changes
If passenger count changes after vehicle selection:
- Previous `vehicle_allocation` is invalidated
- Must re-run optimization

## Database Schema

### TransportOption Model
```python
class TransportOption(models.Model):
    name = CharField(max_length=100)
    description = TextField()
    
    # Legacy field (kept for backward compatibility)
    base_price = DecimalField(max_digits=10, decimal_places=2)
    
    # New fields for optimization
    base_price_per_day = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    passenger_capacity = IntegerField(default=4)
    luggage_capacity = IntegerField(default=3)
    is_active = BooleanField(default=True)
```

### Booking Model
```python
class Booking(models.Model):
    # Existing fields...
    selected_transport = ForeignKey(TransportOption)  # Required, remains unchanged
    
    # New field for optimization
    vehicle_allocation = JSONField(default=list, blank=True)
    # Structure: [{"transport_option_id": 1, "count": 2}]
```

## Migrations

### Apply Migrations
```bash
# Apply TransportOption changes
python manage.py migrate packages 0011_add_vehicle_optimization_fields

# Apply Booking changes
python manage.py migrate bookings 0011_add_vehicle_allocation
```

### Data Migration (Optional)
To populate new fields for existing TransportOptions:
```python
from packages.models import TransportOption

for transport in TransportOption.objects.all():
    if not transport.base_price_per_day:
        transport.base_price_per_day = transport.base_price
    transport.save()
```

## Testing

### Run Unit Tests
```bash
# Test optimization engine
pytest backend/apps/pricing_engine/tests/test_vehicle_optimization.py -v

# Test integration
pytest backend/apps/bookings/tests/ -v
```

### Test Cases Covered
- Single passenger (P = 1)
- Exact capacity match (P = 12 for van)
- Capacity + 1 (P = 13)
- Large passenger count (P = 120)
- Single vehicle type active
- Tie cases
- No under-capacity solutions
- Pricing calculation
- Dominance elimination
- Empty vehicle types
- Zero passengers
- Inactive vehicles excluded

## Performance Characteristics

### Complexity
- Approximately O(vehicle_types × passenger_count)
- Pruning prevents exponential explosion
- Dominance elimination reduces solution space

### Optimization Techniques
1. **Early Termination**: Stop exploring branches worse than best known
2. **Upper Bounds**: Limit maximum vehicles per type
3. **Dominance Filtering**: Remove inferior solutions
4. **Capacity Pruning**: Skip over-capacity combinations

## Edge Cases Handled

1. **No Active Vehicles**: Returns empty solutions with error message
2. **Zero Passengers**: Returns empty solutions
3. **Inactive Vehicles**: Excluded from optimization
4. **Vehicle Deactivated After Preview**: Validation fails on booking
5. **Passenger Count Changed**: Previous allocation invalidated
6. **Fractional Days**: Ceiled to integer (e.g., 1.5 → 2)

## Frontend Integration Guidelines

### Display Recommendations
1. Call `/api/vehicle-suggestions/` with passenger count and days
2. Display returned combinations
3. Highlight first solution as "Best Recommendation"
4. Show breakdown: vehicles, capacity, unused seats, pricing

### Booking Flow
1. User selects a combination
2. Send `vehicle_allocation` in booking request
3. Backend validates and recalculates price
4. Display confirmation with final pricing

### UI/UX Considerations
- Disable manual under-capacity selection
- Show capacity warnings
- Display unused seats clearly
- Provide price comparison between options

## Reporting & Analytics

### Backward Compatibility
- Existing reports using `selected_transport` continue working
- New reports can use `vehicle_allocation` for detailed analysis

### Analytics Queries
```python
# Bookings using optimization
optimized_bookings = Booking.objects.exclude(vehicle_allocation=[])

# Most popular vehicle combinations
from django.db.models import Count
popular_combos = (
    Booking.objects
    .exclude(vehicle_allocation=[])
    .values('vehicle_allocation')
    .annotate(count=Count('id'))
    .order_by('-count')
)
```

## Security Considerations

1. **Server-Side Validation**: All pricing calculated on backend
2. **Active Status Check**: Only active vehicles can be booked
3. **Capacity Validation**: Prevents under-capacity bookings
4. **Price Recalculation**: Client-sent prices ignored
5. **Audit Logging**: All bookings logged with vehicle allocation

## Troubleshooting

### No Solutions Returned
- Check if any vehicles are active
- Verify passenger count > 0
- Check vehicle capacities are configured

### Price Mismatch
- Ensure `base_price_per_day` is set
- Check if pricing rules are active
- Verify date range calculation

### Validation Errors
- Ensure all transport IDs exist
- Check all vehicles are active
- Verify total capacity ≥ passenger count

## Future Enhancements

1. **Luggage Optimization**: Consider luggage capacity in ranking
2. **Route-Based Pricing**: Different prices for different routes
3. **Peak Season Multipliers**: Dynamic pricing based on demand
4. **Vehicle Availability**: Real-time availability checking
5. **Multi-Objective Weights**: Configurable priority weights

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review test cases: `backend/apps/pricing_engine/tests/`
- Contact: Backend team

## Version History

- **v1.0.0** (2024-02-23): Initial implementation
  - Mathematical optimization engine
  - Vehicle suggestions API
  - Pricing service integration
  - Database migrations
  - Comprehensive testing
