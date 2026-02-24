# Verification script for free experiences implementation

Write-Host "🔍 Verifying Free Experiences Implementation" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Check if migration exists
Write-Host ""
Write-Host "1. Checking migration file..." -ForegroundColor Yellow
if (Test-Path "apps/packages/migrations/0012_allow_free_experiences.py") {
    Write-Host "   ✅ Migration file exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ Migration file not found" -ForegroundColor Red
    exit 1
}

# Check migration status
Write-Host ""
Write-Host "2. Checking migration status..." -ForegroundColor Yellow
python manage.py showmigrations packages | Select-String "0012_allow_free_experiences"

# Run Django system check
Write-Host ""
Write-Host "3. Running Django system check..." -ForegroundColor Yellow
python manage.py check
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ System check passed" -ForegroundColor Green
} else {
    Write-Host "   ❌ System check failed" -ForegroundColor Red
    exit 1
}

# Test free experience validation
Write-Host ""
Write-Host "4. Testing free experience validation..." -ForegroundColor Yellow
$result = python manage.py shell -c "from packages.models import Experience; from decimal import Decimal; exp = Experience(name='Free Test Tour', description='A free walking tour for testing purposes. ' * 5, base_price=Decimal('0.00'), duration_hours=Decimal('2.0'), max_participants=20, difficulty_level='EASY', category='CULTURAL'); exp.full_clean(); print('   ✅ Free experience validation passed')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host $result -ForegroundColor Green
} else {
    Write-Host "   ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# Test negative price rejection
Write-Host ""
Write-Host "5. Testing negative price rejection..." -ForegroundColor Yellow
$result = python manage.py shell -c "from packages.models import Experience; from decimal import Decimal; exp = Experience(name='Invalid', description='Test' * 20, base_price=Decimal('-10.00'), duration_hours=Decimal('2.0')); exp.full_clean()" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ✅ Negative price correctly rejected" -ForegroundColor Green
} else {
    Write-Host "   ❌ Negative price should have been rejected" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "✅ All verification checks passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Apply migration: python manage.py migrate packages"
Write-Host "  2. Test in Django Admin"
Write-Host "  3. Test via API"
Write-Host "  4. Deploy to staging"
