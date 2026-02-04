from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum, Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Any, Optional
import os
import shutil
from ..models import Media

class MediaService:
    """
    Service class for media library business logic and operations
    """
    
    @staticmethod
    def create_media(file, title: str = '', alt_text: str = '', 
                    content_type: str = None, object_id: int = None) -> Media:
        """
        Create a media object with proper validation
        """
        media_data = {
            'file': file,
            'title': title or file.name,
            'alt_text': alt_text
        }
        
        if content_type and object_id:
            app_label, model = content_type.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model)
            media_data.update({
                'content_type': ct,
                'object_id': object_id
            })
        
        return Media.objects.create(**media_data)
    
    @staticmethod
    def attach_media_to_object(media: Media, content_type: str, object_id: int) -> Media:
        """
        Attach existing media to a content object
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        media.content_type = ct
        media.object_id = object_id
        media.save()
        
        return media
    
    @staticmethod
    def get_media_for_object(content_type: str, object_id: int) -> List[Media]:
        """
        Get all media files for a specific object
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        return Media.objects.filter(content_type=ct, object_id=object_id)
    
    @staticmethod
    def bulk_operation(media_ids: List[int], action: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform bulk operations on media files
        """
        media_objects = Media.objects.filter(id__in=media_ids)
        
        if action == 'delete':
            # Delete files from storage
            deleted_files = []
            for media in media_objects:
                if media.file:
                    try:
                        if os.path.exists(media.file.path):
                            os.remove(media.file.path)
                        deleted_files.append(media.file.name)
                    except (OSError, ValueError):
                        pass
            
            deleted_count = media_objects.count()
            media_objects.delete()
            
            return {
                'action': 'delete',
                'processed_count': deleted_count,
                'deleted_files': deleted_files
            }
        
        elif action == 'update_metadata':
            updated_count = 0
            for media in media_objects:
                if metadata.get('title'):
                    media.title = metadata['title']
                if metadata.get('alt_text'):
                    media.alt_text = metadata['alt_text']
                media.save()
                updated_count += 1
            
            return {
                'action': 'update_metadata',
                'processed_count': updated_count,
                'metadata': metadata
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")
    
    @staticmethod
    def get_media_stats() -> Dict[str, Any]:
        """
        Get comprehensive media library statistics
        """
        total_files = Media.objects.count()
        
        # Calculate total file size
        total_size = 0
        for media in Media.objects.all():
            if media.file:
                try:
                    total_size += media.file.size
                except (OSError, ValueError):
                    pass
        
        # Stats by file type
        by_type = {
            'images': Media.objects.filter(
                file__iregex=r'\.(jpg|jpeg|png|gif|webp)$'
            ).count(),
            'videos': Media.objects.filter(
                file__iregex=r'\.(mp4|avi|mov|wmv|flv)$'
            ).count(),
            'documents': Media.objects.filter(
                file__iregex=r'\.pdf$'
            ).count(),
        }
        by_type['other'] = total_files - sum(by_type.values())
        
        # Stats by content type
        by_content_type = list(
            Media.objects.values(
                'content_type__app_label',
                'content_type__model'
            ).annotate(count=Count('id')).order_by('-count')
        )
        
        # Recent uploads (last 7 days)
        recent_date = timezone.now() - timedelta(days=7)
        recent_uploads = Media.objects.filter(created_at__gte=recent_date).count()
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'by_type': by_type,
            'by_content_type': by_content_type,
            'recent_uploads': recent_uploads
        }
    
    @staticmethod
    def search_media(search_params: Dict[str, Any]) -> List[Media]:
        """
        Advanced search for media files
        """
        queryset = Media.objects.all()
        
        # Text search
        query = search_params.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(alt_text__icontains=query) |
                Q(file__icontains=query)
            )
        
        # File type filter
        file_type = search_params.get('file_type')
        if file_type:
            if file_type == 'image':
                queryset = queryset.filter(
                    file__iregex=r'\.(jpg|jpeg|png|gif|webp)$'
                )
            elif file_type == 'video':
                queryset = queryset.filter(
                    file__iregex=r'\.(mp4|avi|mov|wmv|flv)$'
                )
            elif file_type == 'document':
                queryset = queryset.filter(file__iregex=r'\.pdf$')
        
        # Content type filter
        content_type = search_params.get('content_type')
        if content_type:
            try:
                app_label, model = content_type.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model)
                queryset = queryset.filter(content_type=ct)
            except (ValueError, ContentType.DoesNotExist):
                pass
        
        # Date range filter
        date_from = search_params.get('date_from')
        date_to = search_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def cleanup_orphaned_media() -> int:
        """
        Delete media files that are not attached to any existing object
        """
        orphaned_media = []
        
        for media in Media.objects.all():
            try:
                # Try to access the content object
                if not media.content_object:
                    orphaned_media.append(media)
            except:
                orphaned_media.append(media)
        
        # Delete orphaned media
        deleted_count = 0
        for media in orphaned_media:
            try:
                if media.file and os.path.exists(media.file.path):
                    os.remove(media.file.path)
                media.delete()
                deleted_count += 1
            except (OSError, ValueError):
                pass
        
        return deleted_count
    
    @staticmethod
    def get_storage_info() -> Dict[str, Any]:
        """
        Get storage information and usage
        """
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        
        if not media_root:
            return {
                'error': 'MEDIA_ROOT not configured in settings'
            }
        
        # Convert to string if it's a Path object
        media_root_str = str(media_root)
        
        if not os.path.exists(media_root_str):
            try:
                # Try to create the media directory if it doesn't exist
                os.makedirs(media_root_str, exist_ok=True)
            except (OSError, PermissionError) as e:
                return {
                    'error': f'Media root not accessible: {str(e)}'
                }
        
        # Calculate directory size
        total_size = 0
        file_count = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(media_root_str):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        total_size += file_size
                        file_count += 1
                    except (OSError, ValueError):
                        pass
        except (OSError, PermissionError) as e:
            return {
                'error': f'Cannot access media directory: {str(e)}'
            }
        
        # Get disk usage - handle Windows/Unix differences
        disk_total = disk_free = disk_used = disk_usage_percentage = None
        
        try:
            if hasattr(shutil, 'disk_usage'):
                disk_usage = shutil.disk_usage(media_root_str)
                disk_total = disk_usage.total
                disk_free = disk_usage.free
                disk_used = disk_total - disk_free
                disk_usage_percentage = (disk_used / disk_total * 100) if disk_total > 0 else 0
        except (OSError, AttributeError, PermissionError) as e:
            # Fallback: just report that disk usage info is not available
            pass
        
        return {
            'media_root': media_root_str,
            'total_files': file_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0,
            'disk_total': disk_total,
            'disk_used': disk_used,
            'disk_free': disk_free,
            'disk_usage_percentage': round(disk_usage_percentage, 2) if disk_usage_percentage is not None else None,
            'disk_info_available': disk_total is not None
        }
    
    @staticmethod
    def cleanup_unused_files() -> Dict[str, Any]:
        """
        Clean up files in media directory that are not referenced in database
        """
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        if not media_root or not os.path.exists(media_root):
            return {'error': 'Media root not found'}
        
        # Get all file paths from database
        db_files = set()
        for media in Media.objects.all():
            if media.file:
                # Get relative path from media root
                try:
                    rel_path = os.path.relpath(media.file.path, media_root)
                    db_files.add(rel_path)
                except (ValueError, AttributeError):
                    pass
        
        # Find files in storage that are not in database
        unused_files = []
        total_size_freed = 0
        
        for dirpath, dirnames, filenames in os.walk(media_root):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, media_root)
                
                if rel_path not in db_files:
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        unused_files.append(rel_path)
                        total_size_freed += file_size
                    except (OSError, ValueError):
                        pass
        
        # Remove empty directories
        empty_dirs_removed = 0
        for dirpath, dirnames, filenames in os.walk(media_root, topdown=False):
            if dirpath != media_root:  # Don't remove media root itself
                try:
                    if not os.listdir(dirpath):  # Directory is empty
                        os.rmdir(dirpath)
                        empty_dirs_removed += 1
                except (OSError, ValueError):
                    pass
        
        return {
            'unused_files_removed': len(unused_files),
            'total_size_freed': total_size_freed,
            'empty_dirs_removed': empty_dirs_removed,
            'files': unused_files[:50]  # Return first 50 for reference
        }
    
    @staticmethod
    def duplicate_media(media: Media, new_title: str = None) -> Media:
        """
        Create a duplicate of existing media
        """
        # Copy the file
        import shutil
        from django.core.files import File
        
        if not media.file:
            raise ValueError("Cannot duplicate media without file")
        
        # Create new filename
        original_name = media.file.name
        name, ext = os.path.splitext(original_name)
        new_filename = f"{name}_copy{ext}"
        
        # Copy file
        original_path = media.file.path
        new_path = os.path.join(os.path.dirname(original_path), os.path.basename(new_filename))
        
        shutil.copy2(original_path, new_path)
        
        # Create new media object
        with open(new_path, 'rb') as f:
            new_media = Media.objects.create(
                file=File(f, name=os.path.basename(new_filename)),
                title=new_title or f"{media.title} (Copy)",
                alt_text=media.alt_text,
                content_type=media.content_type,
                object_id=media.object_id
            )
        
        return new_media
    
    @staticmethod
    def get_media_usage_report() -> Dict[str, Any]:
        """
        Generate a comprehensive usage report
        """
        # Media by content type with details
        content_type_usage = []
        
        for ct_data in Media.objects.values(
            'content_type__app_label',
            'content_type__model'
        ).annotate(count=Count('id')).order_by('-count'):
            
            content_type_str = f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}"
            
            # Get size for this content type
            ct_media = Media.objects.filter(
                content_type__app_label=ct_data['content_type__app_label'],
                content_type__model=ct_data['content_type__model']
            )
            
            total_size = 0
            for media in ct_media:
                if media.file:
                    try:
                        total_size += media.file.size
                    except (OSError, ValueError):
                        pass
            
            content_type_usage.append({
                'content_type': content_type_str,
                'count': ct_data['count'],
                'total_size': total_size
            })
        
        # Recent activity
        recent_uploads = []
        for days in [1, 7, 30]:
            recent_date = timezone.now() - timedelta(days=days)
            count = Media.objects.filter(created_at__gte=recent_date).count()
            recent_uploads.append({
                'period': f"Last {days} day{'s' if days > 1 else ''}",
                'count': count
            })
        
        # File type distribution
        file_types = MediaService.get_media_stats()['by_type']
        
        return {
            'content_type_usage': content_type_usage,
            'recent_uploads': recent_uploads,
            'file_type_distribution': file_types,
            'total_files': Media.objects.count(),
            'generated_at': timezone.now().isoformat()
        }