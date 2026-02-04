import mimetypes
import os
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.files.uploadedfile import (InMemoryUploadedFile,
                                            TemporaryUploadedFile)
from PIL import Image, ImageOps

from .models import Media


class MediaValidator:
    """
    Utility class for validating media files
    """

    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB for images
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB for videos

    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".wmv", ".flv"]
    ALLOWED_DOCUMENT_EXTENSIONS = [".pdf"]

    def validate_file(self, file) -> Dict[str, Any]:
        """
        Comprehensive file validation
        """
        if not file:
            raise ValueError("No file provided")

        # Get file info
        file_info = self._get_file_info(file)

        # Validate file size
        self._validate_file_size(file, file_info)

        # Validate file type
        self._validate_file_type(file, file_info)

        # Additional validation for images
        if file_info["type"] == "image":
            self._validate_image(file, file_info)

        return file_info

    def _get_file_info(self, file) -> Dict[str, Any]:
        """
        Extract file information
        """
        filename = file.name
        file_size = file.size
        file_extension = os.path.splitext(filename)[1].lower()

        # Determine file type
        if file_extension in self.ALLOWED_IMAGE_EXTENSIONS:
            file_type = "image"
        elif file_extension in self.ALLOWED_VIDEO_EXTENSIONS:
            file_type = "video"
        elif file_extension in self.ALLOWED_DOCUMENT_EXTENSIONS:
            file_type = "document"
        else:
            file_type = "other"

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(filename)

        return {
            "filename": filename,
            "size": file_size,
            "extension": file_extension,
            "type": file_type,
            "mime_type": mime_type,
        }

    def _validate_file_size(self, file, file_info: Dict[str, Any]):
        """
        Validate file size based on type
        """
        file_size = file_info["size"]
        file_type = file_info["type"]

        if file_type == "image" and file_size > self.MAX_IMAGE_SIZE:
            raise ValueError(
                f"Image file too large. Maximum size is {self.MAX_IMAGE_SIZE // (1024*1024)}MB"
            )
        elif file_type == "video" and file_size > self.MAX_VIDEO_SIZE:
            raise ValueError(
                f"Video file too large. Maximum size is {self.MAX_VIDEO_SIZE // (1024*1024)}MB"
            )
        elif file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large. Maximum size is {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )

    def _validate_file_type(self, file, file_info: Dict[str, Any]):
        """
        Validate file type and extension
        """
        extension = file_info["extension"]
        all_allowed = (
            self.ALLOWED_IMAGE_EXTENSIONS
            + self.ALLOWED_VIDEO_EXTENSIONS
            + self.ALLOWED_DOCUMENT_EXTENSIONS
        )

        if extension not in all_allowed:
            raise ValueError(
                f"File type not allowed. Allowed extensions: {', '.join(all_allowed)}"
            )

    def _validate_image(self, file, file_info: Dict[str, Any]):
        """
        Additional validation for image files
        """
        try:
            # Try to open and validate the image
            with Image.open(file) as img:
                # Check image dimensions
                width, height = img.size

                # Maximum dimensions
                max_width = 4000
                max_height = 4000

                if width > max_width or height > max_height:
                    raise ValueError(
                        f"Image dimensions too large. Maximum: {max_width}x{max_height}"
                    )

                # Minimum dimensions
                min_width = 10
                min_height = 10

                if width < min_width or height < min_height:
                    raise ValueError(
                        f"Image dimensions too small. Minimum: {min_width}x{min_height}"
                    )

                # Update file info with image dimensions
                file_info.update(
                    {"width": width, "height": height, "format": img.format}
                )

        except Exception as e:
            if "Image dimensions" in str(e):
                raise e
            raise ValueError("Invalid image file or corrupted image")


class MediaProcessor:
    """
    Utility class for processing media files
    """

    def process_media(self, media: Media) -> Dict[str, Any]:
        """
        Process uploaded media file
        """
        if not media.file:
            return {"success": False, "error": "No file to process"}

        file_type = self._get_file_type(media.file.name)

        if file_type == "image":
            return self._process_image(media)
        elif file_type == "video":
            return self._process_video(media)
        else:
            return {"success": True, "message": "No processing needed"}

    def _get_file_type(self, filename: str) -> str:
        """
        Determine file type from filename
        """
        extension = os.path.splitext(filename)[1].lower()

        if extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            return "image"
        elif extension in [".mp4", ".avi", ".mov", ".wmv", ".flv"]:
            return "video"
        else:
            return "other"

    def _process_image(self, media: Media) -> Dict[str, Any]:
        """
        Process image files (orientation, optimization)
        """
        try:
            with Image.open(media.file.path) as img:
                # Fix orientation based on EXIF data
                img = ImageOps.exif_transpose(img)

                # Convert RGBA to RGB if saving as JPEG
                if img.mode == "RGBA" and media.file.name.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    # Create white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(
                        img, mask=img.split()[-1]
                    )  # Use alpha channel as mask
                    img = background

                # Save the processed image
                img.save(media.file.path, optimize=True, quality=85)

                return {
                    "success": True,
                    "message": "Image processed successfully",
                    "dimensions": img.size,
                }

        except Exception as e:
            return {"success": False, "error": f"Error processing image: {str(e)}"}

    def _process_video(self, media: Media) -> Dict[str, Any]:
        """
        Process video files (placeholder for future video processing)
        """
        # Video processing would require additional libraries like ffmpeg
        # For now, just return success
        return {
            "success": True,
            "message": "Video uploaded successfully (no processing applied)",
        }

    def generate_thumbnail(
        self, media: Media, width: int = 150, height: int = 150
    ) -> Optional[str]:
        """
        Generate thumbnail for image files
        """
        if not media.file or not self._get_file_type(media.file.name) == "image":
            return None

        try:
            # Create thumbnails directory
            thumbnail_dir = os.path.join(os.path.dirname(media.file.path), "thumbnails")
            os.makedirs(thumbnail_dir, exist_ok=True)

            # Generate thumbnail filename
            filename = os.path.basename(media.file.name)
            name, ext = os.path.splitext(filename)
            thumbnail_filename = f"{name}_{width}x{height}{ext}"
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)

            # Generate thumbnail if it doesn't exist
            if not os.path.exists(thumbnail_path):
                with Image.open(media.file.path) as img:
                    # Create thumbnail maintaining aspect ratio
                    img.thumbnail((width, height), Image.Resampling.LANCZOS)

                    # Create a square thumbnail with padding if needed
                    if img.size != (width, height):
                        # Create new image with white background
                        new_img = Image.new("RGB", (width, height), (255, 255, 255))

                        # Calculate position to center the image
                        x = (width - img.size[0]) // 2
                        y = (height - img.size[1]) // 2

                        new_img.paste(img, (x, y))
                        img = new_img

                    img.save(thumbnail_path, optimize=True, quality=80)

            # Return relative URL
            media_url = getattr(settings, "MEDIA_URL", "/media/")
            relative_path = os.path.relpath(
                thumbnail_path, getattr(settings, "MEDIA_ROOT", "")
            )
            return f"{media_url}{relative_path}".replace("\\", "/")

        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None

    def optimize_media(self, media: Media) -> Dict[str, Any]:
        """
        Optimize media file (compress, resize if needed)
        """
        if not media.file:
            return {"success": False, "error": "No file to optimize"}

        file_type = self._get_file_type(media.file.name)

        if file_type == "image":
            return self._optimize_image(media)
        else:
            return {
                "success": False,
                "error": "Optimization not supported for this file type",
            }

    def _optimize_image(self, media: Media) -> Dict[str, Any]:
        """
        Optimize image file
        """
        try:
            original_size = os.path.getsize(media.file.path)

            with Image.open(media.file.path) as img:
                # Resize if image is too large
                max_dimension = 2000
                if img.width > max_dimension or img.height > max_dimension:
                    img.thumbnail(
                        (max_dimension, max_dimension), Image.Resampling.LANCZOS
                    )

                # Convert to RGB if RGBA (for JPEG)
                if img.mode == "RGBA" and media.file.name.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background

                # Save with optimization
                img.save(media.file.path, optimize=True, quality=75)

            new_size = os.path.getsize(media.file.path)
            size_reduction = original_size - new_size
            reduction_percentage = (
                (size_reduction / original_size) * 100 if original_size > 0 else 0
            )

            return {
                "success": True,
                "message": "Image optimized successfully",
                "original_size": original_size,
                "new_size": new_size,
                "size_reduction": size_reduction,
                "reduction_percentage": round(reduction_percentage, 2),
            }

        except Exception as e:
            return {"success": False, "error": f"Error optimizing image: {str(e)}"}


class MediaUtils:
    """
    General media utility functions
    """

    @staticmethod
    def get_file_type_icon(filename: str) -> str:
        """
        Get icon name for file type
        """
        extension = os.path.splitext(filename)[1].lower()

        icon_map = {
            # Images
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".gif": "image",
            ".webp": "image",
            # Videos
            ".mp4": "video",
            ".avi": "video",
            ".mov": "video",
            ".wmv": "video",
            ".flv": "video",
            # Documents
            ".pdf": "file-text",
            # Default
            "default": "file",
        }

        return icon_map.get(extension, icon_map["default"])

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math

        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)

        return f"{s} {size_names[i]}"

    @staticmethod
    def get_image_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an image file
        """
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "has_transparency": img.mode in ("RGBA", "LA")
                    or "transparency" in img.info,
                }
        except Exception:
            return None

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """
        Check if file is an image based on extension
        """
        extension = os.path.splitext(filename)[1].lower()
        return extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    @staticmethod
    def is_video_file(filename: str) -> bool:
        """
        Check if file is a video based on extension
        """
        extension = os.path.splitext(filename)[1].lower()
        return extension in [".mp4", ".avi", ".mov", ".wmv", ".flv"]

    @staticmethod
    def generate_unique_filename(original_filename: str, media_dir: str) -> str:
        """
        Generate unique filename to avoid conflicts
        """
        name, ext = os.path.splitext(original_filename)
        counter = 1
        new_filename = original_filename

        while os.path.exists(os.path.join(media_dir, new_filename)):
            new_filename = f"{name}_{counter}{ext}"
            counter += 1

        return new_filename

    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        Clean filename by removing/replacing invalid characters
        """
        import re

        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # Remove multiple underscores
        filename = re.sub(r"_+", "_", filename)

        # Remove leading/trailing underscores and dots
        filename = filename.strip("_.")

        # Ensure filename is not empty
        if not filename:
            filename = "unnamed_file"

        return filename
