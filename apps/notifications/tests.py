from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification
from .services.notification_service import NotificationService

User = get_user_model()


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            user=self.user, title="Test Notification", message="This is a test message"
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.message, "This is a test message")
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)

    def test_notification_str_method(self):
        notification = Notification.objects.create(
            user=self.user, title="Test", message="Test message"
        )

        self.assertEqual(str(notification), f"Notification for {self.user.id}")


class NotificationServiceTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="testpass123"
        )

    def test_create_notification(self):
        notification = NotificationService.create_notification(
            user=self.user1, title="Service Test", message="Service test message"
        )

        self.assertEqual(notification.user, self.user1)
        self.assertEqual(notification.title, "Service Test")
        self.assertFalse(notification.is_read)

    def test_create_bulk_notifications(self):
        users = [self.user1, self.user2]
        notifications = NotificationService.create_bulk_notifications(
            users=users, title="Bulk Test", message="Bulk test message"
        )

        self.assertEqual(len(notifications), 2)
        self.assertEqual(Notification.objects.count(), 2)

    def test_get_user_stats(self):
        # Create some notifications
        NotificationService.create_notification(self.user1, "Test 1", "Message 1")
        notification2 = NotificationService.create_notification(
            self.user1, "Test 2", "Message 2"
        )
        notification2.is_read = True
        notification2.save()

        stats = NotificationService.get_user_stats(self.user1)

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["unread"], 1)
        self.assertEqual(stats["read"], 1)

    def test_mark_all_read(self):
        # Create unread notifications
        NotificationService.create_notification(self.user1, "Test 1", "Message 1")
        NotificationService.create_notification(self.user1, "Test 2", "Message 2")

        updated_count = NotificationService.mark_all_read(self.user1)

        self.assertEqual(updated_count, 2)
        self.assertEqual(
            Notification.objects.filter(user=self.user1, is_read=False).count(), 0
        )


class NotificationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )

        # Create test notifications
        self.notification1 = Notification.objects.create(
            user=self.user, title="Test Notification 1", message="Test message 1"
        )
        self.notification2 = Notification.objects.create(
            user=self.user,
            title="Test Notification 2",
            message="Test message 2",
            is_read=True,
        )
        # Notification for other user (should not be accessible)
        self.other_notification = Notification.objects.create(
            user=self.other_user,
            title="Other User Notification",
            message="Other user message",
        )

    def test_list_notifications_unauthenticated(self):
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notifications_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Should only see own notifications
        notification_ids = [n["id"] for n in response.data["results"]]
        self.assertIn(self.notification1.id, notification_ids)
        self.assertIn(self.notification2.id, notification_ids)
        self.assertNotIn(self.other_notification.id, notification_ids)

    def test_filter_notifications_by_read_status(self):
        self.client.force_authenticate(user=self.user)

        # Test unread filter
        url = reverse("notification-list") + "?is_read=false"
        response = self.client.get(url)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.notification1.id)

        # Test read filter
        url = reverse("notification-list") + "?is_read=true"
        response = self.client.get(url)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.notification2.id)

    def test_search_notifications(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-list") + "?search=Notification 1"
        response = self.client.get(url)

        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.notification1.id)

    def test_get_notification_stats(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-stats")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_count"], 2)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(response.data["read_count"], 1)

    def test_mark_all_read(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-mark-all-read")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 1)

        # Verify notification is marked as read
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_mark_notification_read(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-mark-read", kwargs={"pk": self.notification1.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])

        # Verify in database
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_cannot_access_other_user_notification(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-detail", kwargs={"pk": self.other_notification.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_unread_notifications(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-unread")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.notification1.id)

    def test_get_recent_notifications(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-recent")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_clear_read_notifications(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("notification-clear-read")
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 1)

        # Verify read notification is deleted
        self.assertFalse(Notification.objects.filter(id=self.notification2.id).exists())
        # Verify unread notification still exists
        self.assertTrue(Notification.objects.filter(id=self.notification1.id).exists())

    def test_clear_old_notifications(self):
        # Create old notification
        old_notification = Notification.objects.create(
            user=self.user, title="Old Notification", message="Old message"
        )
        old_notification.created_at = timezone.now() - timedelta(days=35)
        old_notification.save()

        self.client.force_authenticate(user=self.user)
        url = reverse("notification-clear-old") + "?days=30"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 1)

        # Verify old notification is deleted
        self.assertFalse(Notification.objects.filter(id=old_notification.id).exists())
