"""
Secure Swagger views with environment-based access control.
Production: Admin-only access
Development: Public access
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAdminUser
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


class SecureSpectacularAPIView(SpectacularAPIView):
    """Schema view with environment-based security"""
    
    def get_permissions(self):
        if not settings.DEBUG:
            return [IsAdminUser()]
        return []


class SecureSpectacularSwaggerView(SpectacularSwaggerView):
    """Swagger UI with environment-based security"""
    
    def get_permissions(self):
        if not settings.DEBUG:
            return [IsAdminUser()]
        return []


class SecureSpectacularRedocView(SpectacularRedocView):
    """ReDoc UI with environment-based security"""
    
    def get_permissions(self):
        if not settings.DEBUG:
            return [IsAdminUser()]
        return []


# Apply login_required decorator for non-DEBUG environments
if not settings.DEBUG:
    SecureSpectacularSwaggerView = method_decorator(
        login_required, name='dispatch'
    )(SecureSpectacularSwaggerView)
    
    SecureSpectacularRedocView = method_decorator(
        login_required, name='dispatch'
    )(SecureSpectacularRedocView)
    
    SecureSpectacularAPIView = method_decorator(
        login_required, name='dispatch'
    )(SecureSpectacularAPIView)