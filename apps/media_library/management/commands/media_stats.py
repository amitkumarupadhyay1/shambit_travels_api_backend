from django.core.management.base import BaseCommand
from media_library.services.media_service import MediaService
from media_library.utils import MediaUtils

class Command(BaseCommand):
    help = 'Display media library statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed statistics'
        )
        parser.add_argument(
            '--storage',
            action='store_true',
            help='Show storage information'
        )
        parser.add_argument(
            '--usage-report',
            action='store_true',
            help='Generate comprehensive usage report'
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        show_storage = options['storage']
        usage_report = options['usage_report']

        self.stdout.write(
            self.style.SUCCESS('Media Library Statistics')
        )
        self.stdout.write('=' * 50)

        # Basic statistics
        stats = MediaService.get_media_stats()
        
        self.stdout.write(f"Total Files: {stats['total_files']}")
        self.stdout.write(f"Total Size: {MediaUtils.format_file_size(stats['total_size'])}")
        self.stdout.write(f"Recent Uploads (7 days): {stats['recent_uploads']}")
        
        # File type breakdown
        self.stdout.write('\nFile Types:')
        for file_type, count in stats['by_type'].items():
            self.stdout.write(f"  {file_type.capitalize()}: {count}")
        
        # Content type breakdown
        if stats['by_content_type']:
            self.stdout.write('\nBy Content Type:')
            for ct_data in stats['by_content_type']:
                content_type = f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}"
                self.stdout.write(f"  {content_type}: {ct_data['count']}")

        # Detailed statistics
        if detailed:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write('DETAILED STATISTICS')
            self.stdout.write('=' * 50)
            
            from media_library.models import Media
            from django.utils import timezone
            from datetime import timedelta
            
            # Upload trends
            self.stdout.write('\nUpload Trends:')
            for days in [1, 7, 30]:
                recent_date = timezone.now() - timedelta(days=days)
                count = Media.objects.filter(created_at__gte=recent_date).count()
                self.stdout.write(f"  Last {days} day{'s' if days > 1 else ''}: {count}")
            
            # Average file sizes by type
            self.stdout.write('\nAverage File Sizes:')
            for file_type in ['image', 'video', 'document']:
                if file_type == 'image':
                    queryset = Media.objects.filter(file__iregex=r'\.(jpg|jpeg|png|gif|webp)$')
                elif file_type == 'video':
                    queryset = Media.objects.filter(file__iregex=r'\.(mp4|avi|mov|wmv|flv)$')
                elif file_type == 'document':
                    queryset = Media.objects.filter(file__iregex=r'\.pdf$')
                
                if queryset.exists():
                    total_size = 0
                    count = 0
                    for media in queryset:
                        if media.file:
                            try:
                                total_size += media.file.size
                                count += 1
                            except (OSError, ValueError):
                                pass
                    
                    if count > 0:
                        avg_size = total_size / count
                        self.stdout.write(f"  {file_type.capitalize()}: {MediaUtils.format_file_size(int(avg_size))}")

        # Storage information
        if show_storage:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write('STORAGE INFORMATION')
            self.stdout.write('=' * 50)
            
            storage_info = MediaService.get_storage_info()
            
            if 'error' in storage_info:
                self.stdout.write(
                    self.style.ERROR(f'Error: {storage_info["error"]}')
                )
            else:
                self.stdout.write(f"Media Root: {storage_info['media_root']}")
                self.stdout.write(f"Files in Storage: {storage_info['total_files']}")
                self.stdout.write(f"Storage Size: {MediaUtils.format_file_size(storage_info['total_size'])}")
                
                if storage_info['disk_total']:
                    self.stdout.write(f"Disk Total: {MediaUtils.format_file_size(storage_info['disk_total'])}")
                    self.stdout.write(f"Disk Used: {MediaUtils.format_file_size(storage_info['disk_used'])}")
                    self.stdout.write(f"Disk Free: {MediaUtils.format_file_size(storage_info['disk_free'])}")
                    self.stdout.write(f"Disk Usage: {storage_info['disk_usage_percentage']:.1f}%")

        # Usage report
        if usage_report:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write('USAGE REPORT')
            self.stdout.write('=' * 50)
            
            report = MediaService.get_media_usage_report()
            
            # Content type usage
            self.stdout.write('\nContent Type Usage:')
            for ct_usage in report['content_type_usage']:
                size_str = MediaUtils.format_file_size(ct_usage['total_size'])
                self.stdout.write(
                    f"  {ct_usage['content_type']}: {ct_usage['count']} files ({size_str})"
                )
            
            # Recent activity
            self.stdout.write('\nRecent Activity:')
            for activity in report['recent_uploads']:
                self.stdout.write(f"  {activity['period']}: {activity['count']} uploads")
            
            # File type distribution
            self.stdout.write('\nFile Type Distribution:')
            for file_type, count in report['file_type_distribution'].items():
                percentage = (count / report['total_files'] * 100) if report['total_files'] > 0 else 0
                self.stdout.write(f"  {file_type.capitalize()}: {count} ({percentage:.1f}%)")

        self.stdout.write(
            self.style.SUCCESS('\nStatistics complete!')
        )