import os
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from PIL import Image
from rest_framework import serializers

from .models import Media


class MediaSerializer(serializers.ModelSerializer):
    """
    Full media serializer for detailed views
    """

    content_type_name = serializers.CharField(
        source="content_type.model", read_only=True
    )
    content_object_str = serializers.CharField(
        source="content_object.__str__", read_only=True
    )
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    is_image = serializers.SerializerMethodField()
    image_dimensions = serializers.SerializerMethodField()
    responsive_urls = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            "id",
            "file",
            "file_url",
            "file_size",
            "file_type",
            "is_image",
            "image_dimensions",
            "responsive_urls",
            "alt_text",
            "title",
            "content_type",
            "object_id",
            "content_type_name",
            "content_object_str",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "file_url",
            "file_size",
            "file_type",
            "is_image",
            "image_dimensions",
            "responsive_urls",
        ]

    def get_file_url(self, obj) -> Optional[str]:
        """Get the full URL of the file"""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_file_size(self, obj) -> Optional[int]:
        """Get file size in bytes"""
        if obj.file:
            try:
                return obj.file.size
            except (OSError, ValueError):
                return None
        return None

    def get_file_type(self, obj) -> Optional[str]:
        """Get file MIME type"""
        if obj.file:
            name = obj.file.name.lower()
            if name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                return "image"
            elif name.endswith((".mp4", ".avi", ".mov", ".wmv", ".flv")):
                return "video"
            elif name.endswith((".pdf")):
                return "document"
            else:
                return "other"
        return None

    def get_is_image(self, obj) -> bool:
        """Check if file is an image"""
        return self.get_file_type(obj) == "image"

    def get_image_dimensions(self, obj) -> Optional[dict]:
        """Get image dimensions if it's an image"""
        if self.get_is_image(obj) and obj.file:
            try:
                with Image.open(obj.file.path) as img:
                    return {"width": img.width, "height": img.height}
            except (OSError, ValueError, AttributeError):
                return None
        return None

    def get_responsive_urls(self, obj) -> Optional[dict]:
        """
        Generate responsive image URLs for different screen sizes
        Only for images, returns None for other file types

        Uses Cloudinary transformations when available for automatic
        format optimization (WebP, AVIF) and quality adjustment
        """
        if not obj.file or not self.get_is_image(obj):
            return None

        # Check if using Cloudinary
        if hasattr(obj.file, "url") and "cloudinary" in obj.file.url:
            base_url = obj.file.url

            # Generate Cloudinary transformation URLs
            return {
                "thumbnail": self._cloudinary_transform(
                    base_url, "c_fill,w_150,h_150,q_auto,f_auto"
                ),
                "small": self._cloudinary_transform(
                    base_url, "c_limit,w_640,q_auto,f_auto"
                ),
                "medium": self._cloudinary_transform(
                    base_url, "c_limit,w_1024,q_auto,f_auto"
                ),
                "large": self._cloudinary_transform(
                    base_url, "c_limit,w_1920,q_auto,f_auto"
                ),
                "mobile": self._cloudinary_transform(
                    base_url, "c_limit,w_768,q_auto,f_auto,dpr_2.0"
                ),
                "tablet": self._cloudinary_transform(
                    base_url, "c_limit,w_1024,q_auto,f_auto,dpr_2.0"
                ),
                "original": base_url,
            }

        # For local storage, return original only
        return {"original": obj.file.url if obj.file else None}

    def _cloudinary_transform(self, url: str, transformation: str) -> str:
        """
        Apply Cloudinary transformation to URL

        Args:
            url: Original Cloudinary URL
            transformation: Transformation string (e.g., 'c_fill,w_150,h_150')

        Returns:
            Transformed URL
        """
        # Cloudinary URL format: .../upload/v123/path.jpg
        # Insert transformation: .../upload/transformation/v123/path.jpg
        if "/upload/" in url:
            return url.replace("/upload/", f"/upload/{transformation}/")
        return url


class MediaListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views
    """

    file_url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    content_type_name = serializers.CharField(
        source="content_type.model", read_only=True
    )

    class Meta:
        model = Media
        fields = [
            "id",
            "file_url",
            "file_type",
            "title",
            "alt_text",
            "content_type_name",
            "created_at",
        ]

    def get_file_url(self, obj) -> Optional[str]:
        """Get the full URL of the file"""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_file_type(self, obj) -> Optional[str]:
        """Get file type"""
        if obj.file:
            name = obj.file.name.lower()
            if name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                return "image"
            elif name.endswith((".mp4", ".avi", ".mov", ".wmv", ".flv")):
                return "video"
            elif name.endswith((".pdf")):
                return "document"
            else:
                return "other"
        return None


class MediaUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading media files
    """

    class Meta:
        model = Media
        fields = ["file", "title", "alt_text", "content_type", "object_id"]

    def validate_file(self, value):
        """
        Validate uploaded file
        """
        if not value:
            raise serializers.ValidationError("File is required")

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size too large. Maximum size is {max_size // (1024*1024)}MB"
            )

        # Check file type
        allowed_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",  # Images
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",  # Videos
            ".pdf",  # Documents
        ]

        file_extension = os.path.splitext(value.name)[1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )

        return value

    def validate(self, data):
        """
        Validate that the content object exists
        """
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        if content_type and object_id:
            try:
                content_type.get_object_for_this_type(id=object_id)
            except content_type.model_class().DoesNotExist:
                raise serializers.ValidationError(
                    f"Object with id {object_id} does not exist for {content_type.model}"
                )

        return data


class MediaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating media metadata (not the file itself)
    """

    class Meta:
        model = Media
        fields = ["title", "alt_text"]


class MediaBulkSerializer(serializers.Serializer):
    """
    Serializer for bulk operations
    """

    media_ids = serializers.ListField(child=serializers.IntegerField())
    action = serializers.ChoiceField(choices=["delete", "update_metadata"])
    metadata = serializers.DictField(required=False)

    def validate_action(self, value):
        """Validate the action"""
        if value not in ["delete", "update_metadata"]:
            raise serializers.ValidationError("Invalid action")
        return value

    def validate(self, data):
        """Validate bulk operation data"""
        if data["action"] == "update_metadata" and not data.get("metadata"):
            raise serializers.ValidationError(
                "Metadata is required for update_metadata action"
            )
        return data


class MediaStatsSerializer(serializers.Serializer):
    """
    Serializer for media statistics
    """

    total_files = serializers.IntegerField()
    total_size = serializers.IntegerField()
    by_type = serializers.DictField()
    by_content_type = serializers.ListField()
    recent_uploads = serializers.IntegerField()


class MediaSearchSerializer(serializers.Serializer):
    """
    Serializer for media search parameters
    """

    query = serializers.CharField(required=False, allow_blank=True)
    file_type = serializers.ChoiceField(
        choices=["image", "video", "document", "other"], required=False
    )
    content_type = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate_content_type(self, value):
        """Validate content type format"""
        if value:
            try:
                app_label, model = value.split(".")
                ContentType.objects.get(app_label=app_label, model=model)
            except (ValueError, ContentType.DoesNotExist):
                raise serializers.ValidationError(
                    "Content type must be in format 'app_label.model' and must exist"
                )
        return value


class ContentTypeMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for getting media by content type
    """

    media_files = MediaListSerializer(source="media_set", many=True, read_only=True)

    class Meta:
        model = ContentType
        fields = ["id", "app_label", "model", "media_files"]


class MediaGallerySerializer(serializers.Serializer):
    """
    Serializer for gallery view with pagination info
    """

    media = MediaListSerializer(many=True)
    total_count = serializers.IntegerField()
    page_count = serializers.IntegerField()
    current_page = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()
