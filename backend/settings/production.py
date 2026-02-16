from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Railway specific settings
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Add Railway health check and internal domains
ALLOWED_HOSTS.extend(
    [
        "healthcheck.railway.app",
        "*.railway.app",
        "*.up.railway.app",
    ]
)

if "RAILWAY_STATIC_URL" in os.environ:
    ALLOWED_HOSTS.append(
        os.environ["RAILWAY_STATIC_URL"].replace("https://", "").replace("http://", "")
    )

# Add Railway public domain if available
if "RAILWAY_PUBLIC_DOMAIN" in os.environ:
    ALLOWED_HOSTS.append(os.environ["RAILWAY_PUBLIC_DOMAIN"])

# Use PORT from Railway
PORT = os.environ.get("PORT", "8000")

# Database settings for production - Railway PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Manual parsing for maximum reliability
    # Format: postgresql://user:password@host:port/dbname?options
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)

    # Extract SSL mode from query string
    ssl_mode = "require" if "sslmode=require" in DATABASE_URL else "prefer"

    # Construct DATABASES directly - no external library dependencies
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path[1:],  # Remove leading slash
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": parsed.port or 5432,
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "sslmode": ssl_mode,
            },
        }
    }
else:
    raise ValueError("DATABASE_URL environment variable is required in production")

# Fast2SMS settings for SMS OTP
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "")

# Email settings for production
# Use console backend if SMTP is not available (Railway network restrictions)
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", 30))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@travelplatform.com")

# CORS settings for production - Railway
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    # Add your Railway frontend domain here - UPDATE THIS
    "https://shambit-frontend.up.railway.app",
    "https://shambittravels.up.railway.app",
]

# Add Railway domain when available
if "RAILWAY_STATIC_URL" in os.environ:
    railway_url = os.environ["RAILWAY_STATIC_URL"]
    if not railway_url.startswith(("http://", "https://")):
        railway_url = f"https://{railway_url}"
    CORS_ALLOWED_ORIGINS.append(railway_url)

# Add Railway public URL if available
if "RAILWAY_PUBLIC_DOMAIN" in os.environ:
    public_domain = os.environ["RAILWAY_PUBLIC_DOMAIN"]
    if not public_domain.startswith(("http://", "https://")):
        public_domain = f"https://{public_domain}"
    CORS_ALLOWED_ORIGINS.append(public_domain)

CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False") == "True"

# Allow custom headers for production
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

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://shambit-frontend.up.railway.app",
    "https://shambittravels.up.railway.app",
    "https://shambit.up.railway.app",
]

# Add Railway domains to CSRF trusted origins
if "RAILWAY_STATIC_URL" in os.environ:
    railway_url = os.environ["RAILWAY_STATIC_URL"]
    if not railway_url.startswith(("http://", "https://")):
        railway_url = f"https://{railway_url}"
    CSRF_TRUSTED_ORIGINS.append(railway_url)

if "RAILWAY_PUBLIC_DOMAIN" in os.environ:
    public_domain = os.environ["RAILWAY_PUBLIC_DOMAIN"]
    if not public_domain.startswith(("http://", "https://")):
        public_domain = f"https://{public_domain}"
    CSRF_TRUSTED_ORIGINS.append(public_domain)

# Security settings for production - Railway
# Disable SSL redirect for health checks
SECURE_SSL_REDIRECT = False  # Railway handles SSL termination
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "True") == "True"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "True") == "True"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Static files for Railway
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Ensure static directory exists
STATICFILES_DIRS = []
static_dir = BASE_DIR / "static"
if static_dir.exists():
    STATICFILES_DIRS = [static_dir]

# Media files configuration - Cloudinary or Railway Volume
MEDIA_URL = "/media/"

# Check if Cloudinary should be used (from base.py)
if os.environ.get("USE_CLOUDINARY") == "True":
    # Use Cloudinary storage (configured in base.py)
    # STORAGES is already set in base.py with MediaCloudinaryStorage
    print("✅ Using Cloudinary for media storage in production")
    pass  # Keep the STORAGES from base.py
else:
    # Fallback to Railway Volume or local storage
    if "RAILWAY_VOLUME_MOUNT_PATH" in os.environ:
        # Railway Hobby plan volume is mounted
        volume_path = os.environ["RAILWAY_VOLUME_MOUNT_PATH"]
        MEDIA_ROOT = os.path.join(volume_path, "media")

        # Create media directory if it doesn't exist
        os.makedirs(MEDIA_ROOT, mode=0o755, exist_ok=True)
        print(f"⚠️  Using Railway Volume for media storage: {MEDIA_ROOT}")
    else:
        # Local development
        MEDIA_ROOT = BASE_DIR / "media"
        print(f"⚠️  Using local filesystem for media storage: {MEDIA_ROOT}")

    # Override STORAGES to use FileSystemStorage
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": MEDIA_ROOT},
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# Logging settings for production
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
            "filename": BASE_DIR / "logs" / "django_prod.log",
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

# Django Admin settings for production
ADMIN_URL = "admin/"
