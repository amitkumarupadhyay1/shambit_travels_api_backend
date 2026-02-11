"""
Custom exception handlers for standardized error responses
"""

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("packages.errors")


def custom_exception_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[Response]:
    """
    Custom exception handler that provides standardized error responses
    with user-friendly messages and proper logging
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)

    # Get request info for logging
    request = context.get("view").request if context.get("view") else None
    path = request.path if request else "unknown"
    method = request.method if request else "unknown"

    # If DRF handled it, enhance the response
    if response is not None:
        error_data = {
            "error": get_user_friendly_message(exc, response.status_code),
            "status_code": response.status_code,
        }

        # Add detail if available
        if hasattr(exc, "detail"):
            if isinstance(exc.detail, dict):
                error_data["details"] = exc.detail
            else:
                error_data["detail"] = str(exc.detail)

        # Log the error
        log_error(exc, response.status_code, path, method)

        return Response(error_data, status=response.status_code)

    # Handle Django exceptions that DRF doesn't handle
    if isinstance(exc, Http404):
        error_data = {
            "error": "The requested resource was not found.",
            "status_code": status.HTTP_404_NOT_FOUND,
        }
        log_error(exc, status.HTTP_404_NOT_FOUND, path, method)
        return Response(error_data, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, PermissionDenied):
        error_data = {
            "error": "You do not have permission to perform this action.",
            "status_code": status.HTTP_403_FORBIDDEN,
        }
        log_error(exc, status.HTTP_403_FORBIDDEN, path, method)
        return Response(error_data, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, ValidationError):
        error_data = {
            "error": "Validation error occurred.",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "details": exc.message_dict if hasattr(exc, "message_dict") else str(exc),
        }
        log_error(exc, status.HTTP_400_BAD_REQUEST, path, method)
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

    # Handle unexpected errors
    error_data = {
        "error": "An unexpected error occurred. Our team has been notified.",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    log_error(
        exc, status.HTTP_500_INTERNAL_SERVER_ERROR, path, method, is_unexpected=True
    )
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_user_friendly_message(exc: Exception, status_code: int) -> str:
    """
    Convert technical error messages to user-friendly ones
    """
    # Check if exception has a custom message
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, dict):
            # Return first error message from dict
            for key, value in detail.items():
                if isinstance(value, list):
                    return str(value[0])
                return str(value)
        return str(detail)

    # Default messages based on status code
    messages = {
        400: "Invalid request. Please check your input and try again.",
        401: "Authentication required. Please log in to continue.",
        403: "You do not have permission to perform this action.",
        404: "The requested resource was not found.",
        405: "This method is not allowed for this endpoint.",
        408: "Request timeout. Please try again.",
        409: "Conflict with existing data. Please check and try again.",
        429: "Too many requests. Please wait a moment and try again.",
        500: "Server error. Our team has been notified. Please try again later.",
        502: "Bad gateway. Please try again in a few moments.",
        503: "Service temporarily unavailable. Please try again shortly.",
        504: "Gateway timeout. Please try again.",
    }

    return messages.get(status_code, "An error occurred. Please try again.")


def log_error(
    exc: Exception,
    status_code: int,
    path: str,
    method: str,
    is_unexpected: bool = False,
) -> None:
    """
    Log error with appropriate level based on severity
    """
    error_info = {
        "exception_type": type(exc).__name__,
        "message": str(exc),
        "status_code": status_code,
        "path": path,
        "method": method,
    }

    if is_unexpected or status_code >= 500:
        logger.error(f"Server error: {error_info}", exc_info=True)
    elif status_code >= 400:
        logger.warning(f"Client error: {error_info}")
    else:
        logger.info(f"Error handled: {error_info}")
