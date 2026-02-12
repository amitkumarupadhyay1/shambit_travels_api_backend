"""
Cloudinary Free Tier Optimization Middleware
Ensures we stay within Cloudinary free tier limits
"""

import os

from django.conf import settings


class CloudinaryOptimizationMiddleware:
    """
    Middleware to optimize Cloudinary usage for free tier.

    Free Tier Limits:
    - 25 GB storage
    - 25 GB bandwidth/month
    - 25,000 transformations/month

    This middleware provides helper methods for optimization.
    """

    # Free tier optimization constants
    MAX_FILE_SIZE_MB = 10  # Keep files under 10MB
    MAX_IMAGE_DIMENSION = 2000  # Max width/height
    DEFAULT_QUALITY = 80  # Compression quality

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    @staticmethod
    def get_optimized_transformation():
        """
        Returns Cloudinary transformation parameters optimized for free tier.
        Use these parameters when generating image URLs.

        Returns:
            dict: Transformation parameters
        """
        return {
            "quality": "auto:low",  # Automatic quality optimization
            "fetch_format": "auto",  # Automatic format selection (WebP when supported)
            "flags": "lossy",  # Lossy compression
            "dpr": "auto",  # Automatic DPR for responsive images
        }

    @staticmethod
    def get_thumbnail_transformation(width=300, height=200):
        """
        Returns optimized transformation for thumbnails.

        Args:
            width (int): Thumbnail width
            height (int): Thumbnail height

        Returns:
            dict: Transformation parameters
        """
        return {
            "width": width,
            "height": height,
            "crop": "fill",
            "quality": "auto:low",
            "fetch_format": "auto",
            "flags": "lossy",
        }

    @staticmethod
    def validate_file_size(file_size_bytes):
        """
        Validate file size against free tier limits.

        Args:
            file_size_bytes (int): File size in bytes

        Returns:
            tuple: (is_valid, error_message)
        """
        max_size_bytes = CloudinaryOptimizationMiddleware.MAX_FILE_SIZE_MB * 1024 * 1024

        if file_size_bytes > max_size_bytes:
            return (
                False,
                f"File size exceeds {CloudinaryOptimizationMiddleware.MAX_FILE_SIZE_MB}MB limit",
            )

        return True, None

    @staticmethod
    def should_compress_image(file_size_bytes):
        """
        Determine if image should be compressed before upload.

        Args:
            file_size_bytes (int): File size in bytes

        Returns:
            bool: True if compression recommended
        """
        # Compress if file is larger than 500KB
        return file_size_bytes > (500 * 1024)
