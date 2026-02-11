"""
Middleware for monitoring and logging API performance
"""

import logging
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("packages.performance")


class PerformanceMonitoringMiddleware:
    """
    Middleware to log API response times and error rates
    Helps identify slow endpoints and performance issues
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip monitoring for static files and admin
        if request.path.startswith(("/static/", "/media/", "/admin/")):
            return self.get_response(request)

        # Record start time
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to ms

        # Log performance metrics
        log_data = {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "response_time_ms": round(response_time, 2),
            "user": (
                request.user.id
                if hasattr(request, "user") and request.user.is_authenticated
                else "anonymous"
            ),
        }

        # Log based on response time and status
        if response.status_code >= 500:
            logger.error(f"Server error: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Client error: {log_data}")
        elif response_time > 1000:  # Slow request (>1s)
            logger.warning(f"Slow request: {log_data}")
        else:
            logger.info(f"Request: {log_data}")

        # Add response time header for debugging
        response["X-Response-Time"] = f"{round(response_time, 2)}ms"

        return response


class ErrorRateMonitoringMiddleware:
    """
    Middleware to track error rates for monitoring
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.error_count = 0
        self.request_count = 0

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip monitoring for static files and admin
        if request.path.startswith(("/static/", "/media/", "/admin/")):
            return self.get_response(request)

        self.request_count += 1

        response = self.get_response(request)

        # Track errors
        if response.status_code >= 400:
            self.error_count += 1

        # Log error rate every 100 requests
        if self.request_count % 100 == 0:
            error_rate = (self.error_count / self.request_count) * 100
            logger.info(
                f"Error rate: {error_rate:.2f}% "
                f"({self.error_count}/{self.request_count} requests)"
            )

        return response
