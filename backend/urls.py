import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import include, path
from django.views.static import serve

from .swagger_views import (
    SecureSpectacularAPIView,
    SecureSpectacularRedocView,
    SecureSpectacularSwaggerView,
)


def serve_media(request, path):
    """
    Custom media serving view that handles multiple storage locations
    with proper CORS headers for Next.js Image Optimization
    """
    # Handle OPTIONS preflight request
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response["Access-Control-Allow-Headers"] = "*"
        response["Access-Control-Max-Age"] = "86400"
        return response

    # Try primary media location first
    primary_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(primary_path):
        response = serve(request, path, document_root=settings.MEDIA_ROOT)
        # Add CORS headers for Next.js Image Optimization
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response["Access-Control-Allow-Headers"] = "*"
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    # Try fallback location
    fallback_root = "/tmp/media"
    fallback_path = os.path.join(fallback_root, path)
    if os.path.exists(fallback_path):
        response = serve(request, path, document_root=fallback_root)
        # Add CORS headers for Next.js Image Optimization
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response["Access-Control-Allow-Headers"] = "*"
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    # File not found in either location
    raise Http404("Media file not found")


def health_check(request):
    """Health check endpoint for monitoring and load balancers"""
    import time

    start_time = time.time()

    try:
        # Try database connection but don't fail if it's not available
        db_status = "unknown"
        db_response_time = None
        try:
            from django.db import connection

            db_start = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_response_time = round((time.time() - db_start) * 1000, 2)  # ms
            db_status = "connected"
        except Exception as e:
            db_status = f"disconnected: {str(e)}"

        response_time = round((time.time() - start_time) * 1000, 2)  # ms

        return JsonResponse(
            {
                "status": "healthy",
                "service": "shambit-travels-api",
                "version": "1.0.0",
                "timestamp": time.time(),
                "database": {
                    "status": db_status,
                    "response_time_ms": db_response_time,
                },
                "response_time_ms": response_time,
            }
        )
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000, 2)
        return JsonResponse(
            {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": response_time,
            },
            status=500,
        )


def root_redirect(request):
    """Redirect root URL to API documentation"""
    return redirect("/api/docs/")


def api_root(request):
    """API root endpoint with available endpoints"""
    return JsonResponse(
        {
            "message": "Welcome to Shambit Travels API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health/",
                "admin": "/admin/",
                "api_docs": "/api/docs/",
                "api_schema": "/api/schema/",
                "auth": "/api/auth/",
                "cities": "/api/cities/",
                "articles": "/api/articles/",
                "packages": "/api/packages/",
                "bookings": "/api/bookings/",
                "payments": "/api/payments/",
                "notifications": "/api/notifications/",
                "seo": "/api/seo/",
                "media": "/api/media/",
                "pricing": "/api/pricing/",
                "search": "/api/search/",
            },
        }
    )


# Customize admin site
admin.site.site_header = "Travel Platform Admin"
admin.site.site_title = "Travel Platform"
admin.site.index_title = "Welcome to Travel Platform Administration"

urlpatterns = [
    path("", root_redirect, name="root"),
    path("api/", api_root, name="api-root"),
    path("health/", health_check, name="health-check"),
    path(
        "api/health/", health_check, name="api-health-check"
    ),  # Alternative path for Railway
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/cities/", include("cities.urls")),
    path("api/articles/", include("articles.urls")),
    path("api/packages/", include("packages.urls")),
    path("api/bookings/", include("bookings.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/seo/", include("seo.urls")),
    path("api/media/", include("media_library.urls")),
    path("api/pricing/", include("pricing_engine.urls")),
    path("api/search/", include("search.urls")),  # Universal search endpoint
    # API Documentation - Secure access based on environment
    path("api/schema/", SecureSpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SecureSpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SecureSpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # Custom media serving for Railway - handles multiple storage locations
    path("media/<path:path>", serve_media, name="serve_media"),
]

# Only add static file serving in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
