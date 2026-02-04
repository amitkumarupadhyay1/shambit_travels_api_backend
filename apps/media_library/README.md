# Media Library App

A comprehensive media management system for the travel platform with production-level features for file upload, processing, and organization.

## Features

### Core Functionality
- ✅ File upload with validation and processing
- ✅ Support for images, videos, and documents
- ✅ Generic content object association
- ✅ Image processing and optimization
- ✅ Thumbnail generation
- ✅ Bulk operations for efficiency
- ✅ Advanced search and filtering
- ✅ Storage management and cleanup

### API Endpoints

#### Media Management
- `GET /api/media/` - List media files (with filtering)
- `POST /api/media/` - Upload media file
- `GET /api/media/{id}/` - Get specific media file
- `PUT /api/media/{id}/` - Update media metadata
- `PATCH /api/media/{id}/` - Partial update media metadata
- `DELETE /api/media/{id}/` - Delete media file

#### Custom Media Actions
- `GET /api/media/gallery/?page=1&page_size=20` - Gallery view with pagination
- `GET /api/media/by_content_type/` - Get media grouped by content type
- `GET /api/media/for_object/?content_type=app.model&object_id=123` - Get media for specific object
- `GET /api/media/{id}/download/` - Download media file
- `GET /api/media/{id}/thumbnail/?size=150x150` - Get thumbnail for image
- `POST /api/media/bulk_upload/` - Upload multiple files
- `POST /api/media/bulk_operations/` - Perform bulk operations (delete, update metadata)
- `GET /api/media/stats/` - Get media library statistics
- `GET /api/media/recent/?days=7` - Get recently uploaded media
- `GET /api/media/orphaned/` - Find orphaned media files
- `DELETE /api/media/cleanup_orphaned/` - Delete orphaned media files
- `POST /api/media/search/` - Advanced search for media files
- `POST /api/media/{id}/optimize/` - Optimize media file
- `GET /api/media/content_types/` - Get available content types for media

#### Media Tools
- `POST /api/media/tools/validate_file/` - Validate file before upload
- `GET /api/media/tools/storage_info/` - Get storage information and usage
- `POST /api/media/tools/cleanup_unused/` - Clean up unused media files

#### Query Parameters for List Endpoint
- `?content_type=app.model` - Filter by content type
- `?object_id=123` - Filter by object ID
- `?file_type=image/video/document/other` - Filter by file type
- `?search=text` - Search in title, alt_text, filename
- `?date_from=YYYY-MM-DD` - Filter by upload date from
- `?date_to=YYYY-MM-DD` - Filter by upload date to

### Service Layer

The `MediaService` class provides business logic methods:

```python
from media_library.services.media_service import MediaService

# Create media with content association
media = MediaService.create_media(
    file=uploaded_file,
    title='Beautiful Landscape',
    alt_text='A scenic mountain landscape',
    content_type='cities.city',
    object_id=city.id
)

# Get all media for an object
media_files = MediaService.get_media_for_object('articles.article', article.id)

# Bulk operations
result = MediaService.bulk_operation(
    media_ids=[1, 2, 3, 4, 5],
    action='update_metadata',
    metadata={'alt_text': 'Updated alt text'}
)

# Get comprehensive statistics
stats = MediaService.get_media_stats()
# Returns: {'total_files': 150, 'total_size': 52428800, 'by_type': {...}, ...}

# Advanced search
results = MediaService.search_media({
    'query': 'landscape',
    'file_type': 'image',
    'content_type': 'cities.city',
    'date_from': '2024-01-01'
})

# Cleanup operations
deleted_count = MediaService.cleanup_orphaned_media()
cleanup_result = MediaService.cleanup_unused_files()
```

### File Processing and Validation

Comprehensive file validation and processing:

```python
from media_library.utils import MediaValidator, MediaProcessor

# Validate uploaded files
validator = MediaValidator()
try:
    file_info = validator.validate_file(uploaded_file)
    # Returns: {'filename': '...', 'size': 1024, 'type': 'image', ...}
except ValueError as e:
    print(f"Validation error: {e}")

# Process media files
processor = MediaProcessor()
result = processor.process_media(media)
# Handles image orientation, optimization, format conversion

# Generate thumbnails
thumbnail_url = processor.generate_thumbnail(media, width=300, height=200)

# Optimize images
optimization_result = processor.optimize_media(media)
# Returns: {'success': True, 'size_reduction': 1024, 'reduction_percentage': 25.5}
```

### File Type Support

#### Images
- **Formats**: JPEG, PNG, GIF, WebP
- **Max Size**: 5MB
- **Max Dimensions**: 4000x4000 pixels
- **Processing**: Auto-rotation, format conversion, optimization
- **Features**: Thumbnail generation, dimension detection

#### Videos
- **Formats**: MP4, AVI, MOV, WMV, FLV
- **Max Size**: 50MB
- **Processing**: Basic validation (extensible for future video processing)

#### Documents
- **Formats**: PDF
- **Max Size**: 10MB
- **Processing**: Basic validation and metadata extraction

### Management Commands

#### Media Statistics
```bash
# Basic statistics
python manage.py media_stats

# Detailed statistics with storage info
python manage.py media_stats --detailed --storage

# Comprehensive usage report
python manage.py media_stats --usage-report
```

#### Media Cleanup
```bash
# Clean up orphaned media files
python manage.py cleanup_media --orphaned

# Clean up unused files from storage
python manage.py cleanup_media --unused

# Clean up everything
python manage.py cleanup_media --all

# Dry run to see what would be cleaned
python manage.py cleanup_media --all --dry-run
```

### Admin Interface

Enhanced admin interface with:
- **Visual Previews**: Thumbnail previews for images, file type icons for others
- **File Information**: Detailed file info including dimensions, size, format
- **Bulk Actions**: Optimize images, generate thumbnails, update metadata
- **Media Dashboard**: Comprehensive overview with statistics and recent uploads
- **Cleanup Tools**: Safe cleanup of orphaned and unused files
- **Storage Monitoring**: Disk usage and storage information

### Database Model

The media system uses a generic foreign key to attach media to any model:

```python
class Media(models.Model):
    file = models.FileField(upload_to='library/')
    alt_text = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    
    # Generic relation to attach media to anything
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### Usage Examples

#### Frontend Integration
```javascript
// Upload multiple files
const formData = new FormData();
files.forEach(file => formData.append('files', file));
formData.append('content_type', 'articles.article');
formData.append('object_id', articleId);

const response = await fetch('/api/media/bulk_upload/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});

// Get media gallery with pagination
const galleryResponse = await fetch('/api/media/gallery/?page=1&page_size=12');
const gallery = await galleryResponse.json();

// Search media files
const searchResponse = await fetch('/api/media/search/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        query: 'landscape',
        file_type: 'image',
        date_from: '2024-01-01'
    })
});

// Get thumbnail
const thumbnailUrl = `/api/media/${mediaId}/thumbnail/?size=300x200`;
```

#### Backend Integration
```python
# In your views, associate media with objects
from media_library.services.media_service import MediaService

def create_article_with_media(request):
    article = Article.objects.create(...)
    
    # Handle uploaded files
    for uploaded_file in request.FILES.getlist('images'):
        MediaService.create_media(
            file=uploaded_file,
            title=f"Image for {article.title}",
            content_type='articles.article',
            object_id=article.id
        )
    
    return JsonResponse({'success': True})

# In templates, display media
def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    
    # Get associated media
    media_files = MediaService.get_media_for_object('articles.article', article.id)
    
    return render(request, 'article_detail.html', {
        'article': article,
        'media_files': media_files
    })
```

### Performance Considerations

1. **File Validation**: Comprehensive validation prevents invalid uploads
2. **Image Processing**: Automatic optimization reduces storage usage
3. **Thumbnail Generation**: On-demand thumbnail creation with caching
4. **Bulk Operations**: Efficient bulk upload and management
5. **Database Indexes**: Optimized queries with proper indexing
6. **Storage Management**: Cleanup tools prevent storage bloat

### Security Features

- **File Type Validation**: Only allowed file types can be uploaded
- **Size Limits**: Configurable size limits prevent abuse
- **Content Validation**: Images are validated by opening them
- **Path Security**: Safe file path handling prevents directory traversal
- **Authentication**: Upload operations require authentication
- **Content Type Verification**: MIME type validation

### Storage Organization

```
media/
├── library/
│   ├── images/
│   │   ├── 2024/01/15/
│   │   └── thumbnails/
│   ├── videos/
│   └── documents/
```

### Configuration

Key settings for media library:

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024   # 50MB

# Media library specific settings
MEDIA_LIBRARY = {
    'MAX_FILE_SIZE': 10 * 1024 * 1024,      # 10MB default
    'MAX_IMAGE_SIZE': 5 * 1024 * 1024,       # 5MB for images
    'MAX_VIDEO_SIZE': 50 * 1024 * 1024,      # 50MB for videos
    'THUMBNAIL_SIZES': [(150, 150), (300, 200), (600, 400)],
    'IMAGE_QUALITY': 85,
    'OPTIMIZE_IMAGES': True,
}
```

### Future Enhancements

- Video processing and thumbnail generation
- Cloud storage integration (AWS S3, Google Cloud)
- Image filters and effects
- Batch image resizing
- CDN integration
- Advanced metadata extraction
- Facial recognition and tagging
- Duplicate detection and removal