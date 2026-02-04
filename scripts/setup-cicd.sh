#!/bin/bash

# Shambit Travels API - CI/CD Setup Script
# This script sets up the complete CI/CD pipeline

set -e

echo "🚀 Setting up CI/CD Pipeline for Shambit Travels API"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on GitHub Actions
if [ "$GITHUB_ACTIONS" = "true" ]; then
    print_status "Running in GitHub Actions environment"
    IS_CI=true
else
    print_status "Running in local environment"
    IS_CI=false
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists git; then
    print_error "Git is not installed"
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi

if ! command_exists docker; then
    print_warning "Docker is not installed - some features will be unavailable"
fi

# Setup Python virtual environment
if [ "$IS_CI" = "false" ]; then
    print_status "Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
print_status "Installing development dependencies..."
pip install \
    black \
    flake8 \
    isort \
    mypy \
    bandit \
    safety \
    coverage \
    pytest \
    pytest-django \
    pytest-cov

# Setup pre-commit hooks
if [ "$IS_CI" = "false" ]; then
    print_status "Setting up pre-commit hooks..."
    pip install pre-commit
    
    # Create pre-commit config
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=127]

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", ".", "-x", "tests/"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
        args: [--ignore-missing-imports]
EOF

    pre-commit install
    print_status "Pre-commit hooks installed"
fi

# Setup environment file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please update .env file with your configuration"
fi

# Run code quality checks
print_status "Running code quality checks..."

# Black formatting check
print_status "Checking code formatting with Black..."
black --check . || {
    print_warning "Code formatting issues found. Run 'black .' to fix them."
}

# Import sorting check
print_status "Checking import sorting with isort..."
isort --check-only . || {
    print_warning "Import sorting issues found. Run 'isort .' to fix them."
}

# Linting with flake8
print_status "Running linting with flake8..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Type checking with mypy
print_status "Running type checking with mypy..."
mypy . --ignore-missing-imports || {
    print_warning "Type checking issues found"
}

# Security scanning with bandit
print_status "Running security scan with bandit..."
bandit -r . -x tests/ || {
    print_warning "Security issues found"
}

# Dependency vulnerability check
print_status "Checking for vulnerable dependencies..."
safety check || {
    print_warning "Vulnerable dependencies found"
}

# Database setup for testing
if [ "$IS_CI" = "false" ]; then
    print_status "Setting up test database..."
    python manage.py migrate --settings=backend.settings.local
fi

# Run tests
print_status "Running tests..."
if [ "$IS_CI" = "true" ]; then
    coverage run --source='.' manage.py test
    coverage report
    coverage xml
else
    python manage.py test --settings=backend.settings.local
fi

# Docker setup
if command_exists docker; then
    print_status "Building Docker image..."
    docker build -t shambit-travels-api:latest .
    
    if [ "$IS_CI" = "false" ]; then
        print_status "Testing Docker container..."
        docker run --rm -d --name test-container -p 8001:8000 shambit-travels-api:latest
        sleep 10
        
        # Test health endpoint
        if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
            print_status "Docker container health check passed"
        else
            print_error "Docker container health check failed"
        fi
        
        docker stop test-container
    fi
fi

# Generate documentation
print_status "Generating API documentation..."
python manage.py spectacular --color --file schema.yml

# Setup monitoring (if not in CI)
if [ "$IS_CI" = "false" ] && command_exists docker-compose; then
    print_status "Setting up monitoring stack..."
    mkdir -p monitoring/grafana/provisioning/{dashboards,datasources}
    
    # Create Grafana datasource configuration
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    print_status "Monitoring configuration created"
fi

# Create deployment checklist
print_status "Creating deployment checklist..."
cat > DEPLOYMENT_CHECKLIST.md << EOF
# Deployment Checklist

## Pre-deployment
- [ ] All tests passing
- [ ] Code quality checks passed
- [ ] Security scan completed
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Static files collected

## Deployment
- [ ] Backup current database
- [ ] Deploy new version
- [ ] Run database migrations
- [ ] Collect static files
- [ ] Restart application services
- [ ] Verify health checks

## Post-deployment
- [ ] Monitor application logs
- [ ] Check error rates
- [ ] Verify key functionality
- [ ] Monitor performance metrics
- [ ] Update documentation

## Rollback Plan
- [ ] Database rollback scripts ready
- [ ] Previous version tagged
- [ ] Rollback procedure documented
EOF

print_status "✅ CI/CD Pipeline setup completed successfully!"

if [ "$IS_CI" = "false" ]; then
    echo ""
    print_status "Next steps:"
    echo "1. Update .env file with your configuration"
    echo "2. Set up your database"
    echo "3. Configure your deployment target"
    echo "4. Set up monitoring and alerting"
    echo "5. Configure backup strategy"
    echo ""
    print_status "To start development server:"
    echo "python manage.py runserver"
    echo ""
    print_status "To start with Docker:"
    echo "docker-compose up -d"
    echo ""
    print_status "To start monitoring:"
    echo "docker-compose -f docker-compose.monitoring.yml up -d"
fi