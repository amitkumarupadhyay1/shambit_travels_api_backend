# Python Version Compatibility Guide

This guide explains the Python version requirements and compatibility for the Shambit Travels API Backend.

## Current Configuration

- **Default Python Version**: 3.10+
- **Django Version**: 4.2.16 LTS (Long Term Support)
- **Recommended for Production**: Python 3.10 or 3.11

## Version Compatibility Matrix

| Python Version | Django Version | Status | Notes |
|----------------|----------------|--------|-------|
| 3.8 | 4.2.x | ⚠️ Deprecated | End of life, not recommended |
| 3.9 | 4.2.x | ✅ Supported | Works but consider upgrading |
| 3.10 | 4.2.x, 5.1.x | ✅ Recommended | Best compatibility |
| 3.11 | 4.2.x, 5.1.x | ✅ Recommended | Latest stable features |
| 3.12 | 4.2.x, 5.1.x | ✅ Latest | Cutting edge, test thoroughly |

## Requirements Files

We provide multiple requirements files for different scenarios:

### 1. `requirements.txt` (Default - Django 4.2 LTS)
- **Django**: 4.2.16 LTS
- **Python**: 3.9+ (3.10+ recommended)
- **Use case**: Production deployments, stable environments
- **Benefits**: Long-term support, battle-tested, stable

### 2. `requirements-django5.txt` (Django 5.x)
- **Django**: 5.1.4
- **Python**: 3.10+ (required)
- **Use case**: New projects, latest features
- **Benefits**: Latest Django features, improved performance

### 3. `requirements-stable.txt` (Maximum Compatibility)
- **Django**: 4.2.16 LTS
- **Python**: 3.9+
- **Use case**: Legacy systems, maximum compatibility
- **Benefits**: Works with older Python versions

## Switching Between Versions

### To use Django 5.x (requires Python 3.10+):
```bash
# Backup current requirements
cp requirements.txt requirements-backup.txt

# Switch to Django 5.x
cp requirements-django5.txt requirements.txt

# Reinstall dependencies
pip install -r requirements.txt

# Run migrations (may be needed for Django upgrades)
python manage.py migrate
```

### To use maximum compatibility (Django 4.2 LTS):
```bash
# Switch to stable requirements
cp requirements-stable.txt requirements.txt

# Reinstall dependencies
pip install -r requirements.txt
```

## CI/CD Configuration

The GitHub Actions workflows are configured to use Python 3.10 by default. To change this:

1. Edit `.github/workflows/ci-cd.yml`
2. Change the `PYTHON_VERSION` environment variable
3. Ensure your requirements.txt is compatible with the chosen Python version

```yaml
env:
  PYTHON_VERSION: '3.11'  # Change this to your preferred version
```

## Docker Configuration

The Dockerfile uses Python 3.10 by default. To change:

```dockerfile
# Change this line in Dockerfile
FROM python:3.11-slim  # Use your preferred version
```

## Upgrading Python Version

### Step 1: Check Compatibility
```bash
# Check current Python version
python --version

# Check Django compatibility
python -c "import django; print(django.VERSION)"
```

### Step 2: Update Requirements
Choose the appropriate requirements file based on your target Python version.

### Step 3: Update CI/CD
Update the Python version in all GitHub Actions workflows:
- `.github/workflows/ci-cd.yml`
- `.github/workflows/code-quality.yml`
- `.github/workflows/security.yml`

### Step 4: Update Docker
Update the Python version in:
- `Dockerfile`
- `docker-compose.yml` (if using custom images)

### Step 5: Test Thoroughly
```bash
# Run tests
python manage.py test

# Check for deprecation warnings
python -Wd manage.py test

# Run security checks
bandit -r .
safety check
```

## Troubleshooting

### Django 5.2 Installation Error
**Error**: `ERROR: No matching distribution found for Django==5.2`

**Solution**: Django 5.2 doesn't exist yet. Use Django 5.1.x or 4.2.x LTS.

### Python Version Mismatch
**Error**: `Requires-Python >=3.10`

**Solutions**:
1. Upgrade Python to 3.10+
2. Use `requirements-stable.txt` for older Python versions
3. Use Django 4.2 LTS which supports Python 3.8+

### Package Compatibility Issues
**Error**: Package conflicts during installation

**Solutions**:
1. Create a fresh virtual environment
2. Use the appropriate requirements file for your Python version
3. Check package compatibility on PyPI

## Recommendations

### For New Projects
- **Python**: 3.11 or 3.12
- **Django**: 5.1.x (latest stable)
- **Requirements**: `requirements-django5.txt`

### For Production Systems
- **Python**: 3.10 or 3.11
- **Django**: 4.2.x LTS
- **Requirements**: `requirements.txt` (default)

### For Legacy Systems
- **Python**: 3.9+
- **Django**: 4.2.x LTS
- **Requirements**: `requirements-stable.txt`

## Support Timeline

| Version | Support Until | Recommendation |
|---------|---------------|----------------|
| Python 3.8 | October 2024 | ❌ Upgrade immediately |
| Python 3.9 | October 2025 | ⚠️ Plan upgrade |
| Python 3.10 | October 2026 | ✅ Recommended |
| Python 3.11 | October 2027 | ✅ Recommended |
| Python 3.12 | October 2028 | ✅ Future-proof |

| Django Version | Support Until | Recommendation |
|----------------|---------------|----------------|
| Django 4.2 LTS | April 2026 | ✅ Recommended for production |
| Django 5.0 | August 2024 | ❌ Upgrade to 5.1 |
| Django 5.1 | December 2024 | ✅ Good for new projects |

## Getting Help

If you encounter issues with Python version compatibility:

1. Check this guide first
2. Review the error messages carefully
3. Ensure you're using the correct requirements file
4. Create an issue on GitHub with:
   - Your Python version (`python --version`)
   - Your operating system
   - The complete error message
   - Steps to reproduce the issue