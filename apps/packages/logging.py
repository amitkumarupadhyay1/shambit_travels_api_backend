"""
Audit logging for packages app
Logs important events like price calculations, validation failures, etc.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("packages.audit")


class AuditLogger:
    """Centralized audit logging for packages operations"""

    @staticmethod
    def log_price_calculation(
        user_id: Optional[int],
        package_slug: str,
        experience_count: int,
        total_price: float,
        ip_address: str,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log price calculation attempts"""
        log_data = {
            "event": "price_calculation",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id or "anonymous",
            "package_slug": package_slug,
            "experience_count": experience_count,
            "total_price": total_price,
            "ip_address": ip_address,
            "success": success,
        }

        if error:
            log_data["error"] = error

        if success:
            logger.info(f"Price calculation successful: {log_data}")
        else:
            logger.warning(f"Price calculation failed: {log_data}")

    @staticmethod
    def log_validation_failure(
        endpoint: str,
        error_type: str,
        error_message: str,
        user_id: Optional[int],
        ip_address: str,
        request_data: Optional[Dict[str, Any]] = None,
    ):
        """Log validation failures for security monitoring"""
        log_data = {
            "event": "validation_failure",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "error_type": error_type,
            "error_message": error_message,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address,
        }

        # Sanitize request data (remove sensitive info)
        if request_data:
            safe_data = {k: v for k, v in request_data.items() if k != "password"}
            log_data["request_data"] = safe_data

        logger.warning(f"Validation failure: {log_data}")

    @staticmethod
    def log_rate_limit_exceeded(
        endpoint: str,
        user_id: Optional[int],
        ip_address: str,
        rate_limit: str,
    ):
        """Log rate limit violations"""
        log_data = {
            "event": "rate_limit_exceeded",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address,
            "rate_limit": rate_limit,
        }

        logger.warning(f"Rate limit exceeded: {log_data}")

    @staticmethod
    def log_suspicious_activity(
        activity_type: str,
        description: str,
        user_id: Optional[int],
        ip_address: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log suspicious activities for security review"""
        log_data = {
            "event": "suspicious_activity",
            "timestamp": datetime.now().isoformat(),
            "activity_type": activity_type,
            "description": description,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address,
        }

        if additional_data:
            log_data["additional_data"] = additional_data

        logger.error(f"Suspicious activity detected: {log_data}")

    @staticmethod
    def log_search_query(
        query: str,
        results_count: int,
        user_id: Optional[int],
        ip_address: str,
        sanitized: bool = False,
    ):
        """Log search queries for analytics and security"""
        log_data = {
            "event": "search_query",
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # Limit length
            "results_count": results_count,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address,
            "sanitized": sanitized,
        }

        logger.info(f"Search query: {log_data}")


def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip
