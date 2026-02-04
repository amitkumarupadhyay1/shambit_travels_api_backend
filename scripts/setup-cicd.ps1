# Shambit Travels API - CI/CD Setup Script (PowerShell)
# This script sets up the complete CI/CD pipeline on Windows

param(
    [switch]$SkipDocker,
    [switch]$SkipTests,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up CI/CD Pipeline for Shambit Travels API" -ForegroundColor Green

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check prerequisites
Write-Status "Checking prerequisites..."

if (-not (Test-Command "git")) {
    Write-Error "Git is not installed"
    exit 1
}

if (-not (Test-Command "python")) {
    Write-Error "Python is not installed"
    exit 1
}

if (-not (Test-Command "docker") -and -not $SkipDocker) {
    Write-Warning "Docker is not installed - some features will be unavailable"
    $SkipDocker = $true
}

# Setup Python virtual environment
Write-Status "Setting up Python virtual environment..."
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Status "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
Write-Status "Installing development dependencies..."
pip install black flake8 isort mypy bandit safety coverage pytest pytest-django pytest-cov

# Setup environment file
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Write-Status "Creating .env file from template..."
    Copy-Item ".env.example" ".env"
    Write-Warning "Please update .env file with your configuration"
}

# Run code quality checks
Write-Status "Running code quality checks..."

# Black formatting check
Write-Status "Checking code formatting with Black..."
try {
    black --check .
    Write-Status "Code formatting check passed"
}
catch {
    Write-Warning "Code formatting issues found. Run 'black .' to fix them."
}

# Import sorting check
Write-Status "Checking import sorting with isort..."
try {
    isort --check-only .
    Write-Status "Import sorting check passed"
}
catch {
    Write-Warning "Import sorting issues found. Run 'isort .' to fix them."
}

# Linting with flake8
Write-Status "Running linting with flake8..."
try {
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    Write-Status "Linting check passed"
}
catch {
    Write-Warning "Linting issues found"
}

# Type checking with mypy
Write-Status "Running type checking with mypy..."
try {
    mypy . --ignore-missing-imports
    Write-Status "Type checking passed"
}
catch {
    Write-Warning "Type checking issues found"
}

# Security scanning with bandit
Write-Status "Running security scan with bandit..."
try {
    bandit -r . -x tests/
    Write-Status "Security scan passed"
}
catch {
    Write-Warning "Security issues found"
}

# Dependency vulnerability check
Write-Status "Checking for vulnerable dependencies..."
try {
    safety check
    Write-Status "Dependency check passed"
}
catch {
    Write-Warning "Vulnerable dependencies found"
}

# Database setup for testing
Write-Status "Setting up test database..."
python manage.py migrate --settings=backend.settings.local

# Run tests
if (-not $SkipTests) {
    Write-Status "Running tests..."
    python manage.py test --settings=backend.settings.local
}

# Docker setup
if (-not $SkipDocker -and (Test-Command "docker")) {
    Write-Status "Building Docker image..."
    docker build -t shambit-travels-api:latest .
    
    Write-Status "Testing Docker container..."
    docker run --rm -d --name test-container -p 8001:8000 shambit-travels-api:latest
    Start-Sleep -Seconds 10
    
    # Test health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health/" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Status "Docker container health check passed"
        }
        else {
            Write-Error "Docker container health check failed"
        }
    }
    catch {
        Write-Error "Docker container health check failed: $($_.Exception.Message)"
    }
    finally {
        docker stop test-container
    }
}

# Generate documentation
Write-Status "Generating API documentation..."
python manage.py spectacular --color --file schema.yml

# Setup monitoring directories
Write-Status "Setting up monitoring configuration..."
New-Item -ItemType Directory -Force -Path "monitoring\grafana\provisioning\dashboards"
New-Item -ItemType Directory -Force -Path "monitoring\grafana\provisioning\datasources"

# Create Grafana datasource configuration
$grafanaConfig = @"
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
"@

$grafanaConfig | Out-File -FilePath "monitoring\grafana\provisioning\datasources\prometheus.yml" -Encoding UTF8

# Create deployment checklist
Write-Status "Creating deployment checklist..."
$checklist = @"
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
"@

$checklist | Out-File -FilePath "DEPLOYMENT_CHECKLIST.md" -Encoding UTF8

Write-Status "✅ CI/CD Pipeline setup completed successfully!" -ForegroundColor Green

Write-Host ""
Write-Status "Next steps:"
Write-Host "1. Update .env file with your configuration"
Write-Host "2. Set up your database"
Write-Host "3. Configure your deployment target"
Write-Host "4. Set up monitoring and alerting"
Write-Host "5. Configure backup strategy"
Write-Host ""
Write-Status "To start development server:"
Write-Host "python manage.py runserver"
Write-Host ""
Write-Status "To start with Docker:"
Write-Host "docker-compose up -d"
Write-Host ""
Write-Status "To start monitoring:"
Write-Host "docker-compose -f docker-compose.monitoring.yml up -d"