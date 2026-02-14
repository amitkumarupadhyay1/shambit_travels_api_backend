"""
Caching utilities for packages app
Provides decorators and functions for caching API responses
"""

import hashlib
import logging
from functools import wraps
from typing import Any, Callable, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest

logger = logging.getLogger("packages.cache")


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from prefix and arguments
    """
    # Create a string from all arguments
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

    # Create hash for long keys
    key_string = ":".join(key_parts)
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    return key_string


def cache_response(
    timeout: Optional[int] = None,
    key_prefix: str = "api",
    vary_on_user: bool = False,
    vary_on_params: Optional[list] = None,
):
    """
    Decorator to cache API responses

    Args:
        timeout: Cache timeout in seconds (None = use default)
        key_prefix: Prefix for cache key
        vary_on_user: Include user ID in cache key
        vary_on_params: List of query params to include in cache key

    Example:
        @cache_response(timeout=300, key_prefix="experiences", vary_on_params=["city"])
        def list(self, request, *args, **kwargs):
            return super().list(request, *args, **kwargs)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, request: HttpRequest, *args, **kwargs):
            # Build cache key
            key_parts = [key_prefix, func.__name__]

            # Add user ID if needed
            if (
                vary_on_user
                and hasattr(request, "user")
                and request.user.is_authenticated
            ):
                key_parts.append(f"user_{request.user.id}")

            # Add query params if specified
            if vary_on_params:
                for param in vary_on_params:
                    value = request.query_params.get(param)
                    if value:
                        key_parts.append(f"{param}_{value}")

            # Add URL args
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in kwargs.items())

            cache_key = get_cache_key(*key_parts)

            # Try to get from cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Cache hit: {cache_key}")
                # Return cached data as Response
                from rest_framework.response import Response

                return Response(cached_data)

            # Call the function
            logger.info(f"Cache miss: {cache_key}")
            response = func(self, request, *args, **kwargs)

            # Cache the response data if successful
            if hasattr(response, "status_code") and 200 <= response.status_code < 300:
                cache_timeout = timeout or getattr(settings, "CACHE_TTL", {}).get(
                    key_prefix, 300
                )
                # Cache the data, not the Response object
                if hasattr(response, "data"):
                    cache.set(cache_key, response.data, cache_timeout)
                    logger.info(
                        f"Cached response data: {cache_key} (timeout={cache_timeout}s)"
                    )

            return response

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache keys matching a pattern

    Args:
        pattern: Pattern to match (e.g., "experiences:*")

    Returns:
        Number of keys deleted
    """
    try:
        # This works with django-redis backend
        if hasattr(cache, "delete_pattern"):
            deleted = cache.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
            return deleted
        else:
            # Fallback: clear entire cache
            cache.clear()
            logger.warning(
                f"Cache backend doesn't support patterns, cleared entire cache"
            )
            return 0
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return 0


def invalidate_package_cache(package_slug: str) -> None:
    """
    Invalidate all cache entries related to a package
    """
    patterns = [
        f"package:*{package_slug}*",
        "packages:*",
        f"price_range:*{package_slug}*",
        # Legacy prefixes kept for backward compatibility
        f"api:package:*{package_slug}*",
        "api:packages:*",
        f"api:price_range:*{package_slug}*",
    ]

    for pattern in patterns:
        invalidate_cache(pattern)


def invalidate_experience_cache(experience_id: Optional[int] = None) -> None:
    """
    Invalidate all cache entries related to experiences
    """
    if experience_id:
        patterns = [
            f"experience:*{experience_id}*",
            "experiences:*",
            # Legacy prefixes
            f"api:experience:*{experience_id}*",
            "api:experiences:*",
        ]
    else:
        patterns = [
            "experiences:*",
            "api:experiences:*",
        ]

    for pattern in patterns:
        invalidate_cache(pattern)


class CacheStats:
    """
    Track cache hit/miss statistics
    """

    def __init__(self):
        self.hits = 0
        self.misses = 0

    def record_hit(self):
        self.hits += 1

    def record_miss(self):
        self.misses += 1

    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def reset(self):
        self.hits = 0
        self.misses = 0

    def __str__(self):
        return f"Cache Stats: {self.hits} hits, {self.misses} misses, {self.get_hit_rate():.1f}% hit rate"


# Global cache stats instance
cache_stats = CacheStats()
