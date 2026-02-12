# Cloud Storage Configuration for Production
# This file contains storage backends for cloud providers

import os

from django.conf import settings

# Cloudinary Configuration (RECOMMENDED - Free Tier Available)
if os.environ.get("USE_CLOUDINARY") == "True":
    import cloudinary
    import cloudinary.api
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
        api_key=os.environ.get("CLOUDINARY_API_KEY"),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
        secure=True,
    )

    # Use Cloudinary for media files
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

    # Free tier optimization settings
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
        "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
        "SECURE": True,
        "MEDIA_TAG": "media_library",
        "INVALID_VIDEO_ERROR_MESSAGE": "Please upload a valid video file.",
        "EXCLUDE_DELETE_ORPHANED_MEDIA_PATHS": (),
        "STATIC_TAG": "static",
        "STATICFILES_MANIFEST_ROOT": os.path.join(settings.BASE_DIR, "manifest"),
        "MAGIC_FILE_PATH": "magic",
    }

# AWS S3 Configuration (if you want to use S3 later)
elif os.environ.get("USE_S3") == "True":
    # AWS S3 settings
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }

    # Media files
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
