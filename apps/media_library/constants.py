"""
Media Library Constants and Configuration

This module defines allowed file types, size limits, and validation rules
for the media library system.
"""

# Allowed file types with their configurations
ALLOWED_FILE_TYPES = {
    "images": {
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "mime_types": [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        ],
        "max_size_mb": 5,
        "max_size_bytes": 5 * 1024 * 1024,
        "max_dimensions": {"width": 4000, "height": 4000},
        "min_dimensions": {"width": 10, "height": 10},
        "description": "Images for galleries, articles, and city pages",
        "examples": "JPG, PNG, GIF, WebP",
        "use_cases": [
            "City hero images",
            "Article featured images",
            "Package gallery photos",
            "User profile pictures",
        ],
    },
    "videos": {
        "extensions": [".mp4", ".avi", ".mov", ".wmv", ".flv"],
        "mime_types": [
            "video/mp4",
            "video/avi",
            "video/quicktime",
            "video/x-ms-wmv",
            "video/x-flv",
        ],
        "max_size_mb": 50,
        "max_size_bytes": 50 * 1024 * 1024,
        "description": "Video content for experiences and tours",
        "examples": "MP4, MOV, AVI",
        "use_cases": [
            "Experience preview videos",
            "Tour walkthroughs",
            "Destination highlights",
        ],
    },
    "documents": {
        "extensions": [".pdf"],
        "mime_types": ["application/pdf"],
        "max_size_mb": 10,
        "max_size_bytes": 10 * 1024 * 1024,
        "description": "PDF documents like brochures and itineraries",
        "examples": "PDF",
        "use_cases": [
            "Travel brochures",
            "Itinerary documents",
            "Terms and conditions",
            "Booking confirmations",
        ],
    },
}


def get_allowed_extensions():
    """
    Get all allowed file extensions across all file types

    Returns:
        list: List of allowed extensions (e.g., ['.jpg', '.png', ...])
    """
    extensions = []
    for file_type in ALLOWED_FILE_TYPES.values():
        extensions.extend(file_type["extensions"])
    return extensions


def get_allowed_mime_types():
    """
    Get all allowed MIME types across all file types

    Returns:
        list: List of allowed MIME types
    """
    mime_types = []
    for file_type in ALLOWED_FILE_TYPES.values():
        mime_types.extend(file_type["mime_types"])
    return mime_types


def get_file_type_info():
    """
    Get formatted file type information for display to users

    Returns:
        dict: Formatted file type information
    """
    return {
        key: {
            "extensions": ", ".join(value["extensions"]),
            "max_size": f"{value['max_size_mb']} MB",
            "description": value["description"],
            "examples": value["examples"],
            "use_cases": value.get("use_cases", []),
        }
        for key, value in ALLOWED_FILE_TYPES.items()
    }


def get_max_size_for_extension(extension):
    """
    Get maximum file size for a given extension

    Args:
        extension (str): File extension (e.g., '.jpg')

    Returns:
        int: Maximum size in bytes, or None if extension not found
    """
    extension = extension.lower()
    for file_type in ALLOWED_FILE_TYPES.values():
        if extension in file_type["extensions"]:
            return file_type["max_size_bytes"]
    return None


def is_extension_allowed(extension):
    """
    Check if a file extension is allowed

    Args:
        extension (str): File extension (e.g., '.jpg')

    Returns:
        bool: True if extension is allowed
    """
    return extension.lower() in get_allowed_extensions()


def get_file_type_category(extension):
    """
    Get the category (images/videos/documents) for a file extension

    Args:
        extension (str): File extension (e.g., '.jpg')

    Returns:
        str: Category name or 'other' if not found
    """
    extension = extension.lower()
    for category, config in ALLOWED_FILE_TYPES.items():
        if extension in config["extensions"]:
            return category
    return "other"


# Cloudinary folder structure
CLOUDINARY_FOLDERS = {
    "cities": "media_library/cities",
    "articles": "media_library/articles",
    "packages": "media_library/packages",
    "users": "media_library/users",
    "unattached": "media_library/unattached",
}


# Responsive image sizes for different devices
RESPONSIVE_IMAGE_SIZES = {
    "thumbnail_small": {"width": 150, "height": 150, "crop": "fill"},
    "thumbnail_medium": {"width": 300, "height": 200, "crop": "fill"},
    "thumbnail_large": {"width": 600, "height": 400, "crop": "fill"},
    "mobile_small": {"width": 480, "crop": "limit"},
    "mobile_large": {"width": 768, "crop": "limit"},
    "tablet": {"width": 1024, "crop": "limit"},
    "desktop": {"width": 1920, "crop": "limit"},
}


# Cloudinary transformation presets
CLOUDINARY_TRANSFORMATIONS = {
    "thumbnail": "c_fill,w_150,h_150,q_auto,f_auto",
    "small": "c_limit,w_640,q_auto,f_auto",
    "medium": "c_limit,w_1024,q_auto,f_auto",
    "large": "c_limit,w_1920,q_auto,f_auto",
    "mobile": "c_limit,w_768,q_auto,f_auto,dpr_2.0",
    "tablet": "c_limit,w_1024,q_auto,f_auto,dpr_2.0",
    "desktop": "c_limit,w_1920,q_auto,f_auto",
}
