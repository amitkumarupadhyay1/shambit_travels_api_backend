from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Add any extra fields if needed
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    oauth_provider = models.CharField(max_length=50, blank=True, db_index=True)  # OAuth filtering
    oauth_uid = models.CharField(max_length=255, blank=True, db_index=True)  # OAuth lookups
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),  # Email lookups
            models.Index(fields=['oauth_provider', 'oauth_uid']),  # OAuth lookups
            models.Index(fields=['is_active', 'date_joined']),  # Active users by join date
        ]
    
    def __str__(self):
        return self.email or self.username
