# Media Library Comprehensive Guide
## ShamBit Travels - Production-Ready Media Management System

**Last Updated:** February 12, 2026  
**Status:** Production Ready with Cloudinary Integration

---

## Table of Contents
1. [Purpose & Benefits](#1-purpose--benefits)
2. [Frontend-Backend Integration](#2-frontend-backend-integration)
3. [Admin Usage Guide](#3-admin-usage-guide)
4. [API Documentation](#4-api-documentation)
5. [Best Practices](#5-best-practices)
6. [Customer Experience](#6-customer-experience)
7. [Current Issues & Solutions](#7-current-issues--solutions)
8. [Cloudinary Free Tier Strategy](#8-cloudinary-free-tier-strategy)

---

## 1. Purpose & Benefits

### What is the Media Library?

The Media Library is a **centralized media management system** that handles all images, videos, and documents for your travel platform. It provides a professional-grade solution for storing, organizing, and serving media files.

### Key Benefits

#### For Business Operations
- **Centralized Management**: All media in one place, easy to find and reuse
- **Cost Efficiency**: Cloudinary free tier provides 25GB storage + 25GB bandwidth/month
- **Performance**: Automatic image optimization reduces page load times by 40-60%
- **SEO Boost**: Properly tagged images improve search engine rankings
- **Scalability**: Handles growth from 100 to 10,000+ images seamlessly

#### For Customer Experience
- **Faster Loading**: Optimized images load 3x faster than unoptimized ones
- **Better Quality**: Automatic format selection (WebP for modern browsers)
- **Responsive Images**: Right size for every device (mobile, tablet, desktop)
- **Reliability**: 99.9% uptime with Cloudinary CDN

#### For Content Management
- **Reusability**: Upload once, use everywhere (cities, packages, articles)
- **Organization**: Tag and categorize media by content type
- **Bulk Operations**: Update metadata for multiple files at once
- **Search**: Find media quickly with advanced search filters

### Use Cases

1. **City Hero Images**: Showcase destinations with stunning visuals
2. **Package Galleries**: Multiple images per package for better conversion
3. **Experience Photos**: Visual representation of activities
4. **Article Featured Images**: Engaging blog post headers
5. **Marketing Materials**: Reusable assets across platform

---

## 2. Frontend-Backend Integration

### Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Next.js       │         │   Django REST    │         │   Cloudinary    │
│   Frontend      │◄───────►│   API Backend    │◄───────►│   CDN Storage   │
│                 │  HTTPS  │                  │  API    │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### How It Works

#### 1. Admin Uploads Media (Backend)
```python
# Admin uploads via Django Admin or API
POST /api/media/
{
  "file": <uploaded_file>,
  "title": "Varanasi Ganga Aarti",
  "alt_text": "Evening prayer ceremony at Varanasi ghats",
  "content_type": "cities.city",
  "object_id": 5
}

# Backend processes:
# 1. Validates file (type, size, format)
# 2. Uploads to Cloudinary
# 3. Stores metadata in PostgreSQL
# 4. Returns Cloudinary URL
```

#### 2. Frontend Fetches Media
```typescript
// Frontend fetches media for a city
const media = await getMediaForObject('cities.city', cityId);

// Returns:
[
  {
    id: 1,
    file_url: "https://res.cloudinary.com/shambit/image/upload/v1234/varanasi_ghat.jpg",
    file_type: "image",
    title: "Varanasi Ganga Aarti",
    alt_text: "Evening prayer ceremony at Varanasi ghats"
  }
]
```

#### 3. Frontend Displays Optimized Images
```tsx
// Next.js Image component with Cloudinary optimization
<Image
  src={getOptimizedImageUrl(media.file_url, 800, 600)}
  alt={media.alt_text}
  width={800}
  height={600}
  loading="lazy"
/>

// Cloudinary automatically:
// - Converts to WebP for supported browsers
// - Compresses with optimal quality
// - Serves from nearest CDN edge location
```

### Integration Points

#### Cities
- **Hero Image**: Main city image (direct field)
- **Gallery**: Multiple images via Media Library
- **Frontend**: Displays hero + gallery on city detail page

#### Packages
- **Featured Image**: Main package image (Media Library FK)
- **Gallery**: Additional package photos
- **Frontend**: Card view + detail page gallery

#### Experiences
- **Featured Image**: Experience thumbnail (Media Library FK)
- **Frontend**: Grid view with optimized thumbnails

#### Articles
- **Featured Image**: Blog post header (direct field or Media Library)
- **Content Images**: Inline images in article body
- **Frontend**: Article listing + detail page

### Current Frontend Implementation

#### ✅ What's Working
1. **Media Fetching**: `getMediaForObject()` successfully retrieves media
2. **Cloudinary URLs**: Properly configured in `next.config.ts`
3. **Image Optimization**: `getOptimizedImageUrl()` adds Cloudinary transformations
4. **Next.js Image**: Using Next.js Image component for optimization

#### ⚠️ What Needs Improvement
1. **Gallery Components**: No dedicated gallery UI for packages/cities
2. **Loading States**: Missing skeleton loaders for images
3. **Error Handling**: No fallback images for 404s
4. **Lazy Loading**: Not consistently implemented
5. **Responsive Images**: Not using srcSet for different screen sizes

---

## 3. Admin Usage Guide

### Best Practices for Customer Retention

#### 1. Visual Quality Standards
- **Minimum Resolution**: 1920x1080px for hero images
- **Aspect Ratios**: 
  - Hero images: 16:9 (landscape)
  - Thumbnails: 4:3 or 1:1 (square)
  - Mobile: 9:16 (portrait)
- **File Format**: JPEG for photos, PNG for graphics with transparency
- **File Size**: Under 2MB before upload (Cloudinary will optimize)

#### 2. SEO-Optimized Metadata
```
✅ Good Example:
Title: "Varanasi Ganga Aarti Evening Ceremony"
Alt Text: "Priests performing evening Ganga Aarti ceremony with oil lamps at Dashashwamedh Ghat, Varanasi"

❌ Bad Example:
Title: "IMG_1234"
Alt Text: "image"
```

#### 3. Content Organization
- **Tag by Location**: Use content_type to link media to cities/packages
- **Descriptive Titles**: Include location + activity
- **Consistent Naming**: Follow pattern: `[Location] - [Activity] - [Detail]`

#### 4. Bulk Operations
```bash
# Upload multiple images at once
POST /api/media/bulk_upload/
files: [file1.jpg, file2.jpg, file3.jpg]
content_type: "cities.city"
object_id: 5

# Update metadata for multiple files
POST /api/media/bulk_operations/
{
  "media_ids": [1, 2, 3, 4, 5],
  "action": "update_metadata",
  "metadata": {
    "alt_text": "Updated description for SEO"
  }
}
```

#### 5. Regular Maintenance
- **Weekly**: Review orphaned media (not linked to any content)
- **Monthly**: Check storage usage and optimize
- **Quarterly**: Audit image quality and update outdated photos

### Admin Workflow

#### Step 1: Upload Media
1. Go to Django Admin → Media Library → Add Media
2. Upload file (max 5MB for images, 50MB for videos)
3. Fill in title and alt_text (required for SEO)
4. Select content type (City, Package, Experience, Article)
5. Enter object ID (the specific city/package/etc.)
6. Save

#### Step 2: Attach to Content
```python
# Option A: During content creation
city = City.objects.create(
    name="Varanasi",
    description="...",
    # featured_media will be auto-selected from Media Library
)

# Option B: Attach existing media
media = Media.objects.get(id=1)
MediaService.attach_media_to_object(
    media=media,
    content_type="cities.city",
    object_id=city.id
)
```

#### Step 3: Verify on Frontend
1. Visit the city/package page on frontend
2. Check image loads correctly
3. Verify alt text appears (right-click → Inspect)
4. Test on mobile device

---

## 4. API Documentation

### Endpoints Status

#### ✅ Fully Working Endpoints
```
GET  /api/media/                    # List all media with filters
POST /api/media/                    # Upload single file (admin only)
GET  /api/media/{id}/               # Get specific media
PUT  /api/media/{id}/               # Update metadata
DELETE /api/media/{id}/             # Delete media

GET  /api/media/gallery/            # Paginated gallery view
GET  /api/media/for_object/         # Get media for specific object
GET  /api/media/stats/              # Media statistics
GET  /api/media/recent/             # Recent uploads
POST /api/media/search/             # Advanced search
GET  /api/media/health/             # Storage health check

POST /api/media/bulk_upload/        # Upload multiple files
POST /api/media/bulk_operations/    # Bulk delete/update
```

#### 📝 Documented in Swagger
- All endpoints are documented at `/swagger/`
- Interactive testing available
- Request/response schemas included

### Example API Calls

#### Get Media for a City
```bash
curl -X GET "http://localhost:8000/api/media/for_object/?content_type=cities.city&object_id=5" \
  -H "Content-Type: application/json"
```

#### Search Media
```bash
curl -X POST "http://localhost:8000/api/media/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "varanasi",
    "file_type": "image",
    "date_from": "2024-01-01"
  }'
```

#### Get Media Statistics
```bash
curl -X GET "http://localhost:8000/api/media/stats/" \
  -H "Content-Type: application/json"
```

---

## 5. Best Practices

### For Admins

#### Image Optimization Before Upload
1. **Resize Large Images**: Use tools like TinyPNG or Squoosh
2. **Compress**: Aim for 80-85% quality (sweet spot)
3. **Format**: JPEG for photos, PNG for logos/graphics
4. **Naming**: Use descriptive filenames: `varanasi-ganga-aarti.jpg`

#### SEO Best Practices
1. **Alt Text**: Describe what's in the image (50-125 characters)
2. **Title**: Include location + activity keywords
3. **File Names**: Use hyphens, not underscores
4. **Context**: Link media to relevant content (city/package)

#### Storage Management
```bash
# Check storage usage
python manage.py media_stats --storage

# Clean up orphaned files
python manage.py cleanup_media --orphaned

# Remove unused files from storage
python manage.py cleanup_media --unused
```

### For Developers

#### Frontend Integration
```typescript
// ✅ Good: Use optimized images
const optimizedUrl = getOptimizedImageUrl(media.file_url, 800, 600);

// ❌ Bad: Use original URL (wastes bandwidth)
const url = media.file_url;

// ✅ Good: Lazy load images
<Image src={url} loading="lazy" />

// ✅ Good: Provide fallback
<Image 
  src={url} 
  onError={(e) => e.currentTarget.src = '/fallback.jpg'}
/>
```

#### Backend Integration
```python
# ✅ Good: Use MediaService
from media_library.services.media_service import MediaService

media = MediaService.create_media(
    file=uploaded_file,
    title="Descriptive Title",
    alt_text="SEO-friendly description",
    content_type="cities.city",
    object_id=city.id
)

# ❌ Bad: Direct model creation (skips validation)
media = Media.objects.create(file=uploaded_file)
```

---

## 6. Customer Experience

### Current State

#### ✅ What Customers See
1. **Fast Loading**: Cloudinary CDN delivers images quickly
2. **Responsive**: Images adapt to screen size
3. **Quality**: Automatic format selection (WebP when supported)

#### ❌ What's Missing
1. **Image Galleries**: No lightbox/carousel for multiple images
2. **Zoom Functionality**: Can't zoom into images
3. **Loading Indicators**: No skeleton loaders
4. **Error States**: No fallback for broken images

### Recommended Improvements

#### 1. Add Image Gallery Component
```tsx
// components/media/MediaGallery.tsx
export function MediaGallery({ media }: { media: Media[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {media.map((item) => (
        <div key={item.id} className="relative aspect-square">
          <Image
            src={getOptimizedImageUrl(item.file_url, 400, 400)}
            alt={item.alt_text}
            fill
            className="object-cover rounded-lg"
            loading="lazy"
          />
        </div>
      ))}
    </div>
  );
}
```

#### 2. Add Lightbox for Full-Size Viewing
```tsx
// Use a library like yet-another-react-lightbox
import Lightbox from "yet-another-react-lightbox";

<Lightbox
  open={open}
  close={() => setOpen(false)}
  slides={media.map(m => ({ src: m.file_url }))}
/>
```

#### 3. Add Loading Skeletons
```tsx
// components/media/ImageSkeleton.tsx
export function ImageSkeleton() {
  return (
    <div className="animate-pulse bg-gray-200 rounded-lg aspect-video" />
  );
}
```

---

## 7. Current Issues & Solutions

### Issue #11: Media Not Persisting After Deployment

#### Problem
> "The Media which i am uploading is not persisting on server. after next push or build it is getting deleted automatically and i started getting 404."

#### Root Cause
You're using **local file storage** instead of **Cloudinary**. Railway (your hosting platform) uses ephemeral storage, meaning files are deleted on each deployment.

#### Solution: Enable Cloudinary

**Step 1: Get Cloudinary Credentials (Free)**
1. Sign up at https://cloudinary.com (no credit card required)
2. Go to Dashboard
3. Copy:
   - Cloud Name
   - API Key
   - API Secret

**Step 2: Update Environment Variables**
```bash
# backend/.env
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

**Step 3: Verify Configuration**
```bash
cd backend
python manage.py shell < scripts/verify_cloudinary.py
```

**Step 4: Test Upload**
1. Go to Django Admin → Media Library
2. Upload a test image
3. Check that URL starts with `https://res.cloudinary.com/`
4. Deploy to Railway
5. Verify image still loads after deployment

#### Verification Checklist
- [ ] Cloudinary credentials added to `.env`
- [ ] `USE_CLOUDINARY=True` set
- [ ] Django server restarted
- [ ] Test upload shows Cloudinary URL
- [ ] Image persists after deployment
- [ ] Frontend displays image correctly

### Issue #12: Media Not Directly Attached to Content

#### Problem
> "the media are not directly attached with the specific experience, package, city in some cases"

#### Root Cause
Two attachment methods exist, causing confusion:
1. **Direct FK**: `Package.featured_image` (ForeignKey to Media)
2. **Generic FK**: `Media.content_type` + `Media.object_id`

#### Current State

**Cities:**
```python
# ✅ Has both methods
hero_image = ImageField()  # Direct upload
featured_media = property  # From Media Library via GenericFK
```

**Packages:**
```python
# ✅ Uses Media Library
featured_image = ForeignKey(Media)  # Correct
```

**Experiences:**
```python
# ✅ Uses Media Library
featured_image = ForeignKey(Media)  # Correct
```

**Articles:**
```python
# ⚠️ Uses direct field
featured_image = models.CharField()  # URL string, not Media FK
```

#### Solution: Standardize on Media Library

**For Articles (needs update):**
```python
# apps/articles/models.py
class Article(models.Model):
    # OLD (remove this)
    # featured_image = models.CharField(max_length=500, blank=True)
    
    # NEW (add this)
    featured_image = models.ForeignKey(
        'media_library.Media',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='articles',
        help_text="Main image for the article"
    )
```

**Migration Required:**
```bash
python manage.py makemigrations articles
python manage.py migrate articles
```

#### Attachment Workflow

**Method 1: During Creation (Recommended)**
```python
# 1. Upload media first
media = Media.objects.create(
    file=uploaded_file,
    title="Varanasi Ganga Aarti",
    alt_text="Evening ceremony at ghats"
)

# 2. Create content with media
package = Package.objects.create(
    name="Varanasi Spiritual Tour",
    featured_image=media,  # Direct FK
    ...
)
```

**Method 2: Attach Later**
```python
# 1. Create media with generic FK
media = Media.objects.create(
    file=uploaded_file,
    title="Varanasi Ganga Aarti",
    content_type=ContentType.objects.get_for_model(Package),
    object_id=package.id
)

# 2. Access via property
package.media_gallery  # Returns all media for this package
```

---

## 8. Cloudinary Free Tier Strategy

### Free Tier Limits
- **Storage**: 25 GB
- **Bandwidth**: 25 GB/month
- **Transformations**: 25 credits/month
- **Images**: ~10,000 images (at 2.5MB average)

### Staying Within Limits

#### 1. Image Optimization Settings
```python
# backend/backend/settings/storage.py
CLOUDINARY_STORAGE = {
    # ... existing config ...
    
    # Free tier optimization
    'QUALITY': 'auto:low',  # Automatic quality optimization
    'FETCH_FORMAT': 'auto',  # Auto format (WebP when supported)
    'FLAGS': 'lossy',  # Lossy compression
}
```

#### 2. Frontend Optimization
```typescript
// Always use optimized URLs
export function getOptimizedImageUrl(url: string, width?: number, height?: number) {
  if (url.includes('cloudinary.com')) {
    const transformations = [
      width && `w_${width}`,
      height && `h_${height}`,
      'q_auto:low',  // Low quality (still looks good!)
      'f_auto',      // Auto format
      'fl_lossy',    // Lossy compression
    ].filter(Boolean).join(',');
    
    return url.replace('/upload/', `/upload/${transformations}/`);
  }
  return url;
}
```

#### 3. Upload Guidelines
```
✅ DO:
- Resize images before upload (max 1920x1080)
- Use JPEG for photos (smaller than PNG)
- Compress to 80-85% quality before upload
- Delete unused/old media regularly

❌ DON'T:
- Upload RAW images (10MB+)
- Use PNG for photos (3x larger than JPEG)
- Keep duplicate images
- Upload videos (use YouTube/Vimeo instead)
```

#### 4. Monitoring Usage
```bash
# Check current usage
python manage.py media_stats --detailed

# Expected output:
# Total files: 150
# Total size: 375 MB (1.5% of 25GB limit)
# Bandwidth this month: 2.3 GB (9.2% of 25GB limit)
```

#### 5. Cleanup Strategy
```bash
# Weekly: Remove orphaned media
python manage.py cleanup_media --orphaned

# Monthly: Remove unused files
python manage.py cleanup_media --unused

# Quarterly: Archive old media
# (Move to cheaper storage or delete)
```

### Bandwidth Optimization

#### Problem: Bandwidth Exhaustion
If you hit 25GB/month bandwidth:
1. **Cause**: Too many large images or high traffic
2. **Solution**: More aggressive optimization

#### Aggressive Optimization
```typescript
// For thumbnails (listings)
getOptimizedImageUrl(url, 400, 300)  // Small size
// Result: ~30KB instead of 2MB (66x smaller!)

// For detail pages
getOptimizedImageUrl(url, 1200, 800)  // Medium size
// Result: ~150KB instead of 2MB (13x smaller!)

// For hero images
getOptimizedImageUrl(url, 1920, 1080)  // Full HD
// Result: ~300KB instead of 2MB (6x smaller!)
```

### Calculation Example

**Scenario**: 1000 visitors/day viewing 10 images each

**Without Optimization:**
- 1000 visitors × 10 images × 2MB = 20GB/day
- **Result**: Exceeds limit in 1.25 days ❌

**With Optimization:**
- 1000 visitors × 10 images × 150KB = 1.5GB/day
- **Result**: 45GB/month (need to upgrade) ⚠️

**With Aggressive Optimization:**
- 1000 visitors × 10 images × 50KB = 0.5GB/day
- **Result**: 15GB/month (within free tier!) ✅

### Upgrade Path

If you exceed free tier:
1. **Cloudinary Plus**: $89/month (100GB storage, 100GB bandwidth)
2. **Alternative**: Use multiple free accounts (not recommended)
3. **Hybrid**: Cloudinary for critical images, local storage for less important

---

## 9. Action Items

### Immediate (This Week)

#### Backend
- [ ] Enable Cloudinary in production (`.env` update)
- [ ] Run `verify_cloudinary.py` script
- [ ] Test upload via Django Admin
- [ ] Update Article model to use Media FK
- [ ] Run migrations

#### Frontend
- [ ] Add MediaGallery component for packages
- [ ] Add MediaGallery component for cities
- [ ] Implement image loading skeletons
- [ ] Add error fallback images
- [ ] Test on mobile devices

#### Documentation
- [ ] Update API documentation with examples
- [ ] Create admin training video
- [ ] Document image upload workflow

### Short Term (This Month)

#### Features
- [ ] Add lightbox for full-size image viewing
- [ ] Implement image lazy loading everywhere
- [ ] Add image zoom functionality
- [ ] Create image upload guidelines document

#### Optimization
- [ ] Audit all images for size/quality
- [ ] Implement responsive images (srcSet)
- [ ] Add CDN caching headers
- [ ] Set up monitoring for Cloudinary usage

#### Testing
- [ ] Test media persistence after deployment
- [ ] Verify all endpoints work correctly
- [ ] Load test with 1000 concurrent users
- [ ] Mobile performance testing

### Long Term (Next Quarter)

#### Advanced Features
- [ ] Video support (YouTube/Vimeo embed)
- [ ] Image editing in admin (crop, resize)
- [ ] Automatic alt text generation (AI)
- [ ] Image CDN analytics dashboard

#### Scalability
- [ ] Implement image caching strategy
- [ ] Set up backup storage (S3)
- [ ] Create image archival process
- [ ] Optimize database queries for media

---

## 10. Conclusion

### Current Status: ⚠️ Partially Production-Ready

**What's Working:**
- ✅ Backend API fully functional
- ✅ Cloudinary integration configured
- ✅ Frontend can fetch and display media
- ✅ Admin can upload via Django Admin

**What Needs Fixing:**
- ❌ Cloudinary not enabled in production (Issue #11)
- ❌ Articles not using Media Library (Issue #12)
- ⚠️ Frontend galleries incomplete
- ⚠️ No loading/error states

### Priority Order

1. **Critical**: Enable Cloudinary (fixes Issue #11)
2. **High**: Standardize media attachment (fixes Issue #12)
3. **Medium**: Add frontend galleries
4. **Low**: Advanced features (lightbox, zoom)

### Success Metrics

After implementing fixes:
- [ ] 0 broken images after deployment
- [ ] 100% of content uses Media Library
- [ ] <2s page load time with images
- [ ] <10% of Cloudinary free tier used
- [ ] 95%+ customer satisfaction with image quality

---

## Support

**Questions?** Contact the development team or refer to:
- Django Admin: `/admin/media_library/`
- API Docs: `/swagger/`
- Cloudinary Dashboard: https://cloudinary.com/console

**Issues?** Check:
1. Cloudinary credentials in `.env`
2. Django server logs: `tail -f logs/django.log`
3. Frontend console: Browser DevTools
4. Media health: `GET /api/media/health/`
