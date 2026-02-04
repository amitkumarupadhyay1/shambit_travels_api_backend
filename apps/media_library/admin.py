import os

from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Media
from .services.media_service import MediaService
from .utils import MediaUtils


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = [
        "thumbnail_preview",
        "title_with_filename",
        "file_type_badge",
        "file_size_display",
        "content_object_link",
        "created_at",
    ]
    list_filter = ["content_type", "created_at"]
    search_fields = ["title", "alt_text", "file"]
    readonly_fields = ["created_at", "file_info_display", "file_preview"]
    list_per_page = 50

    fieldsets = (
        ("Media File", {"fields": ("file", "file_preview", "file_info_display")}),
        ("Media Info", {"fields": ("title", "alt_text")}),
        (
            "Attachment",
            {
                "fields": ("content_type", "object_id"),
                "description": "Attach this media to a specific object",
            },
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    actions = ["optimize_images", "generate_thumbnails", "update_metadata"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "media-dashboard/",
                self.admin_site.admin_view(self.media_dashboard_view),
                name="media_dashboard",
            ),
            path(
                "cleanup-media/",
                self.admin_site.admin_view(self.cleanup_media_view),
                name="media_cleanup",
            ),
        ]
        return custom_urls + urls

    def thumbnail_preview(self, obj):
        """Show thumbnail preview for images"""
        if obj.file and MediaUtils.is_image_file(obj.file.name):
            try:
                return format_html(
                    '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                    obj.file.url,
                )
            except (ValueError, AttributeError):
                pass

        # Show file type icon for non-images
        icon = MediaUtils.get_file_type_icon(obj.file.name if obj.file else "")
        return format_html(
            '<div style="width: 50px; height: 50px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-size: 20px;">📄</div>'
        )

    thumbnail_preview.short_description = "Preview"

    def title_with_filename(self, obj):
        """Show title with filename"""
        title = obj.title or "Untitled"
        filename = os.path.basename(obj.file.name) if obj.file else "No file"

        return format_html(
            '<strong>{}</strong><br><small style="color: #666;">{}</small>',
            title,
            filename,
        )

    title_with_filename.short_description = "Title / Filename"

    def file_type_badge(self, obj):
        """Show file type with colored badge"""
        if not obj.file:
            return format_html('<span style="color: red;">No file</span>')

        extension = os.path.splitext(obj.file.name)[1].lower()

        if extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            color = "#28a745"  # Green
            type_name = "Image"
        elif extension in [".mp4", ".avi", ".mov", ".wmv", ".flv"]:
            color = "#007bff"  # Blue
            type_name = "Video"
        elif extension in [".pdf"]:
            color = "#dc3545"  # Red
            type_name = "Document"
        else:
            color = "#6c757d"  # Gray
            type_name = "Other"

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            type_name,
        )

    file_type_badge.short_description = "Type"

    def file_size_display(self, obj):
        """Show formatted file size"""
        if obj.file:
            try:
                size = obj.file.size
                return MediaUtils.format_file_size(size)
            except (OSError, ValueError):
                return "Unknown"
        return "No file"

    file_size_display.short_description = "Size"

    def content_object_link(self, obj):
        """Show link to the content object"""
        if obj.content_object:
            try:
                url = reverse(
                    f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change",
                    args=[obj.object_id],
                )
                return format_html(
                    '<a href="{}" target="_blank">{}</a><br><small>{}</small>',
                    url,
                    str(obj.content_object),
                    f"{obj.content_type.app_label}.{obj.content_type.model}",
                )
            except:
                return format_html(
                    "{}<br><small>{}</small>",
                    str(obj.content_object),
                    f"{obj.content_type.app_label}.{obj.content_type.model}",
                )
        return format_html('<span style="color: #999;">Not attached</span>')

    content_object_link.short_description = "Attached To"

    def file_info_display(self, obj):
        """Show detailed file information"""
        if not obj.file:
            return "No file uploaded"

        try:
            file_size = MediaUtils.format_file_size(obj.file.size)
            file_path = obj.file.path

            info_html = f"""
            <div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">
                <p><strong>File:</strong> {os.path.basename(obj.file.name)}</p>
                <p><strong>Size:</strong> {file_size}</p>
                <p><strong>Path:</strong> <code>{file_path}</code></p>
            """

            # Add image-specific info
            if MediaUtils.is_image_file(obj.file.name):
                image_info = MediaUtils.get_image_info(file_path)
                if image_info:
                    info_html += f"""
                    <p><strong>Dimensions:</strong> {image_info['width']} × {image_info['height']}</p>
                    <p><strong>Format:</strong> {image_info['format']}</p>
                    <p><strong>Mode:</strong> {image_info['mode']}</p>
                    """

            info_html += "</div>"
            return format_html(info_html)

        except (OSError, ValueError, AttributeError):
            return "File information unavailable"

    file_info_display.short_description = "File Information"

    def file_preview(self, obj):
        """Show file preview"""
        if not obj.file:
            return "No file to preview"

        if MediaUtils.is_image_file(obj.file.name):
            try:
                return format_html(
                    '<img src="{}" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;">',
                    obj.file.url,
                )
            except (ValueError, AttributeError):
                return "Image preview unavailable"
        else:
            return format_html(
                "<p>Preview not available for this file type.</p>"
                '<p><a href="{}" target="_blank">Download file</a></p>',
                obj.file.url if obj.file else "#",
            )

    file_preview.short_description = "Preview"

    def optimize_images(self, request, queryset):
        """Optimize selected image files"""
        from .utils import MediaProcessor

        processor = MediaProcessor()
        optimized_count = 0

        for media in queryset:
            if media.file and MediaUtils.is_image_file(media.file.name):
                result = processor.optimize_media(media)
                if result["success"]:
                    optimized_count += 1

        self.message_user(
            request, f"Optimized {optimized_count} image files.", messages.SUCCESS
        )

    optimize_images.short_description = "Optimize selected images"

    def generate_thumbnails(self, request, queryset):
        """Generate thumbnails for selected images"""
        from .utils import MediaProcessor

        processor = MediaProcessor()
        generated_count = 0

        for media in queryset:
            if media.file and MediaUtils.is_image_file(media.file.name):
                thumbnail_path = processor.generate_thumbnail(media)
                if thumbnail_path:
                    generated_count += 1

        self.message_user(
            request,
            f"Generated thumbnails for {generated_count} images.",
            messages.SUCCESS,
        )

    generate_thumbnails.short_description = "Generate thumbnails for selected images"

    def update_metadata(self, request, queryset):
        """Update metadata for selected media files"""
        # This would redirect to a form for bulk metadata update
        selected = queryset.values_list("id", flat=True)
        request.session["selected_media"] = list(selected)
        return redirect("admin:media_bulk_update")

    update_metadata.short_description = "Update metadata for selected files"

    def media_dashboard_view(self, request):
        """Media dashboard view"""
        stats = MediaService.get_media_stats()
        storage_info = MediaService.get_storage_info()

        # Get recent uploads
        from datetime import timedelta

        from django.utils import timezone

        from .models import Media

        recent_date = timezone.now() - timedelta(days=7)
        recent_media = Media.objects.filter(created_at__gte=recent_date).order_by(
            "-created_at"
        )[:10]

        context = {
            "title": "Media Library Dashboard",
            "stats": stats,
            "storage_info": storage_info,
            "recent_media": recent_media,
            "opts": self.model._meta,
        }

        return render(request, "admin/media_library/dashboard.html", context)

    def cleanup_media_view(self, request):
        """Media cleanup view"""
        if request.method == "POST":
            action = request.POST.get("action")

            if action == "cleanup_orphaned":
                deleted_count = MediaService.cleanup_orphaned_media()
                self.message_user(
                    request,
                    f"Deleted {deleted_count} orphaned media files.",
                    messages.SUCCESS,
                )
            elif action == "cleanup_unused":
                result = MediaService.cleanup_unused_files()
                if "error" in result:
                    self.message_user(
                        request, f'Error: {result["error"]}', messages.ERROR
                    )
                else:
                    self.message_user(
                        request,
                        f'Cleaned up {result["unused_files_removed"]} unused files, '
                        f'freed {MediaUtils.format_file_size(result["total_size_freed"])}.',
                        messages.SUCCESS,
                    )

            return redirect("admin:media_library_media_changelist")

        # Get cleanup statistics
        orphaned_count = 0
        from .models import Media

        for media in Media.objects.all():
            try:
                if not media.content_object:
                    orphaned_count += 1
            except:
                orphaned_count += 1

        context = {
            "title": "Media Cleanup",
            "orphaned_count": orphaned_count,
            "opts": self.model._meta,
        }

        return render(request, "admin/media_library/cleanup.html", context)
