# Shambit Travels API Backend

A comprehensive Django REST API backend for a travel booking platform with advanced features including pricing engine, notifications, media library, and SEO optimization.

## Features

- **User Management**: Custom user authentication with OAuth support
- **Booking System**: Complete booking management with services
- **Pricing Engine**: Dynamic pricing with configurable rules
- **Payment Processing**: Integrated payment handling
- **Notification System**: Multi-channel notifications with templates
- **Media Library**: File management with cleanup utilities
- **SEO Optimization**: Automated SEO content generation
- **City & Package Management**: Travel destinations and packages
- **Article System**: Content management for travel articles

## Tech Stack

- **Framework**: Django 4.x with Django REST Framework
- **Database**: PostgreSQL (configurable)
- **Authentication**: JWT with OAuth support
- **Documentation**: Swagger/OpenAPI
- **File Storage**: Django file handling with media management
- **Caching**: Redis support
- **Task Queue**: Celery support

## Project Structure

```
├── apps/                    # Django applications
│   ├── articles/           # Article management
│   ├── bookings/           # Booking system
│   ├── cities/             # City management
│   ├── media_library/      # File management
│   ├── notifications/      # Notification system
│   ├── packages/           # Travel packages
│   ├── payments/           # Payment processing
│   ├── pricing_engine/     # Dynamic pricing
│   ├── seo/               # SEO optimization
│   └── users/             # User management
├── backend/               # Django settings
├── docs/                  # Documentation
├── tests/                 # Test files
└── requirements.txt       # Dependencies
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite for development)
- Redis (optional, for caching)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/amitkumarupadhyay1/shambit_travels_api_backend.git
cd shambit_travels_api_backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Environment setup:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Database setup:
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Run development server:
```bash
python manage.py runserver
```

## API Documentation

- **Swagger UI**: `/swagger/`
- **ReDoc**: `/redoc/`
- **OpenAPI Schema**: `/schema/`

## Environment Variables

Key environment variables (see `.env.example`):

- `DEBUG`: Development mode
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database connection
- `REDIS_URL`: Redis connection
- `EMAIL_*`: Email configuration
- `OAUTH_*`: OAuth provider settings

## Development

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
# Linting
flake8 .

# Formatting
black .

# Type checking
mypy .
```

### Management Commands

- `python manage.py cleanup_media`: Clean unused media files
- `python manage.py cleanup_notifications`: Clean old notifications
- `python manage.py generate_seo`: Generate SEO content
- `python manage.py send_notification`: Send notifications

## Deployment

### Docker (Recommended)

```bash
docker build -t shambit-travels-api .
docker run -p 8000:8000 shambit-travels-api
```

### Manual Deployment

1. Set production environment variables
2. Collect static files: `python manage.py collectstatic`
3. Run migrations: `python manage.py migrate`
4. Use a WSGI server like Gunicorn

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Token refresh

### Bookings
- `GET /api/bookings/` - List bookings
- `POST /api/bookings/` - Create booking
- `GET /api/bookings/{id}/` - Get booking details

### Packages
- `GET /api/packages/` - List travel packages
- `GET /api/packages/{id}/` - Package details

### Cities
- `GET /api/cities/` - List cities
- `GET /api/cities/{id}/` - City details

### Pricing
- `POST /api/pricing/calculate/` - Calculate pricing
- `GET /api/pricing/rules/` - List pricing rules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@shambittravels.com or create an issue on GitHub.