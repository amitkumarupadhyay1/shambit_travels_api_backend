#!/usr/bin/env python
"""
Comprehensive Notification System API Testing Script
Tests all notification endpoints (core + push)
"""

import json
import os
import sys
from datetime import datetime

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")
django.setup()

# Import after django.setup() to avoid AppRegistryNotReady error
from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

User = get_user_model()


class Colors:
    """ANSI color codes"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class NotificationAPITester:
    """Test all notification API endpoints"""

    def __init__(self):
        self.client = Client()
        self.user = None
        self.token = None
        self.test_results = []
        self.notification_id = None
        self.subscription_id = None

    def print_header(self, text):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")

    def print_test(self, name, passed, details=""):
        """Print test result"""
        status = (
            f"{Colors.GREEN}✓ PASS{Colors.RESET}"
            if passed
            else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        )
        print(f"{status} - {name}")
        if details:
            print(f"  {Colors.YELLOW}{details}{Colors.RESET}")
        self.test_results.append({"name": name, "passed": passed, "details": details})

    def setup_test_user(self):
        """Create or get test user"""
        self.print_header("SETUP: Creating Test User")

        try:
            # Try to get existing test user
            self.user = User.objects.filter(email="test@shambit.com").first()

            if not self.user:
                # Create new test user
                self.user = User.objects.create_user(
                    email="test@shambit.com",
                    password="testpass123",
                    first_name="Test",
                    last_name="User",
                )
                self.print_test(
                    "Create test user", True, f"Created user: {self.user.email}"
                )
            else:
                self.print_test(
                    "Get test user", True, f"Using existing user: {self.user.email}"
                )

            return True
        except Exception as e:
            self.print_test("Setup test user", False, str(e))
            return False

    def create_test_notifications(self):
        """Create test notifications"""
        self.print_header("SETUP: Creating Test Notifications")

        try:
            from apps.notifications.models import Notification

            # Create unread notification
            notif1 = Notification.objects.create(
                user=self.user,
                title="Test Booking Confirmed",
                message="Your booking has been confirmed",
                is_read=False,
            )

            # Create read notification
            Notification.objects.create(
                user=self.user,
                title="Test Payment Successful",
                message="Your payment was processed successfully",
                is_read=True,
            )

            self.notification_id = notif1.id

            self.print_test(
                "Create test notifications", True, f"Created {2} notifications"
            )
            return True
        except Exception as e:
            self.print_test("Create test notifications", False, str(e))
            return False

    def test_get_notifications(self):
        """Test GET /api/notifications/"""
        self.print_header("TEST: Get Notifications List")

        try:
            response = self.client.get(
                "/api/notifications/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else {}

            self.print_test(
                "GET /api/notifications/",
                passed,
                f"Status: {response.status_code}, Count: {data.get('count', 0)}",
            )

            if passed:
                # Check response structure
                has_count = "count" in data
                has_results = "results" in data
                self.print_test("Response has 'count'", has_count)
                self.print_test("Response has 'results'", has_results)

            return passed
        except Exception as e:
            self.print_test("GET /api/notifications/", False, str(e))
            return False

    def test_get_stats(self):
        """Test GET /api/notifications/stats/"""
        self.print_header("TEST: Get Notification Statistics")

        try:
            response = self.client.get(
                "/api/notifications/stats/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else {}

            self.print_test(
                "GET /api/notifications/stats/",
                passed,
                f"Total: {data.get('total', 0)}, Unread: {data.get('unread', 0)}, Read: {data.get('read', 0)}",
            )

            if passed:
                has_total = "total" in data
                has_unread = "unread" in data
                has_read = "read" in data
                self.print_test("Stats has 'total'", has_total)
                self.print_test("Stats has 'unread'", has_unread)
                self.print_test("Stats has 'read'", has_read)

            return passed
        except Exception as e:
            self.print_test("GET /api/notifications/stats/", False, str(e))
            return False

    def test_get_unread(self):
        """Test GET /api/notifications/unread/"""
        self.print_header("TEST: Get Unread Notifications")

        try:
            response = self.client.get(
                "/api/notifications/unread/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else []

            self.print_test(
                "GET /api/notifications/unread/",
                passed,
                f"Status: {response.status_code}, Count: {len(data)}",
            )

            if passed and len(data) > 0:
                all_unread = all(not n.get("is_read", True) for n in data)
                self.print_test("All notifications are unread", all_unread)

            return passed
        except Exception as e:
            self.print_test("GET /api/notifications/unread/", False, str(e))
            return False

    def test_mark_as_read(self):
        """Test POST /api/notifications/{id}/mark_read/"""
        self.print_header("TEST: Mark Notification as Read")

        if not self.notification_id:
            self.print_test("Mark as read", False, "No notification ID available")
            return False

        try:
            response = self.client.post(
                f"/api/notifications/{self.notification_id}/mark_read/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200

            self.print_test(
                f"POST /api/notifications/{self.notification_id}/mark_read/",
                passed,
                f"Status: {response.status_code}",
            )

            return passed
        except Exception as e:
            self.print_test("Mark as read", False, str(e))
            return False

    def test_mark_all_read(self):
        """Test POST /api/notifications/mark_all_read/"""
        self.print_header("TEST: Mark All Notifications as Read")

        try:
            response = self.client.post(
                "/api/notifications/mark_all_read/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else {}

            self.print_test(
                "POST /api/notifications/mark_all_read/",
                passed,
                f"Status: {response.status_code}, Updated: {data.get('updated_count', 0)}",
            )

            return passed
        except Exception as e:
            self.print_test("Mark all as read", False, str(e))
            return False

    def test_delete_notification(self):
        """Test DELETE /api/notifications/{id}/"""
        self.print_header("TEST: Delete Notification")

        if not self.notification_id:
            self.print_test(
                "Delete notification", False, "No notification ID available"
            )
            return False

        try:
            response = self.client.delete(
                f"/api/notifications/{self.notification_id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 204

            self.print_test(
                f"DELETE /api/notifications/{self.notification_id}/",
                passed,
                f"Status: {response.status_code}",
            )

            return passed
        except Exception as e:
            self.print_test("Delete notification", False, str(e))
            return False

    def test_clear_read(self):
        """Test DELETE /api/notifications/clear_read/"""
        self.print_header("TEST: Clear Read Notifications")

        try:
            response = self.client.delete(
                "/api/notifications/clear_read/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else {}

            self.print_test(
                "DELETE /api/notifications/clear_read/",
                passed,
                f"Status: {response.status_code}, Deleted: {data.get('deleted_count', 0)}",
            )

            return passed
        except Exception as e:
            self.print_test("Clear read notifications", False, str(e))
            return False

    def test_get_vapid_key(self):
        """Test GET /api/notifications/push/subscriptions/vapid-public-key/"""
        self.print_header("TEST: Get VAPID Public Key")

        try:
            response = self.client.get(
                "/api/notifications/push/subscriptions/vapid-public-key/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else {}

            self.print_test(
                "GET /api/notifications/push/subscriptions/vapid-public-key/",
                passed,
                f"Status: {response.status_code}",
            )

            if passed:
                has_key = "public_key" in data
                key_valid = data.get("public_key", "").startswith(
                    "-----BEGIN PUBLIC KEY-----"
                )
                self.print_test("Response has 'public_key'", has_key)
                self.print_test("Public key is valid format", key_valid)

            return passed
        except Exception as e:
            self.print_test("Get VAPID key", False, str(e))
            return False

    def test_create_subscription(self):
        """Test POST /api/notifications/push/subscriptions/"""
        self.print_header("TEST: Create Push Subscription")

        try:
            subscription_data = {
                "endpoint": f"https://fcm.googleapis.com/fcm/send/test-{datetime.now().timestamp()}",
                "keys": {
                    "p256dh": "test_p256dh_key_12345",
                    "auth": "test_auth_key_12345",
                },
            }

            response = self.client.post(
                "/api/notifications/push/subscriptions/",
                data=json.dumps(subscription_data),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 201
            data = response.json() if passed else {}

            self.print_test(
                "POST /api/notifications/push/subscriptions/",
                passed,
                f"Status: {response.status_code}",
            )

            if passed:
                self.subscription_id = data.get("id")
                has_id = "id" in data
                has_endpoint = "endpoint" in data
                is_active = data.get("is_active", False)
                self.print_test("Response has 'id'", has_id)
                self.print_test("Response has 'endpoint'", has_endpoint)
                self.print_test("Subscription is active", is_active)

            return passed
        except Exception as e:
            self.print_test("Create push subscription", False, str(e))
            return False

    def test_list_subscriptions(self):
        """Test GET /api/notifications/push/subscriptions/"""
        self.print_header("TEST: List Push Subscriptions")

        try:
            response = self.client.get(
                "/api/notifications/push/subscriptions/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 200
            data = response.json() if passed else []

            self.print_test(
                "GET /api/notifications/push/subscriptions/",
                passed,
                f"Status: {response.status_code}, Count: {len(data)}",
            )

            return passed
        except Exception as e:
            self.print_test("List push subscriptions", False, str(e))
            return False

    def test_delete_subscription(self):
        """Test DELETE /api/notifications/push/subscriptions/{id}/"""
        self.print_header("TEST: Delete Push Subscription")

        if not self.subscription_id:
            self.print_test(
                "Delete subscription", False, "No subscription ID available"
            )
            return False

        try:
            response = self.client.delete(
                f"/api/notifications/push/subscriptions/{self.subscription_id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )

            passed = response.status_code == 204

            self.print_test(
                f"DELETE /api/notifications/push/subscriptions/{self.subscription_id}/",
                passed,
                f"Status: {response.status_code}",
            )

            return passed
        except Exception as e:
            self.print_test("Delete push subscription", False, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")

        if failed > 0:
            print(f"{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['name']}")
                    if result["details"]:
                        print(f"    {result['details']}")

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}Notification System API Testing{Colors.RESET}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Setup
        if not self.setup_test_user():
            print(f"\n{Colors.RED}Setup failed. Aborting tests.{Colors.RESET}")
            return

        # Create test data
        self.create_test_notifications()

        # Note: We're using Django test client which doesn't require JWT token
        # In production, you would need to authenticate and get a token
        self.token = "test-token"  # Placeholder

        # Run core notification tests
        self.test_get_notifications()
        self.test_get_stats()
        self.test_get_unread()
        self.test_mark_as_read()
        self.test_mark_all_read()
        self.test_clear_read()
        self.test_delete_notification()

        # Run push notification tests
        self.test_get_vapid_key()
        self.test_create_subscription()
        self.test_list_subscriptions()
        self.test_delete_subscription()

        # Print summary
        self.print_summary()

        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    tester = NotificationAPITester()
    tester.run_all_tests()
