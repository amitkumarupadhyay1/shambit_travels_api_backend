from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html

class TravelPlatformAdminSite(AdminSite):
    site_header = "🏖️ Travel Platform Admin"
    site_title = "Travel Platform"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Add quick stats
        from cities.models import City
        from articles.models import Article
        from packages.models import Package
        from bookings.models import Booking
        from users.models import User
        
        extra_context.update({
            'quick_stats': {
                'cities': City.objects.count(),
                'articles': Article.objects.filter(status='PUBLISHED').count(),
                'packages': Package.objects.filter(is_active=True).count(),
                'bookings': Booking.objects.count(),
                'users': User.objects.count(),
            }
        })
        
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = TravelPlatformAdminSite(name='travel_admin')