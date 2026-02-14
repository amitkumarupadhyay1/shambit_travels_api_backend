import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from bookings.models import Booking
from cities.models import City
from packages.models import Experience, HotelTier, Package, TransportOption
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class OAuthSecurityTests(APITestCase):
    """Test OAuth token verification"""

    def setUp(self):
        self.client = APIClient()
        self.sync_url = "/api/auth/nextauth-sync/"

    def test_oauth_sync_requires_token(self):
        """OAuth sync must require token"""
        response = self.client.post(
            self.sync_url,
            {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "provider": "google",
                "uid": "123456",
                # Missing 'token'
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("token", response.data.get("error", "").lower())

    def test_oauth_sync_rejects_invalid_token(self):
        """OAuth sync must reject invalid tokens"""
        response = self.client.post(
            self.sync_url,
            {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "provider": "google",
                "uid": "123456",
                "token": "invalid_token_xyz",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("verify", response.data.get("error", "").lower())

    def test_oauth_sync_validates_email_format(self):
        """OAuth sync must validate email format"""
        response = self.client.post(
            self.sync_url,
            {
                "email": "invalid-email",
                "first_name": "John",
                "last_name": "Doe",
                "provider": "google",
                "uid": "123456",
                "token": "some_token",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data.get("error", "").lower())

    def test_oauth_sync_validates_provider(self):
        """OAuth sync must validate provider"""
        response = self.client.post(
            self.sync_url,
            {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "provider": "linkedin",  # Unsupported
                "uid": "123456",
                "token": "some_token",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("provider", response.data.get("error", "").lower())


class PriceManipulationSecurityTests(APITestCase):
    """Test price cannot be manipulated from frontend"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test data
        self.city = City.objects.create(
            name="Test City", slug="test-city", description="Test", status="PUBLISHED"
        )
        self.package = Package.objects.create(
            city=self.city, name="Test Package", slug="test-package", description="Test"
        )
        self.experience = Experience.objects.create(
            name="Test Experience", description="Test", base_price=100.00
        )
        self.hotel_tier = HotelTier.objects.create(
            name="Budget", description="Budget tier", price_multiplier=1.0
        )
        self.transport = TransportOption.objects.create(
            name="Bus", description="Bus transport", base_price=50.00
        )

    def test_booking_serializer_rejects_total_price(self):
        """Booking create serializer must NOT accept total_price"""
        response = self.client.post(
            "/api/bookings/",
            {
                "package_id": self.package.id,
                "selected_experience_ids": [self.experience.id],
                "hotel_tier_id": self.hotel_tier.id,
                "transport_option_id": self.transport.id,
                "total_price": 0.01,  # ← Frontend tries to manipulate
            },
            format="json",
        )

        # Should succeed but ignore the total_price
        self.assertEqual(response.status_code, 201)

        # Verify booking was created with correct price, not 0.01
        booking = Booking.objects.latest("id")
        expected_price = 100.00 + 50.00  # experience + transport
        self.assertEqual(float(booking.total_price), expected_price)
        self.assertNotEqual(float(booking.total_price), 0.01)

    def test_booking_create_validates_components(self):
        """Booking creation must validate all component IDs"""
        response = self.client.post(
            "/api/bookings/",
            {
                "package_id": 99999,  # Non-existent
                "selected_experience_ids": [self.experience.id],
                "hotel_tier_id": self.hotel_tier.id,
                "transport_option_id": self.transport.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("package", response.data.get("non_field_errors", [""])[0].lower())

    def test_price_validation_rejects_mismatched_price(self):
        """Price validation must catch tampering"""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            selected_hotel_tier=self.hotel_tier,
            selected_transport=self.transport,
            total_price=100.00,
            status="DRAFT",
        )
        booking.selected_experiences.add(self.experience)

        # Tamper with the stored price
        booking.total_price = 0.01
        booking.save()

        # Validation should fail
        from bookings.services.booking_service import BookingService

        is_valid = BookingService.validate_price(booking, booking.total_price)

        self.assertFalse(is_valid)


class PaymentWebhookSecurityTests(APITestCase):
    """Test payment webhook validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.city = City.objects.create(
            name="Test City", slug="test-city", description="Test", status="PUBLISHED"
        )
        self.package = Package.objects.create(
            city=self.city, name="Test Package", slug="test-package", description="Test"
        )
        self.experience = Experience.objects.create(
            name="Test Experience", description="Test", base_price=100.00
        )
        self.hotel_tier = HotelTier.objects.create(
            name="Budget", description="Budget tier", price_multiplier=1.0
        )
        self.transport = TransportOption.objects.create(
            name="Bus", description="Bus transport", base_price=50.00
        )
        self.booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            selected_hotel_tier=self.hotel_tier,
            selected_transport=self.transport,
            total_price=150.00,
            status="PENDING_PAYMENT",
        )
        self.booking.selected_experiences.add(self.experience)

    def test_webhook_validates_payment_amount(self):
        """Webhook must validate payment amount matches booking"""
        from payments.models import Payment
        from payments.services.payment_service import RazorpayService

        # Create payment record
        payment = Payment.objects.create(
            booking=self.booking,
            razorpay_order_id="order_123",
            amount=150.00,
            status="PENDING",
        )

        # Create payment entity with wrong amount
        payment_entity = {
            "id": "pay_123",
            "order_id": "order_123",
            "amount": 1,  # 1 paise = ₹0.01 instead of ₹150
            "status": "captured",
        }

        # This should fail validation
        is_valid, message = RazorpayService.validate_payment_against_booking(
            "order_123", payment_entity
        )

        self.assertFalse(is_valid)
        self.assertIn("amount", message.lower())

    def test_webhook_validates_order_id_match(self):
        """Webhook must validate order ID matches"""
        from payments.models import Payment
        from payments.services.payment_service import RazorpayService

        # Create payment record
        payment = Payment.objects.create(
            booking=self.booking,
            razorpay_order_id="order_123",
            amount=150.00,
            status="PENDING",
        )

        # Create payment entity with wrong order ID
        payment_entity = {
            "id": "pay_123",
            "order_id": "order_456",  # Different order ID
            "amount": 15000,  # Correct amount in paise
            "status": "captured",
        }

        # This should fail validation
        is_valid, message = RazorpayService.validate_payment_against_booking(
            "order_123", payment_entity
        )

        self.assertFalse(is_valid)
        self.assertIn("order id", message.lower())


class RateLimitingTests(APITestCase):
    """Test rate limiting functionality"""

    def setUp(self):
        self.client = APIClient()
        self.sync_url = "/api/auth/nextauth-sync/"

    def test_rate_limiting_blocks_excessive_requests(self):
        """Rate limiting should block excessive requests"""
        # Make multiple requests rapidly
        for i in range(15):  # Exceeds 10/minute limit
            response = self.client.post(
                self.sync_url,
                {
                    "email": f"user{i}@example.com",
                    "provider": "google",
                    "uid": f"12345{i}",
                    "token": "test_token",
                },
                format="json",
            )

        # Last request should be rate limited
        self.assertEqual(response.status_code, 429)


class SecurityHeadersTests(TestCase):
    """Test security headers are present"""

    def setUp(self):
        self.client = Client()

    def test_security_headers_present(self):
        """Security headers should be present in responses"""
        response = self.client.get("/")

        # Check for security headers (these would be added by middleware)
        # Note: These tests would pass in production with proper middleware
        self.assertIsNotNone(response.get("X-Content-Type-Options", None))
        self.assertIsNotNone(response.get("X-Frame-Options", None))
