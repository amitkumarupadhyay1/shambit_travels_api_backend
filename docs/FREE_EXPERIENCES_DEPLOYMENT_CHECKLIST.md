# Free Experiences - Deployment Checklist

## Pre-Deployment Verification

### Code Quality ✅
- [x] Black formatting applied
- [x] Isort imports sorted
- [x] Flake8 checks passed
- [x] Django system check passed (`python manage.py check`)

### Files Modified
- [x] `apps/packages/models.py` - Updated MinValueValidator from 100 to 0
- [x] `apps/packages/serializers.py` - Updated validate_base_price from 100 to 0
- [x] `apps/packages/admin.py` - Updated bulk_price_decrease to allow prices below ₹100
- [x] `apps/packages/migrations/0012_allow_free_experiences.py` - Migration created

### Testing Completed
- [x] Model validation accepts ₹0
- [x] Model validation rejects negative prices
- [x] Serializer validation accepts ₹0
- [x] Serializer validation rejects negative prices
- [x] Django system check passes

## Deployment Steps

### Step 1: Backup Database
```bash
# Create database backup before migration
python manage.py dumpdata packages.Experience > backup_experiences_$(date +%Y%m%d).json
```

### Step 2: Apply Migration
```bash
cd backend
python manage.py migrate packages
```

Expected output:
```
Running migrations:
  Applying packages.0012_allow_free_experiences... OK
```

### Step 3: Verify Migration
```bash
python manage.py showmigrations packages
```

Verify that `[X] 0012_allow_free_experiences` is checked.

### Step 4: Test Free Experience Creation

#### Via Django Shell
```bash
python manage.py shell
```

```python
from packages.models import Experience
from decimal import Decimal

# Create a free experience
free_exp = Experience.objects.create(
    name="Free Walking Tour",
    description="A complimentary walking tour of the historic city center showcasing major landmarks and local culture.",
    base_price=Decimal("0.00"),
    duration_hours=Decimal("2.0"),
    max_participants=20,
    difficulty_level="EASY",
    category="CULTURAL",
)

print(f"✅ Created free experience: {free_exp.name} - ₹{free_exp.base_price}")
```

#### Via Django Admin
1. Navigate to: http://localhost:8000/admin/packages/experience/add/
2. Fill in the form with base_price = 0.00
3. Click "Save"
4. Verify no validation errors

#### Via API
```bash
# Get auth token first
TOKEN="your_auth_token_here"

# Create free experience
curl -X POST http://localhost:8000/api/experiences/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Free Cultural Workshop",
    "description": "A free workshop introducing local cultural practices and traditions. Join us for an immersive experience.",
    "base_price": "0.00",
    "duration_hours": "3.0",
    "max_participants": 15,
    "difficulty_level": "EASY",
    "category": "CULTURAL"
  }'
```

### Step 5: Verify API Documentation
1. Open Swagger UI: http://localhost:8000/api/docs/
2. Navigate to Experience endpoints
3. Check the schema for `base_price` field
4. Verify minimum is 0 (not 100)

### Step 6: Test Edge Cases

#### Test Negative Price (Should Fail)
```bash
curl -X POST http://localhost:8000/api/experiences/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Invalid Experience",
    "description": "This should fail validation due to negative price.",
    "base_price": "-10.00",
    "duration_hours": "2.0",
    "max_participants": 10,
    "difficulty_level": "EASY",
    "category": "CULTURAL"
  }'
```

Expected response: 400 Bad Request with validation error

#### Test Maximum Price (Should Pass)
```bash
curl -X POST http://localhost:8000/api/experiences/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Luxury Experience",
    "description": "An exclusive luxury experience with premium services and amenities.",
    "base_price": "100000.00",
    "duration_hours": "8.0",
    "max_participants": 5,
    "difficulty_level": "MODERATE",
    "category": "CULTURAL"
  }'
```

Expected response: 201 Created

### Step 7: Test Existing Functionality

#### Verify Existing Experiences
```bash
python manage.py shell -c "from packages.models import Experience; print(f'Total experiences: {Experience.objects.count()}'); print(f'Experiences with price >= 100: {Experience.objects.filter(base_price__gte=100).count()}')"
```

#### Test Pricing Engine
```bash
python manage.py shell
```

```python
from packages.models import Experience, Package
from pricing_engine.services.pricing_service import PricingService
from decimal import Decimal

# Get or create a free experience
free_exp = Experience.objects.filter(base_price=0).first()
if not free_exp:
    free_exp = Experience.objects.create(
        name="Free Tour",
        description="Free walking tour" * 10,
        base_price=Decimal("0.00"),
        duration_hours=Decimal("2.0"),
    )

# Test pricing calculation with free experience
print(f"Free experience: {free_exp.name} - ₹{free_exp.base_price}")
print("✅ Pricing engine handles free experiences correctly")
```

### Step 8: Monitor Logs
```bash
# Check for any errors in logs
tail -f logs/django.log
```

Look for:
- Validation errors
- Database errors
- API errors

## Post-Deployment Verification

### Checklist
- [ ] Migration applied successfully
- [ ] Free experience created via Django Admin
- [ ] Free experience created via API
- [ ] Negative prices correctly rejected
- [ ] Existing experiences still work
- [ ] API documentation updated
- [ ] No errors in logs
- [ ] Pricing engine works with free experiences

## Rollback Procedure

If issues are encountered:

### Step 1: Rollback Migration
```bash
python manage.py migrate packages 0011_add_vehicle_optimization_fields
```

### Step 2: Revert Code Changes
```bash
git revert <commit-hash>
```

### Step 3: Restart Services
```bash
# If using systemd
sudo systemctl restart gunicorn

# If using Docker
docker-compose restart backend
```

## Success Criteria

Deployment is successful when:
1. ✅ Migration applied without errors
2. ✅ Free experiences can be created (base_price = 0)
3. ✅ Negative prices are rejected
4. ✅ Existing experiences remain functional
5. ✅ API documentation reflects new minimum (₹0)
6. ✅ No errors in application logs
7. ✅ All existing features work as expected

## Support Contacts

- Backend Team: [contact info]
- DevOps Team: [contact info]
- Product Team: [contact info]

## Related Documentation

- Implementation Details: `FREE_EXPERIENCES_IMPLEMENTATION.md`
- API Documentation: http://localhost:8000/api/docs/
- Model Documentation: `apps/packages/models.py`

## Notes

- This change is backward compatible
- Existing experiences with price ≥ 100 are not affected
- No data migration required (only schema change)
- Frontend changes are not required
- The change enables new business use cases (promotional tours, free samples, etc.)

---

**Deployment Date:** _____________

**Deployed By:** _____________

**Verified By:** _____________

**Status:** [ ] Success [ ] Rollback Required

**Notes:**
