import mimetypes
import os
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from PIL import Image
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Media
from .serializers import (
    ContentTypeMediaSerializer,
    MediaBulkSerializer,
    MediaGallerySerializer,
    MediaListSerializer,
    MediaSearchSerializer,
    MediaSerializer,
    MediaStatsSerializer,
    MediaUpdateSerializer,
    MediaUploadSerializer,
)
from .services.cloudinary_monitor import CloudinaryMonitor
from .services.media_service import MediaService
from .utils import MediaProcessor, MediaValidator


class MediaViewSet(viewsets.ModelViewSet):
    """
    Production-level media library viewset with comprehensive features:
    - File upload with validation and processing
    - Image resizing and optimization
    - Bulk operations for efficiency
    - Advanced search and filtering
    - Content type association
    - Statistics and analytics
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Optimized queryset with filtering capabilities
        """
        queryset = Media.objects.select_related("content_type").all()

        # Filter by content type
        content_type = self.request.query_params.get("content_type")
        if content_type:
            try:
                app_label, model = content_type.split(".")
                ct = ContentType.objects.get(app_label=app_label, model=model)
                queryset = queryset.filter(content_type=ct)
            except (ValueError, ContentType.DoesNotExist):
                pass

        # Filter by object ID
        object_id = self.request.query_params.get("object_id")
        if object_id:
            try:
                queryset = queryset.filter(object_id=int(object_id))
            except ValueError:
                pass

        # Filter by file type
        file_type = self.request.query_params.get("file_type")
        if file_type:
            if file_type == "image":
                queryset = queryset.filter(file__iregex=r"\.(jpg|jpeg|png|gif|webp)$")
            elif file_type == "video":
                queryset = queryset.filter(file__iregex=r"\.(mp4|avi|mov|wmv|flv)$")
            elif file_type == "document":
                queryset = queryset.filter(file__iregex=r"\.pdf$")

        # Search in title and alt_text
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(alt_text__icontains=search)
                | Q(file__icontains=search)
            )

        # Date range filtering
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if date_from:
            try:
                from datetime import datetime

                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass

        if date_to:
            try:
                from datetime import datetime

                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == "list":
            return MediaListSerializer
        elif self.action == "create":
            return MediaUploadSerializer
        elif self.action in ["update", "partial_update"]:
            return MediaUpdateSerializer
        return MediaSerializer

    def perform_create(self, serializer):
        """
        Handle file upload with processing
        """
        media = serializer.save()

        # Process the uploaded file
        processor = MediaProcessor()
        processor.process_media(media)

    def create(self, request, *args, **kwargs):
        """
        Create media and return full representation (id/file_url/etc),
        not just upload payload fields.
        """
        serializer = MediaUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        media = serializer.instance
        output_serializer = MediaSerializer(media, context={"request": request})
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=["get"])
    def gallery(self, request):
        """
        Get media in gallery format with pagination
        """
        queryset = self.get_queryset()

        # Pagination
        page_size = int(request.query_params.get("page_size", 20))
        page = int(request.query_params.get("page", 1))

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = MediaListSerializer(
            page_obj.object_list, many=True, context={"request": request}
        )

        gallery_data = {
            "media": serializer.data,
            "total_count": paginator.count,
            "page_count": paginator.num_pages,
            "current_page": page,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        }

        gallery_serializer = MediaGallerySerializer(gallery_data)
        return Response(gallery_serializer.data)

    @action(detail=False, methods=["get"])
    def by_content_type(self, request):
        """
        Get media grouped by content type
        """
        content_types = (
            ContentType.objects.filter(media__isnull=False)
            .distinct()
            .prefetch_related("media_set")
        )

        serializer = ContentTypeMediaSerializer(content_types, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def for_object(self, request):
        """
        Get media for a specific object
        """
        content_type = request.query_params.get("content_type")
        object_id = request.query_params.get("object_id")

        if not content_type or not object_id:
            return Response(
                {"error": "content_type and object_id parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            app_label, model = content_type.split(".")
            ct = ContentType.objects.get(app_label=app_label, model=model)
            media_files = Media.objects.filter(content_type=ct, object_id=object_id)

            serializer = MediaListSerializer(
                media_files, many=True, context={"request": request}
            )
            return Response(serializer.data)
        except (ValueError, ContentType.DoesNotExist):
            return Response(
                {"error": "Invalid content_type format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Download media file
        """
        media = self.get_object()

        if not media.file:
            raise Http404("File not found")

        try:
            filename = os.path.basename(media.file.name)
            content_type, _ = mimetypes.guess_type(filename)

            with media.file.open("rb") as file_obj:
                response = HttpResponse(
                    file_obj.read(),
                    content_type=content_type or "application/octet-stream",
                )
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                return response
        except Exception:
            raise Http404("File not found in storage")

    @action(detail=True, methods=["get"])
    def thumbnail(self, request, pk=None):
        """
        Get thumbnail for image files
        """
        media = self.get_object()

        if not media.file or not media.file.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".webp")
        ):
            return Response(
                {"error": "Thumbnail only available for image files"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        size = request.query_params.get("size", "150x150")
        try:
            width, height = map(int, size.split("x"))
        except ValueError:
            width, height = 150, 150

        processor = MediaProcessor()
        thumbnail_path = processor.generate_thumbnail(media, width, height)

        if thumbnail_path:
            return Response(
                {"thumbnail_url": request.build_absolute_uri(thumbnail_path)}
            )
        else:
            return Response(
                {"error": "Could not generate thumbnail"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def bulk_upload(self, request):
        """
        Upload multiple files at once
        """
        files = request.FILES.getlist("files")
        content_type_id = request.data.get("content_type")
        object_id = request.data.get("object_id")

        if not files:
            return Response(
                {"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        errors = []

        for file in files:
            try:
                # Validate file
                validator = MediaValidator()
                validator.validate_file(file)

                # Create media object
                media = Media.objects.create(
                    file=file,
                    title=file.name,
                    content_type_id=content_type_id,
                    object_id=object_id,
                )

                # Process the file
                processor = MediaProcessor()
                processor.process_media(media)

                serializer = MediaSerializer(media, context={"request": request})
                results.append(serializer.data)

            except Exception as e:
                errors.append({"file": file.name, "error": str(e)})

        return Response(
            {
                "uploaded": len(results),
                "errors": len(errors),
                "results": results,
                "error_details": errors,
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def bulk_operations(self, request):
        """
        Perform bulk operations on media files
        """
        serializer = MediaBulkSerializer(data=request.data)
        if serializer.is_valid():
            result = MediaService.bulk_operation(
                media_ids=serializer.validated_data["media_ids"],
                action=serializer.validated_data["action"],
                metadata=serializer.validated_data.get("metadata", {}),
            )
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Get media library statistics
        """
        stats = MediaService.get_media_stats()
        serializer = MediaStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """
        Get recently uploaded media
        """
        days = int(request.query_params.get("days", 7))
        recent_date = timezone.now() - timedelta(days=days)

        recent_media = self.get_queryset().filter(created_at__gte=recent_date)[
            :20
        ]  # Limit to 20 most recent

        serializer = MediaListSerializer(
            recent_media, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def orphaned(self, request):
        """
        Find orphaned media files (not attached to any object)
        """
        orphaned_media = []

        for media in Media.objects.all():
            try:
                # Try to access the content object
                if not media.content_object:
                    orphaned_media.append(media)
            except:
                orphaned_media.append(media)

        serializer = MediaListSerializer(
            orphaned_media, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["delete"], permission_classes=[IsAuthenticated])
    def cleanup_orphaned(self, request):
        """
        Delete orphaned media files
        """
        deleted_count = MediaService.cleanup_orphaned_media()
        return Response(
            {
                "message": f"Deleted {deleted_count} orphaned media files",
                "deleted_count": deleted_count,
            }
        )

    @action(detail=False, methods=["post"])
    def search(self, request):
        """
        Advanced search for media files
        """
        search_serializer = MediaSearchSerializer(data=request.data)
        if search_serializer.is_valid():
            results = MediaService.search_media(search_serializer.validated_data)
            serializer = MediaListSerializer(
                results, many=True, context={"request": request}
            )
            return Response(serializer.data)
        return Response(search_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def optimize(self, request, pk=None):
        """
        Optimize media file (compress images, etc.)
        """
        media = self.get_object()

        processor = MediaProcessor()
        result = processor.optimize_media(media)

        if result["success"]:
            # Refresh from database to get updated file info
            media.refresh_from_db()
            serializer = MediaSerializer(media, context={"request": request})
            return Response(
                {
                    "message": "Media optimized successfully",
                    "optimization_result": result,
                    "media": serializer.data,
                }
            )
        else:
            return Response(
                {"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def content_types(self, request):
        """
        Get available content types that can have media
        """
        # Get content types that are commonly used with media
        media_content_types = ["articles.article", "packages.package", "cities.city"]

        content_types = []
        for ct_string in media_content_types:
            try:
                app_label, model = ct_string.split(".")
                ct = ContentType.objects.get(app_label=app_label, model=model)
                content_types.append(
                    {
                        "id": ct.id,
                        "app_label": ct.app_label,
                        "model": ct.model,
                        "name": ct.name,
                        "media_count": Media.objects.filter(content_type=ct).count(),
                    }
                )
            except (ValueError, ContentType.DoesNotExist):
                continue

        return Response(content_types)

    @action(detail=False, methods=["get"])
    def allowed_file_types(self, request):
        """
        Get information about allowed file types for upload
        GET /api/media/allowed_file_types/

        Returns detailed information about:
        - Allowed file extensions
        - Maximum file sizes
        - File type descriptions
        - Use cases and examples
        """
        from .constants import get_file_type_info

        return Response(
            {
                "file_types": get_file_type_info(),
                "note": "These limits apply to all uploads. Files exceeding limits will be rejected.",
                "recommendation": "For best performance, use JPG or WebP for images, MP4 for videos.",
            }
        )

    @action(detail=False, methods=["get"])
    def health(self, request):
        """
        Health check for media storage
        GET /api/media/health/
        """
        storage_info = MediaService.get_storage_info()

        if "error" in storage_info:
            return Response(
                {
                    "status": "unhealthy",
                    "error": storage_info["error"],
                    "recommendation": "Check Railway volume configuration",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Check if using Railway volume
        is_persistent = "RAILWAY_VOLUME_MOUNT_PATH" in os.environ

        return Response(
            {
                "status": "healthy",
                "media_root": storage_info["media_root"],
                "is_persistent": is_persistent,
                "storage_type": (
                    "Railway Volume" if is_persistent else "Local/Ephemeral"
                ),
                "total_files": storage_info["total_files"],
                "total_size_mb": storage_info["total_size_mb"],
                "writable": True,
            }
        )

    @action(detail=False, methods=["get"])
    def cloudinary_usage(self, request):
        """
        Get Cloudinary usage statistics
        GET /api/media/cloudinary_usage/
        """
        try:
            monitor = CloudinaryMonitor()
            usage_stats = monitor.get_usage_stats()
            return Response(usage_stats)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to fetch Cloudinary usage", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def cloudinary_alerts(self, request):
        """
        Get Cloudinary usage alerts
        GET /api/media/cloudinary_alerts/
        """
        try:
            monitor = CloudinaryMonitor()
            alerts = monitor.get_alerts()
            return Response({"alerts": alerts, "count": len(alerts)})
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to fetch alerts", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def cloudinary_summary(self, request):
        """
        Get complete Cloudinary usage summary with recommendations
        GET /api/media/cloudinary_summary/
        """
        try:
            monitor = CloudinaryMonitor()
            summary = monitor.get_summary()
            return Response(summary)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to fetch summary", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MediaToolsViewSet(viewsets.ViewSet):
    """
    Additional media tools and utilities
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=["post"])
    def validate_file(self, request):
        """
        Validate a file before upload
        """
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        validator = MediaValidator()
        try:
            validation_result = validator.validate_file(file)
            return Response({"valid": True, "file_info": validation_result})
        except Exception as e:
            return Response({"valid": False, "error": str(e)})

    @action(detail=False, methods=["get"])
    def storage_info(self, request):
        """
        Get storage information and usage
        """
        storage_info = MediaService.get_storage_info()
        return Response(storage_info)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def cleanup_unused(self, request):
        """
        Clean up unused media files from storage
        """
        cleanup_result = MediaService.cleanup_unused_files()
        return Response(cleanup_result)
