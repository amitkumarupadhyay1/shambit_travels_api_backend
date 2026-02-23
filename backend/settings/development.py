import dj_database_url

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database settings for development
# Use DATABASE_URL if provided, otherwise fall back to individual settings
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "travel_platform_dev"),
            "USER": os.environ.get("DB_USER", "travel_user_dev"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "travel_password_dev"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 600,
            "OPTIONS": {
                "sslmode": "require",
                "connect_timeout": 10,
            },
        }
    }

# Email settings for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:7173",
    "http://192.168.29.45:3000",
    "http://192.168.29.45:5173",
    "http://192.168.29.45:7173",
    "http://192.168.29.45:8000",
    "http://192.168.3.103:3000",
]

# Allow all origins from local network for development (192.168.x.x)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://192\.168\.\d+\.\d+:\d+$",  # Allow any 192.168.x.x:port
    r"^http://localhost:\d+$",  # Allow any localhost:port
    r"^http://127\.0\.0\.1:\d+$",  # Allow any 127.0.0.1:port
]

# Allow custom headers for development (inherits from base.py but can be overridden)
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

# Django Debug Toolbar settings
# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

# INSTALLED_APPS += [
#     'debug_toolbar',
# ]

# Django Silk settings
# MIDDLEWARE += [
#     'silk.middleware.SilkyMiddleware',
# ]

# INSTALLED_APPS += [
#     'silk',
# ]

# Django Extensions settings
# INSTALLED_APPS += [
#     'django_extensions',
# ]

# Django Axes settings for development
AXES_ENABLED = False

# Django Ratelimit settings for development
RATELIMIT_ENABLE = False

# Django Admin Interface settings
ADMIN_INTERFACE = {
    "SKIN": "black",
    "SHOW_THEMES": True,
    "DEFAULT_THEME": "black",
}

# Logging settings for development
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
            "filename": BASE_DIR / "logs" / "django_dev.log",
            "maxBytes": 1024 * 1024 * 5,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Security settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"  # Ensure proper CSRF cookie handling
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access for API calls

# Django Admin settings
ADMIN_URL = "admin/"

# ─────────────────────────────────────────────────────────────────────────────
# Celery Configuration (PHASE 4: Draft Persistence)
# ─────────────────────────────────────────────────────────────────────────────

# Celery broker settings
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Celery task settings
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Celery Beat Schedule (Periodic Tasks)
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "expire-draft-bookings": {
        "task": "apps.bookings.tasks.expire_draft_bookings",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "options": {"expires": 240},  # Task expires after 4 minutes
    },
    "cleanup-expired-drafts": {
        "task": "apps.bookings.tasks.cleanup_expired_drafts",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"expires": 3300},  # Task expires after 55 minutes
    },
}
