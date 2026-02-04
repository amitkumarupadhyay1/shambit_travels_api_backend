from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Notification
from .services.notification_service import NotificationService

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user_email', 'is_read_badge', 'created_at', 'message_preview']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'title', 'message', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_bulk_notification']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Read</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Unread</span>'
            )
    is_read_badge.short_description = 'Status'
    is_read_badge.admin_order_field = 'is_read'
    
    def message_preview(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + '...'
        return obj.message
    message_preview.short_description = 'Message Preview'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request,
            f'{updated} notifications marked as read.',
            messages.SUCCESS
        )
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(
            request,
            f'{updated} notifications marked as unread.',
            messages.SUCCESS
        )
    mark_as_unread.short_description = 'Mark selected notifications as unread'
    
    def send_bulk_notification(self, request, queryset):
        # This action redirects to a custom form for bulk notification
        selected = queryset.values_list('user_id', flat=True)
        request.session['selected_users'] = list(set(selected))
        return redirect('admin:send_bulk_notification')
    send_bulk_notification.short_description = 'Send notification to selected users'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-bulk/',
                self.admin_site.admin_view(self.send_bulk_notification_view),
                name='send_bulk_notification'
            ),
            path(
                'stats/',
                self.admin_site.admin_view(self.notification_stats_view),
                name='notification_stats'
            ),
        ]
        return custom_urls + urls
    
    def send_bulk_notification_view(self, request):
        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            user_ids = request.session.get('selected_users', [])
            
            if title and message and user_ids:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                users = User.objects.filter(id__in=user_ids)
                
                notifications = NotificationService.create_bulk_notifications(
                    list(users), title, message
                )
                
                self.message_user(
                    request,
                    f'Sent notification to {len(notifications)} users.',
                    messages.SUCCESS
                )
                return redirect('admin:notifications_notification_changelist')
        
        user_ids = request.session.get('selected_users', [])
        context = {
            'title': 'Send Bulk Notification',
            'user_count': len(user_ids),
            'opts': self.model._meta,
        }
        return render(request, 'admin/notifications/send_bulk.html', context)
    
    def notification_stats_view(self, request):
        stats = Notification.objects.aggregate(
            total=Count('id'),
            read=Count('id', filter=Q(is_read=True)),
            unread=Count('id', filter=Q(is_read=False))
        )
        
        context = {
            'title': 'Notification Statistics',
            'stats': stats,
            'opts': self.model._meta,
        }
        return render(request, 'admin/notifications/stats.html', context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['notification_stats_url'] = 'admin:notification_stats'
        return super().changelist_view(request, extra_context)