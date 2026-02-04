from django.db import models
from django.conf import settings

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255, db_index=True)  # Title searching
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)  # Read/unread filtering
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_read']),  # User notifications by read status
            models.Index(fields=['user', 'created_at']),  # User notifications ordered by date
            models.Index(fields=['is_read', 'created_at']),  # Unread notifications by date
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.id}"
