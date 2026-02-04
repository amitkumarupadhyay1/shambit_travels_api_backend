import os

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint for Railway"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse(
            {
                "status": "healthy",
                "database": "connected",
                "debug": settings.DEBUG,
                "environment": os.environ.get("RAILWAY_ENVIRONMENT", "unknown"),
            }
        )
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
