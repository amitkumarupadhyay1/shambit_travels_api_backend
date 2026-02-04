"""
Integration examples for the media library system
These examples show how to integrate media with existing models
"""

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from .services.media_service import MediaService
from .utils import MediaProcessor, MediaUtils, MediaValidator


# Example 1: Integration with article creation
def article_media_integration_example():
    """
    Example of integrating media with article creation
    """
    from articles.models import Article
    from cities.models import City

    def create_article_with_images(title, content, city_id, image_files):
        # Create the article
        city = City.objects.get(id=city_id)
        article = Article.objects.create(
            title=title, content=content, city=city, status="PUBLISHED"
        )

        # Process and attach images
        uploaded_media = []
        for i, image_file in enumerate(image_files):
            try:
                # Validate the file
                validator = MediaValidator()
                validator.validate_file(image_file)

                # Create media object
                media = MediaService.create_media(
                    file=image_file,
                    title=f"{article.title} - Image {i+1}",
                    alt_text=f"Image for article: {article.title}",
                    content_type="articles.article",
                    object_id=article.id,
                )

                # Process the image (optimize, generate thumbnails)
                processor = MediaProcessor()
                processor.process_media(media)

                uploaded_media.append(media)

            except Exception as e:
                print(f"Error processing image {i+1}: {e}")

        return article, uploaded_media


# Example 2: City gallery management
def city_gallery_example():
    """
    Example of managing a city's image gallery
    """
    from cities.models import City

    def add_city_gallery_images(city_id, image_files):
        city = City.objects.get(id=city_id)

        # Get existing media count for numbering
        existing_media = MediaService.get_media_for_object("cities.city", city_id)
        start_number = len(existing_media) + 1

        gallery_media = []
        for i, image_file in enumerate(image_files):
            media = MediaService.create_media(
                file=image_file,
                title=f"{city.name} Gallery Image {start_number + i}",
                alt_text=f"Beautiful view of {city.name}",
                content_type="cities.city",
                object_id=city.id,
            )

            # Generate multiple thumbnail sizes for gallery
            processor = MediaProcessor()
            processor.generate_thumbnail(media, 150, 150)  # Small thumbnail
            processor.generate_thumbnail(media, 300, 200)  # Medium thumbnail
            processor.generate_thumbnail(media, 600, 400)  # Large thumbnail

            gallery_media.append(media)

        return gallery_media

    def get_city_gallery(city_id, thumbnail_size="300x200"):
        """Get city gallery with thumbnails"""
        media_files = MediaService.get_media_for_object("cities.city", city_id)

        gallery = []
        for media in media_files:
            if MediaUtils.is_image_file(media.file.name):
                processor = MediaProcessor()
                width, height = map(int, thumbnail_size.split("x"))
                thumbnail_url = processor.generate_thumbnail(media, width, height)

                gallery.append(
                    {
                        "id": media.id,
                        "title": media.title,
                        "alt_text": media.alt_text,
                        "original_url": media.file.url,
                        "thumbnail_url": thumbnail_url,
                        "file_size": media.file.size,
                        "created_at": media.created_at,
                    }
                )

        return gallery


# Example 3: Package media management
def package_media_example():
    """
    Example of managing package media (images, brochures, videos)
    """
    from packages.models import Package

    def create_package_media_set(package_id, media_files):
        package = Package.objects.get(id=package_id)

        media_by_type = {"images": [], "videos": [], "documents": []}

        for media_file in media_files:
            # Determine file type
            if MediaUtils.is_image_file(media_file.name):
                file_type = "images"
                title_prefix = f"{package.name} - Photo"
            elif MediaUtils.is_video_file(media_file.name):
                file_type = "videos"
                title_prefix = f"{package.name} - Video"
            else:
                file_type = "documents"
                title_prefix = f"{package.name} - Document"

            # Create media
            media = MediaService.create_media(
                file=media_file,
                title=f"{title_prefix} - {media_file.name}",
                alt_text=f"Media for {package.name} package",
                content_type="packages.package",
                object_id=package.id,
            )

            # Process based on type
            if file_type == "images":
                processor = MediaProcessor()
                processor.process_media(media)  # Optimize images
                processor.generate_thumbnail(media, 300, 200)  # Package thumbnail

            media_by_type[file_type].append(media)

        return media_by_type


# Example 4: Bulk media operations
def bulk_media_operations_example():
    """
    Example of bulk media operations for content management
    """

    def bulk_optimize_city_images(city_id):
        """Optimize all images for a specific city"""
        media_files = MediaService.get_media_for_object("cities.city", city_id)

        processor = MediaProcessor()
        optimization_results = []

        for media in media_files:
            if MediaUtils.is_image_file(media.file.name):
                result = processor.optimize_media(media)
                optimization_results.append(
                    {
                        "media_id": media.id,
                        "filename": media.file.name,
                        "result": result,
                    }
                )

        return optimization_results

    def bulk_update_alt_text(content_type, object_id, alt_text_template):
        """Update alt text for all media of an object"""
        media_files = MediaService.get_media_for_object(content_type, object_id)

        updated_count = 0
        for i, media in enumerate(media_files):
            media.alt_text = alt_text_template.format(
                index=i + 1, filename=media.file.name, title=media.title
            )
            media.save()
            updated_count += 1

        return updated_count


# Example 5: Media search and filtering
def media_search_example():
    """
    Example of advanced media search and filtering
    """

    def search_travel_images(query, city_name=None, date_from=None):
        """Search for travel-related images"""
        search_params = {"query": query, "file_type": "image"}

        if city_name:
            # Find city and add to search
            from cities.models import City

            try:
                city = City.objects.get(name__icontains=city_name)
                search_params["content_type"] = "cities.city"
                # Note: This would need to be extended to search by object_id
            except City.DoesNotExist:
                pass

        if date_from:
            search_params["date_from"] = date_from

        return MediaService.search_media(search_params)

    def get_recent_uploads_by_type(days=7):
        """Get recent uploads grouped by content type"""
        from datetime import timedelta

        from django.utils import timezone

        recent_date = timezone.now() - timedelta(days=days)

        # This would need to be implemented in the service
        from media_library.models import Media

        recent_media = Media.objects.filter(created_at__gte=recent_date)

        by_content_type = {}
        for media in recent_media:
            ct_key = f"{media.content_type.app_label}.{media.content_type.model}"
            if ct_key not in by_content_type:
                by_content_type[ct_key] = []
            by_content_type[ct_key].append(media)

        return by_content_type


# Example 6: API integration for frontend
def frontend_api_integration_example():
    """
    Example of using media API endpoints from frontend
    """
    import requests

    def upload_article_images(article_id, image_files, auth_token):
        """Upload multiple images for an article"""
        files = []
        for image_file in image_files:
            files.append(("files", image_file))

        data = {"content_type": "articles.article", "object_id": article_id}

        response = requests.post(
            "/api/media/bulk_upload/",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        return response.json()

    def get_city_gallery_api(city_id):
        """Get city gallery through API"""
        response = requests.get(
            "/api/media/for_object/",
            params={"content_type": "cities.city", "object_id": city_id},
        )

        if response.status_code == 200:
            media_files = response.json()

            # Add thumbnail URLs
            for media in media_files:
                if media["file_type"] == "image":
                    media["thumbnail_url"] = (
                        f"/api/media/{media['id']}/thumbnail/?size=300x200"
                    )

            return media_files

        return []

    def search_media_api(query, filters=None):
        """Search media through API"""
        search_data = {"query": query}
        if filters:
            search_data.update(filters)

        response = requests.post(
            "/api/media/search/",
            json=search_data,
            headers={"Content-Type": "application/json"},
        )

        return response.json() if response.status_code == 200 else []


# Example 7: Template integration
def template_integration_example():
    """
    Example of using media in Django templates
    """
    from cities.models import City
    from django.shortcuts import get_object_or_404, render

    def city_detail_view(request, slug):
        city = get_object_or_404(City, slug=slug)

        # Get city media
        city_media = MediaService.get_media_for_object("cities.city", city.id)

        # Separate by type
        images = [m for m in city_media if MediaUtils.is_image_file(m.file.name)]
        videos = [m for m in city_media if MediaUtils.is_video_file(m.file.name)]
        documents = [m for m in city_media if m.file.name.lower().endswith(".pdf")]

        # Generate thumbnails for images
        processor = MediaProcessor()
        for image in images:
            image.thumbnail_url = processor.generate_thumbnail(image, 300, 200)

        return render(
            request,
            "cities/detail.html",
            {"city": city, "images": images, "videos": videos, "documents": documents},
        )


# Example 8: Media cleanup and maintenance
def media_maintenance_example():
    """
    Example of media maintenance tasks
    """

    def daily_media_maintenance():
        """Daily maintenance tasks"""
        from datetime import timedelta

        from django.utils import timezone

        # Clean up orphaned media older than 7 days
        week_ago = timezone.now() - timedelta(days=7)

        from media_library.models import Media

        orphaned_media = []

        for media in Media.objects.filter(created_at__lt=week_ago):
            try:
                if not media.content_object:
                    orphaned_media.append(media)
            except:
                orphaned_media.append(media)

        deleted_count = 0
        for media in orphaned_media:
            try:
                if media.file:
                    media.file.delete()
                media.delete()
                deleted_count += 1
            except:
                pass

        print(f"Cleaned up {deleted_count} orphaned media files")

        # Generate missing thumbnails
        images_without_thumbnails = Media.objects.filter(
            file__iregex=r"\.(jpg|jpeg|png|gif|webp)$"
        )

        processor = MediaProcessor()
        thumbnail_count = 0

        for media in images_without_thumbnails:
            thumbnail_url = processor.generate_thumbnail(media, 300, 200)
            if thumbnail_url:
                thumbnail_count += 1

        print(f"Generated {thumbnail_count} missing thumbnails")

    def weekly_storage_report():
        """Generate weekly storage report"""
        stats = MediaService.get_media_stats()
        storage_info = MediaService.get_storage_info()

        report = f"""
        Weekly Media Storage Report
        ==========================
        
        Total Files: {stats['total_files']}
        Total Size: {MediaUtils.format_file_size(stats['total_size'])}
        
        File Types:
        - Images: {stats['by_type']['images']}
        - Videos: {stats['by_type']['videos']}
        - Documents: {stats['by_type']['documents']}
        - Other: {stats['by_type']['other']}
        
        Recent Uploads (7 days): {stats['recent_uploads']}
        
        Storage Usage:
        - Files in Storage: {storage_info.get('total_files', 'N/A')}
        - Storage Size: {MediaUtils.format_file_size(storage_info.get('total_size', 0))}
        """

        if storage_info.get("disk_usage_percentage"):
            report += f"- Disk Usage: {storage_info['disk_usage_percentage']:.1f}%\n"

        return report


if __name__ == "__main__":
    # These are just examples - don't run directly
    print("Media library integration examples")
    print("See the functions above for implementation details")
