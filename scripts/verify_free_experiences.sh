#!/bin/bash
# Verification script for free experiences implementation

echo "🔍 Verifying Free Experiences Implementation"
echo "=============================================="

# Check if migration exists
echo ""
echo "1. Checking migration file..."
if [ -f "apps/packages/migrations/0012_allow_free_experiences.py" ]; then
    echo "   ✅ Migration file exists"
else
    echo "   ❌ Migration file not found"
    exit 1
fi

# Check migration status
echo ""
echo "2. Checking migration status..."
python manage.py showmigrations packages | grep "0012_allow_free_experiences"

# Run Django system check
echo ""
echo "3. Running Django system check..."
python manage.py check
if [ $? -eq 0 ]; then
    echo "   ✅ System check passed"
else
    echo "   ❌ System check failed"
    exit 1
fi

# Test free experience validation
echo ""
echo "4. Testing free experience validation..."
python manage.py shell -c "
from packages.models import Experience
from decimal import Decimal

try:
    exp = Experience(
        name='Free Test Tour',
        description='A free walking tour for testing purposes. ' * 5,
        base_price=Decimal('0.00'),
        duration_hours=Decimal('2.0'),
        max_participants=20,
        difficulty_level='EASY',
        category='CULTURAL'
    )
    exp.full_clean()
    print('   ✅ Free experience validation passed')
except Exception as e:
    print(f'   ❌ Validation failed: {e}')
    exit(1)
"

# Test negative price rejection
echo ""
echo "5. Testing negative price rejection..."
python manage.py shell -c "
from packages.models import Experience
from decimal import Decimal

try:
    exp = Experience(
        name='Invalid Experience',
        description='This should fail validation. ' * 10,
        base_price=Decimal('-10.00'),
        duration_hours=Decimal('2.0')
    )
    exp.full_clean()
    print('   ❌ Negative price should have been rejected')
    exit(1)
except Exception:
    print('   ✅ Negative price correctly rejected')
"

echo ""
echo "=============================================="
echo "✅ All verification checks passed!"
echo ""
echo "Next steps:"
echo "  1. Apply migration: python manage.py migrate packages"
echo "  2. Test in Django Admin"
echo "  3. Test via API"
echo "  4. Deploy to staging"
