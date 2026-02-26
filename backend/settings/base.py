import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "apps"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-*=+@8#5^v9z7k3m2n1p0q")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,192.168.29.45,0.0.0.0"
).split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # Required for PostgreSQL full-text search
    # Cloudinary must be before django.contrib.staticfiles
    "cloudinary_storage",
    "cloudinary",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "users",
    "cities",
    "articles",
    "media_library",
    "packages",
    "pricing_engine",
    "bookings",
    "payments",
    "notifications",
    "seo",
    "search",  # Universal search app
    "apps.travelers",  # Traveler management
    "inquiries",  # Customer inquiries/contact form
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database configuration - MUST be set in environment-specific settings
# Do NOT set a default here as it causes Django to initialize connections prematurely
# DATABASES will be configured in production.py, development.py, or local.py

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only add static directory if it exists
STATICFILES_DIRS = []
static_dir = BASE_DIR / "static"
if static_dir.exists():
    STATICFILES_DIRS = [static_dir]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

# Django REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Changed from IsAuthenticated to AllowAny
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "City Travel Platform API",
    "DESCRIPTION": "API documentation for City-Based Travel Platform with booking, payment, and content management capabilities",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "defaultModelRendering": "example",
        "displayRequestDuration": True,
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
    "SECURITY": [
        {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
        },
    ],
    "AUTHENTICATION_WHITELIST": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "TAGS": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization",
        },
        {"name": "Cities", "description": "City information and context"},
        {"name": "Articles", "description": "Travel articles and content"},
        {"name": "Packages", "description": "Travel packages and components"},
        {"name": "Bookings", "description": "Booking management"},
        {"name": "Payments", "description": "Payment processing"},
        {"name": "Notifications", "description": "User notifications"},
        {"name": "SEO", "description": "SEO metadata management"},
        {"name": "Media", "description": "Media library management"},
        {"name": "Pricing", "description": "Dynamic pricing engine"},
        {"name": "Search", "description": "Universal search across all content"},
    ],
}

# JWT settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:7173",
    "http://192.168.29.45:3000",
    "http://192.168.29.45:5173",
    "http://192.168.29.45:7173",
    "https://yourdomain.com",
]

# Allow all origins from local network for development
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://192\.168\.\d{1,3}\.\d{1,3}:\d+$",  # Local network IPs
]

CORS_ALLOW_CREDENTIALS = True

# Allow custom headers for idempotency and other features
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "idempotency-key",  # Custom header for idempotent booking requests
]

# CSRF trusted origins for mobile and local network access
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:7173",
    "http://localhost:8000",  # Django admin
    "http://127.0.0.1:8000",  # Django admin alternative
    "http://192.168.29.45:3000",
    "http://192.168.29.45:5173",
    "http://192.168.29.45:7173",
    "http://192.168.29.45:8000",  # Django admin on network
]

# CSRF Cookie Configuration
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_COOKIE_DOMAIN = None  # Allow all domains in development
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SAMESITE = "Lax"  # Allow same-site requests (required for admin)
CSRF_COOKIE_HTTPONLY = False  # Must be False for JavaScript access
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_TRUSTED_ORIGINS_REGEX = []

# Rate limiting settings
RATELIMIT_ENABLE = True
RATELIMIT_DEFAULT = "100/hour;2000/day"

# Stricter limits for auth endpoints
RATELIMIT_AUTH_LOGIN = "5/minute;50/hour"
RATELIMIT_AUTH_SYNC = "10/minute;100/hour"
RATELIMIT_PASSWORD_RESET = "3/minute;20/hour"

# Axes settings
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_TEMPLATE = "locked_out.html"

# Cache settings - Redis for production, local memory for development
CACHES = {
    "default": {
        "BACKEND": os.environ.get(
            "CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"
        ),
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "IGNORE_EXCEPTIONS": True,  # Don't fail if Redis is down
        },
        "KEY_PREFIX": "shambit",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Cache time settings (in seconds)
CACHE_TTL = {
    "experiences_list": 300,  # 5 minutes
    "package_detail": 600,  # 10 minutes
    "package_list": 300,  # 5 minutes
    "city_list": 3600,  # 1 hour
    "price_range": 600,  # 10 minutes
}

# Celery settings - disabled for development
# CELERY_BROKER_URL = 'redis://localhost:6379/1'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_BEAT_SCHEDULE = {
#     'cleanup-old-sessions': {
#         'task': 'django.contrib.sessions.backends.db.cleanup',
#         'schedule': crontab(hour=0, minute=0),
#     },
# }

# Logging settings
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 5,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# Security settings
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False") == "True"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False") == "True"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Fast2SMS settings for SMS OTP
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "")

# Email settings
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@travelplatform.com")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "support@shambit.com")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://shambittravels.up.railway.app")

# Admin interface settings
ADMIN_INTERFACE = {
    "SKIN": "black",
    "SHOW_THEMES": True,
    "DEFAULT_THEME": "black",
}

# Razorpay settings
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_placeholder")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "placeholder_secret")
RAZORPAY_WEBHOOK_SECRET = os.environ.get(
    "RAZORPAY_WEBHOOK_SECRET", "placeholder_webhook_secret"
)

# Debug toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "192.168.29.45",
    "192.168.29.1",  # Gateway
]

# Import storage configuration (Cloudinary)
# This must be imported after INSTALLED_APPS and other base settings
try:
    from .storage import *  # noqa
except ImportError:
    pass  # Storage configuration is optional

# Force Cloudinary storage if enabled (MUST be after storage.py import)
# This ensures Cloudinary is actually used instead of FileSystemStorage
if os.environ.get("USE_CLOUDINARY") == "True":
    # Use STORAGES for Django 4.2+ (DEFAULT_FILE_STORAGE is deprecated)
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# ============================================================
# Push Notifications Configuration (Web Push API)
# ============================================================
# VAPID keys for Web Push Notifications
# Generated using: python generate_vapid_keys.py
# Keep VAPID_PRIVATE_KEY secret - never commit to git

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY") or (
    "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEvcq8j0G4OF0RZ6omO7KDhcugqviB\n"
    "omutTRJI8Hs09yke6OTHSB46yKzqxpAylMpEh6CTqUtmfyhglVwNr5VI9g==\n"
    "-----END PUBLIC KEY-----"
)

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY") or (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgrd0ri3wGz2l2z+rh\n"
    "tQZQUomDm2wPnVFzICYKLabNTzihRANCAAS9yryPQbg4XRFnqiY7soOFy6Cq+IGi\n"
    "a61NEkjwezT3KR7o5MdIHjrIrOrGkDKUykSHoJOpS2Z/KGCVXA2vlUj2\n"
    "-----END PRIVATE KEY-----"
)

VAPID_CLAIMS = {"sub": os.environ.get("VAPID_ADMIN_EMAIL", "mailto:admin@shambit.com")}

# Push notification settings
PUSH_NOTIFICATION_SETTINGS = {
    "MAX_FAILURES_BEFORE_DEACTIVATE": 3,  # Deactivate subscription after 3 failed attempts
    "NOTIFICATION_TTL": 86400,  # Time to live: 24 hours
    "NOTIFICATION_URGENCY": "normal",  # Options: very-low, low, normal, high
}
