# Free Experiences Implementation

## Overview
This document describes the implementation of support for free experiences (base_price = ₹0) in the ShamBit platform.

## Business Requirement
Allow experiences to be offered for free by setting the minimum base price to ₹0 instead of ₹100.

## Changes Made

### 1. Model Changes (`apps/packages/models.py`)

**Before:**
```python
base_price = models.DecimalField(
    validators=[
        MinValueValidator(100, message="Base price must be at least ₹100"),
        MaxValueValidator(100000, message="Base price cannot exceed ₹100,000"),
    ],
    help_text="Price in INR (₹100 - ₹100,000)",
)
```

**After:**
```python
base_price = models.DecimalField(
    validators=[
        MinValueValidator(0, message="Base price must be at least ₹0 (free experiences allowed)"),
        MaxValueValidator(100000, message="Base price cannot exceed ₹100,000"),
    ],
    help_text="Price in INR (₹0 - ₹100,000). Set to 0 for free experiences.",
)
```

### 2. Serializer Changes (`apps/packages/serializers.py`)

**Before:**
```python
def validate_base_price(self, value):
    """Validate base price is within acceptable range"""
    if value < 100:
        raise ValidationError("Base price must be at least ₹100")
    if value > 100000:
        raise ValidationError("Base price cannot exceed ₹100,000")
    return value
```

**After:**
```python
def validate_base_price(self, value):
    """Validate base price is within acceptable range"""
    if value < 0:
        raise ValidationError("Base price must be at least ₹0 (free experiences allowed)")
    if value > 100000:
        raise ValidationError("Base price cannot exceed ₹100,000")
    return value
```

### 3. Database Migration

**Migration:** `0012_allow_free_experiences.py`

This migration updates the `base_price` field validator to allow values from ₹0 to ₹100,000.

## Validation Rules

### Accepted Values
- ✅ `0.00` - Free experience
- ✅ `50.00` - Low-cost experience
- ✅ `1000.00` - Mid-range experience
- ✅ `100000.00` - Maximum price

### Rejected Values
- ❌ `-1.00` - Negative prices not allowed
- ❌ `100001.00` - Exceeds maximum price

## Testing

### Manual Testing
```bash
# Test free experience validation
python manage.py shell -c "from packages.models import Experience; from decimal import Decimal; exp = Experience(name='Free Tour', description='A free walking tour' * 5, base_price=Decimal('0.00'), duration_hours=Decimal('2.0')); exp.full_clean(); print('✅ Validation passed!')"

# Test negative price rejection
python manage.py shell -c "from packages.models import Experience; from decimal import Decimal; exp = Experience(name='Invalid', description='Test' * 20, base_price=Decimal('-10.00'), duration_hours=Decimal('2.0')); exp.full_clean()"
```

## Deployment Steps

### 1. Apply Migration
```bash
cd backend
python manage.py migrate packages
```

### 2. Verify Migration
```bash
python manage.py showmigrations packages
```

Expected output should show:
```
[X] 0012_allow_free_experiences
```

### 3. Test in Django Admin
1. Navigate to Django Admin
2. Go to Packages > Experiences
3. Create or edit an experience
4. Set base_price to 0.00
5. Save and verify no validation errors

### 4. Test via API
```bash
# Create a free experience via API
curl -X POST http://localhost:8000/api/experiences/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Free Walking Tour",
    "description": "A complimentary walking tour of the historic city center showcasing major landmarks and local culture.",
    "base_price": "0.00",
    "duration_hours": "2.0",
    "max_participants": 20,
    "difficulty_level": "EASY",
    "category": "CULTURAL"
  }'
```

## Impact Analysis

### Backend Impact
- ✅ Backward compatible - existing experiences with price ≥100 remain valid
- ✅ No breaking changes to API contracts
- ✅ Database migration is safe and reversible
- ✅ All existing pricing calculations handle ₹0 correctly

### Frontend Impact
- ✅ No frontend changes required
- ✅ Frontend already handles various price points
- ✅ Price display logic works with ₹0

### Business Logic Impact
- ✅ Pricing engine handles free experiences correctly
- ✅ Booking calculations work with ₹0 base price
- ✅ Search and filtering work with ₹0 price

## API Documentation

The Swagger/ReDoc documentation will automatically reflect the updated validation rules:

- **Minimum:** ₹0 (was ₹100)
- **Maximum:** ₹100,000 (unchanged)
- **Description:** "Price in INR (₹0 - ₹100,000). Set to 0 for free experiences."

Access documentation at:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Rollback Plan

If needed, rollback can be performed:

```bash
# Rollback migration
python manage.py migrate packages 0011_add_vehicle_optimization_fields

# Revert code changes
git revert <commit-hash>
```

## Quality Assurance Checklist

- [x] Model validator updated
- [x] Serializer validator updated
- [x] Migration created and tested
- [x] Code formatted with black
- [x] Imports sorted with isort
- [x] Flake8 checks passed
- [x] Manual validation testing completed
- [x] Documentation created

## Notes

1. **Free Experiences Use Cases:**
   - Promotional tours
   - Community events
   - Sample experiences
   - Charity events
   - Marketing campaigns

2. **Pricing Engine Compatibility:**
   - The pricing engine correctly handles ₹0 base price
   - Total package price calculation includes free experiences
   - No division by zero or edge case issues

3. **Future Considerations:**
   - Consider adding an `is_free` boolean field for easier filtering
   - Add analytics tracking for free experience bookings
   - Consider separate reporting for free vs paid experiences

## Related Files

- `backend/apps/packages/models.py` - Model definition
- `backend/apps/packages/serializers.py` - API serializer
- `backend/apps/packages/migrations/0012_allow_free_experiences.py` - Migration
- `backend/apps/packages/admin.py` - Django admin configuration

## Support

For questions or issues, contact the development team or refer to:
- API Documentation: `/api/docs/`
- Project README: `backend/README.md`
