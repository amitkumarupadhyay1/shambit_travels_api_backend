import os

from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Media
from .services.media_service import MediaService
from .utils import MediaUtils


class MediaAdminForm(forms.ModelForm):
    """
    Custom form for better admin UX with helpful guidance
    """

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(
            app_label__in=["cities", "articles", "packages"]
        ),
        required=False,
        help_text="Select what type of content this media belongs to (City, Article, or Package)",
        label="Attach to Content Type",
        empty_label="-- Not attached to any content --",
    )

    object_id = forms.IntegerField(
        required=False,
        help_text="Enter the ID of the specific item. Find IDs in the respective admin sections.",
        label="Content ID",
        widget=forms.NumberInput(
            attrs={"placeholder": "Enter ID after selecting content type above"}
        ),
    )

    class Meta:
        model = Media
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add helpful placeholder and help text
        self.fields["title"].help_text = (
            "Descriptive title for this media file (e.g., 'Paris Eiffel Tower View')"
        )
        self.fields["title"].widget.attrs[
            "placeholder"
        ] = "Enter a descriptive title..."

        self.fields["alt_text"].help_text = (
            "Alternative text for accessibility - describes the image for screen readers and SEO"
        )
        self.fields["alt_text"].widget.attrs[
            "placeholder"
        ] = "Describe what's in the image..."

        self.fields["file"].help_text = format_html(
            "<strong>Allowed file types:</strong><br>"
            "📷 <strong>Images:</strong> JPG, PNG, GIF, WebP (max 5MB)<br>"
            "🎥 <strong>Videos:</strong> MP4, MOV, AVI (max 50MB)<br>"
            "📄 <strong>Documents:</strong> PDF (max 10MB)"
        )


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    form = MediaAdminForm
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
    list_select_related = ["content_type"]  # Optimize queries

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

    def get_queryset(self, request):
        """Override to add select_related for performance"""
        qs = super().get_queryset(request)
        return qs.select_related("content_type")

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
        if obj.file:
            try:
                if MediaUtils.is_image_file(obj.file.name):
                    return format_html(
                        '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                        obj.file.url,
                    )
            except (ValueError, AttributeError, Exception):
                # If file URL fails, show error icon
                return format_html(
                    '<div style="width: 50px; height: 50px; background: #ffebee; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-size: 20px; color: #c62828;">⚠️</div>'
                )

        # Show file type icon for non-images or missing files
        return format_html(
            '<div style="width: 50px; height: 50px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-size: 20px;">📄</div>'
        )

    thumbnail_preview.short_description = "Preview"

    def title_with_filename(self, obj):
        """Show title with filename"""
        title = obj.title or "Untitled"

        try:
            filename = os.path.basename(obj.file.name) if obj.file else "No file"
        except Exception:
            filename = "Error loading filename"

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

        try:
            extension = os.path.splitext(obj.file.name)[1].lower()
        except Exception:
            return format_html('<span style="color: red;">Error</span>')

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
            except (OSError, ValueError, Exception):
                return format_html('<span style="color: #f57c00;">Error</span>')
        return "No file"

    file_size_display.short_description = "Size"

    def content_object_link(self, obj):
        """Enhanced display with object name instead of just ID"""
        try:
            if obj.content_object:
                # Get the actual object
                content_obj = obj.content_object
                obj_name = str(content_obj)

                # Try to get admin URL
                try:
                    url = reverse(
                        f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change",
                        args=[obj.object_id],
                    )
                    return format_html(
                        '<div style="line-height: 1.6;">'
                        '<a href="{}" target="_blank" style="font-weight: 600; color: #0066cc; text-decoration: none;">'
                        "📎 {}</a><br>"
                        '<small style="color: #666;">Type: {} | ID: {}</small>'
                        "</div>",
                        url,
                        obj_name,
                        obj.content_type.model.replace("_", " ").title(),
                        obj.object_id,
                    )
                except Exception:
                    return format_html(
                        '<div style="line-height: 1.6;">'
                        '<span style="font-weight: 600;">📎 {}</span><br>'
                        '<small style="color: #666;">Type: {} | ID: {}</small>'
                        "</div>",
                        obj_name,
                        obj.content_type.model.replace("_", " ").title(),
                        obj.object_id,
                    )
            return format_html(
                '<div style="line-height: 1.6;">'
                '<span style="color: #999; font-style: italic;">🔓 Not attached</span><br>'
                '<small style="color: #666;">This media is available but not linked to any content</small>'
                "</div>"
            )
        except Exception as e:
            return format_html(
                '<span style="color: #f57c00;">⚠️ Error loading</span><br>'
                '<small style="color: #666;">{}</small>',
                str(e),
            )

    content_object_link.short_description = "Attached To"

    def file_info_display(self, obj):
        """Enhanced file information with clear labels and helpful explanations"""
        if not obj.file:
            return format_html(
                '<div style="background: #fff3cd; padding: 12px; border-radius: 4px; border-left: 4px solid #ffc107;">'
                "<strong>⚠️ No file uploaded</strong><br>"
                "<small>Upload a file to see its information</small>"
                "</div>"
            )

        try:
            # Basic file info
            file_size = MediaUtils.format_file_size(obj.file.size)
            file_name = os.path.basename(obj.file.name)
            file_extension = os.path.splitext(file_name)[1].upper()

            info_html = f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #dee2e6;">
                <h4 style="margin-top: 0; color: #495057; font-size: 14px;">📄 File Details</h4>
                
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; width: 140px; color: #495057;">File Name:</td>
                        <td style="padding: 8px 0; color: #212529;">{file_name}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">File Type:</td>
                        <td style="padding: 8px 0; color: #212529;">{file_extension} file</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">File Size:</td>
                        <td style="padding: 8px 0; color: #212529;">{file_size}</td>
                    </tr>
            """

            # Storage location
            if "cloudinary" in obj.file.url:
                info_html += f"""
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Storage:</td>
                        <td style="padding: 8px 0;">
                            <span style="background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 3px; font-size: 12px;">
                                ☁️ Cloudinary (Cloud Storage)
                            </span>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Public URL:</td>
                        <td style="padding: 8px 0;">
                            <a href="{obj.file.url}" target="_blank" style="color: #007bff; word-break: break-all; font-size: 12px;">
                                View on Cloudinary →
                            </a>
                        </td>
                    </tr>
                """
            else:
                try:
                    file_path = obj.file.path
                    info_html += f"""
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Storage:</td>
                        <td style="padding: 8px 0;">
                            <span style="background: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 3px; font-size: 12px;">
                                💾 Local Server Storage
                            </span>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Server Path:</td>
                        <td style="padding: 8px 0;"><code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 11px; word-break: break-all;">{file_path}</code></td>
                    </tr>
                    """
                except (NotImplementedError, AttributeError):
                    pass

            # Image-specific info
            if MediaUtils.is_image_file(obj.file.name):
                try:
                    if hasattr(obj.file, "path"):
                        image_info = MediaUtils.get_image_info(obj.file.path)
                        if image_info:
                            info_html += f"""
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Dimensions:</td>
                        <td style="padding: 8px 0; color: #212529;">{image_info['width']} × {image_info['height']} pixels</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Image Format:</td>
                        <td style="padding: 8px 0; color: #212529;">{image_info['format']}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Color Mode:</td>
                        <td style="padding: 8px 0; color: #212529;">{image_info['mode']}</td>
                    </tr>
                            """
                except Exception:
                    pass

            # Upload date
            info_html += f"""
                    <tr>
                        <td style="padding: 8px 0; font-weight: 600; color: #495057;">Uploaded:</td>
                        <td style="padding: 8px 0; color: #212529;">{obj.created_at.strftime('%B %d, %Y at %I:%M %p')}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 12px; padding: 10px; background: #e7f3ff; border-radius: 4px; border-left: 3px solid #0066cc;">
                    <small style="color: #004085; font-size: 12px;">
                        <strong>💡 Usage Tip:</strong> This file is publicly accessible via the URL above. 
                        {'For responsive images, the system automatically generates optimized versions for different devices.' if MediaUtils.is_image_file(obj.file.name) and 'cloudinary' in obj.file.url else 'Copy the URL to use this file in your content.'}
                    </small>
                </div>
            </div>
            """

            return format_html(info_html)

        except Exception as e:
            return format_html(
                '<div style="background: #ffebee; padding: 12px; border-radius: 4px; border-left: 4px solid #c62828;">'
                "<strong>⚠️ Error loading file information</strong><br>"
                '<small style="color: #666;">{}</small>'
                "</div>",
                str(e),
            )

    file_info_display.short_description = "File Information"

    def file_preview(self, obj):
        """Show file preview"""
        if not obj.file:
            return "No file to preview"

        try:
            if MediaUtils.is_image_file(obj.file.name):
                try:
                    return format_html(
                        '<img src="{}" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;">',
                        obj.file.url,
                    )
                except Exception:
                    return "Image preview unavailable"
            else:
                try:
                    return format_html(
                        "<p>Preview not available for this file type.</p>"
                        '<p><a href="{}" target="_blank">Download file</a></p>',
                        obj.file.url,
                    )
                except Exception:
                    return "File preview unavailable"
        except Exception:
            return "Preview unavailable"

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
