from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Full notification serializer for detailed views
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user_email', 'title', 'message', 'is_read', 
            'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'created_at']

class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views to optimize performance
    """
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications (admin/system use)
    """
    class Meta:
        model = Notification
        fields = ['title', 'message', 'user']

class NotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating notification read status
    """
    class Meta:
        model = Notification
        fields = ['is_read']

class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics
    """
    total_count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()