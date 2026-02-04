from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewset
router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]

# Available endpoints:
# GET /api/notifications/ - List user's notifications (with filtering)
# POST /api/notifications/ - Create notification (admin/system)
# GET /api/notifications/{id}/ - Get specific notification
# PUT /api/notifications/{id}/ - Update notification
# PATCH /api/notifications/{id}/ - Partial update notification
# DELETE /api/notifications/{id}/ - Delete notification
# 
# Custom actions:
# GET /api/notifications/stats/ - Get notification statistics
# POST /api/notifications/mark_all_read/ - Mark all as read
# POST /api/notifications/mark_all_unread/ - Mark all as unread
# POST /api/notifications/{id}/mark_read/ - Mark specific as read
# POST /api/notifications/{id}/mark_unread/ - Mark specific as unread
# DELETE /api/notifications/clear_read/ - Delete all read notifications
# DELETE /api/notifications/clear_old/?days=30 - Delete old notifications
# GET /api/notifications/recent/ - Get recent notifications (7 days)
# GET /api/notifications/unread/ - Get only unread notifications
#
# Query parameters for list endpoint:
# ?is_read=true/false - Filter by read status
# ?search=text - Search in title and message
# ?days=7 - Filter by days since creation