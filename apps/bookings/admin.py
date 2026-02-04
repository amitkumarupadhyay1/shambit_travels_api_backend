from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'package', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'package__city']
    search_fields = ['user__email', 'user__username', 'package__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Booking Info', {
            'fields': ('user', 'package', 'status', 'total_price')
        }),
        ('Selected Components', {
            'fields': ('selected_experiences', 'selected_hotel_tier', 'selected_transport')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['selected_experiences']
    
    def get_queryset(self, request):
        # Optimize admin queryset with select_related and prefetch_related
        return super().get_queryset(request).select_related(
            'user', 'package__city', 'selected_hotel_tier', 'selected_transport'
        ).prefetch_related('selected_experiences')