import dj_database_url

from .development import *

# Use Neon DB
# postgresql://neondb_owner:npg_VyDnfoCEu46z@ep-solitary-cell-ahfvkw6i-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "neondb",
        "USER": "neondb_owner",
        "PASSWORD": "npg_VyDnfoCEu46z",
        "HOST": "ep-solitary-cell-ahfvkw6i-pooler.c-3.us-east-1.aws.neon.tech",
        "PORT": "5432",
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# Override Cache to use Local Memory instead of Redis for this run
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Disable Celery/Redis dependencies
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "db+sqlite:///results.sqlite"
CELERY_ALWAYS_EAGER = True

# Override logging to fix Windows permission issues with RotatingFileHandler
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
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
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",  # Reduce log level to INFO to reduce noise
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Reduce database query logging
            "propagate": False,
        },
    },
}
