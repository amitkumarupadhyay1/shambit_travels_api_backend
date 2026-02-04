# Notifications App

A comprehensive notification system for the travel platform with production-level features.

## Features

### Core Functionality
- ✅ User-specific notifications
- ✅ Read/unread status tracking
- ✅ Bulk operations for performance
- ✅ Search and filtering capabilities
- ✅ Statistics and analytics
- ✅ Automatic cleanup of old notifications

### API Endpoints

#### Standard CRUD Operations
- `GET /api/notifications/` - List user's notifications
- `POST /api/notifications/` - Create notification (admin/system)
- `GET /api/notifications/{id}/` - Get specific notification
- `PUT /api/notifications/{id}/` - Update notification
- `PATCH /api/notifications/{id}/` - Partial update notification
- `DELETE /api/notifications/{id}/` - Delete notification

#### Custom Actions
- `GET /api/notifications/stats/` - Get notification statistics
- `POST /api/notifications/mark_all_read/` - Mark all as read
- `POST /api/notifications/mark_all_unread/` - Mark all as unread
- `POST /api/notifications/{id}/mark_read/` - Mark specific as read
- `POST /api/notifications/{id}/mark_unread/` - Mark specific as unread
- `DELETE /api/notifications/clear_read/` - Delete all read notifications
- `DELETE /api/notifications/clear_old/?days=30` - Delete old notifications
- `GET /api/notifications/recent/` - Get recent notifications (7 days)
- `GET /api/notifications/unread/` - Get only unread notifications

#### Query Parameters for List Endpoint
- `?is_read=true/false` - Filter by read status
- `?search=text` - Search in title and message
- `?days=7` - Filter by days since creation

### Service Layer

The `NotificationService` class provides business logic methods:

```python
from notifications.services.notification_service import NotificationService

# Create single notification
notification = NotificationService.create_notification(
    user=user,
    title="Booking Confirmed",
    message="Your booking has been confirmed"
)

# Create bulk notifications
NotificationService.create_bulk_notifications(
    users=[user1, user2],
    title="System Maintenance",
    message="Scheduled maintenance tonight"
)

# Get user statistics
stats = NotificationService.get_user_stats(user)
# Returns: {'total': 10, 'unread': 3, 'read': 7}

# Mark all as read
updated_count = NotificationService.mark_all_read(user)
```

### Automatic Notifications

The system automatically creates notifications for:

- **User Registration**: Welcome message for new users
- **Booking Events**: Creation, confirmation, cancellation
- **Payment Events**: Success, failure notifications

### Management Commands

#### Cleanup Old Notifications
```bash
# Delete notifications older than 30 days
python manage.py cleanup_notifications --days=30

# Dry run to see what would be deleted
python manage.py cleanup_notifications --days=30 --dry-run
```

#### Send Notifications
```bash
# Send to specific user
python manage.py send_notification "Important Update" "Please check your bookings" --user-id=123

# Send to all users
python manage.py send_notification "System Maintenance" "Scheduled maintenance tonight" --all-users
```

### Database Optimization

The notification model includes optimized indexes for:
- User + read status queries
- User + creation date ordering
- Read status + creation date filtering

```python
class Meta:
    indexes = [
        models.Index(fields=['user', 'is_read']),
        models.Index(fields=['user', 'created_at']),
        models.Index(fields=['is_read', 'created_at']),
    ]
    ordering = ['-created_at']
```

### Testing

Comprehensive test suite covering:
- Model functionality
- Service layer methods
- API endpoints
- Authentication and authorization
- Filtering and search
- Bulk operations

Run tests:
```bash
python manage.py test notifications
```

### Usage Examples

#### Frontend Integration
```javascript
// Get user notifications
const response = await fetch('/api/notifications/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const notifications = await response.json();

// Mark notification as read
await fetch(`/api/notifications/${notificationId}/mark_read/`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Get notification stats
const statsResponse = await fetch('/api/notifications/stats/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const stats = await statsResponse.json();
// { total_count: 15, unread_count: 3, read_count: 12 }
```

#### Backend Integration
```python
# In your booking view
from notifications.services.notification_service import NotificationService

def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'CONFIRMED'
    booking.save()
    
    # Notification is automatically created via signals
    # Or create manually:
    NotificationService.notify_booking_confirmed(booking)
```

### Performance Considerations

1. **Database Indexes**: Optimized for common query patterns
2. **Bulk Operations**: Use bulk_create and bulk_update for multiple notifications
3. **Pagination**: List endpoints are paginated by default
4. **Selective Fields**: List serializer returns only essential fields
5. **Query Optimization**: Uses select_related and prefetch_related where appropriate

### Security Features

- **User Isolation**: Users can only access their own notifications
- **Authentication Required**: All endpoints require authentication
- **Input Validation**: Comprehensive serializer validation
- **SQL Injection Protection**: Uses Django ORM exclusively

### Future Enhancements

- Real-time notifications via WebSocket (Django Channels)
- Email/SMS notification delivery
- Notification templates and categories
- Push notification support
- Notification preferences per user