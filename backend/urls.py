from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from .swagger_views import (
    SecureSpectacularAPIView,
    SecureSpectacularRedocView,
    SecureSpectacularSwaggerView,
)


def health_check(request):
    """Health check endpoint for monitoring and load balancers"""
    return JsonResponse(
        {"status": "healthy", "service": "shambit-travels-api", "version": "1.0.0"}
    )


# Customize admin site
admin.site.site_header = "Travel Platform Admin"
admin.site.site_title = "Travel Platform"
admin.site.index_title = "Welcome to Travel Platform Administration"

urlpatterns = [
    path("health/", health_check, name="health-check"),
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
]

if settings.DEBUG:
    # import debug_toolbar
    # urlpatterns = [
    #     path('__debug__/', include(debug_toolbar.urls)),
    # ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
