from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r"", views.MediaViewSet, basename="media")
router.register(r"tools", views.MediaToolsViewSet, basename="mediatools")

urlpatterns = [
    path("", include(router.urls)),
]

# Available endpoints:
#
# Media Management:
# GET /api/media/ - List media files (with filtering)
# POST /api/media/ - Upload media file
# GET /api/media/{id}/ - Get specific media file
# PUT /api/media/{id}/ - Update media metadata
# PATCH /api/media/{id}/ - Partial update media metadata
# DELETE /api/media/{id}/ - Delete media file
#
# Custom Media Actions:
# GET /api/media/gallery/?page=1&page_size=20 - Gallery view with pagination
# GET /api/media/by_content_type/ - Get media grouped by content type
# GET /api/media/for_object/?content_type=app.model&object_id=123 - Get media for specific object
# GET /api/media/{id}/download/ - Download media file
# GET /api/media/{id}/thumbnail/?size=150x150 - Get thumbnail for image
# POST /api/media/bulk_upload/ - Upload multiple files
# POST /api/media/bulk_operations/ - Perform bulk operations (delete, update metadata)
# GET /api/media/stats/ - Get media library statistics
# GET /api/media/recent/?days=7 - Get recently uploaded media
# GET /api/media/orphaned/ - Find orphaned media files
# DELETE /api/media/cleanup_orphaned/ - Delete orphaned media files
# POST /api/media/search/ - Advanced search for media files
# POST /api/media/{id}/optimize/ - Optimize media file
# GET /api/media/content_types/ - Get available content types for media
#
# Media Tools:
# POST /api/media/tools/validate_file/ - Validate file before upload
# GET /api/media/tools/storage_info/ - Get storage information and usage
# POST /api/media/tools/cleanup_unused/ - Clean up unused media files
#
# Query parameters for list endpoint:
# ?content_type=app.model - Filter by content type
# ?object_id=123 - Filter by object ID
# ?file_type=image/video/document/other - Filter by file type
# ?search=text - Search in title, alt_text, filename
# ?date_from=YYYY-MM-DD - Filter by upload date from
# ?date_to=YYYY-MM-DD - Filter by upload date to
