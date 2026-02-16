"""
Tests for booking state machine implementation.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking
from packages.models import (
    City,
    Experience,
    HotelTier,
    Package,
    TransportOption,
)

User = get_user_model()


class BookingStateMachineTests(TestCase):
    """Test booking state machine transitions."""

    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        # Create city
        self.city = City.objects.create(
            name="Test City", slug="test-city", description="Test description"
        )

        # Create package
        self.package = Package.objects.create(
            name="Test Package",
            slug="test-package",
            city=self.city,
            description="Test package description",
        )

        # Create experience
        self.experience = Experience.objects.create(
            name="Test Experience",
            description="Test experience",
            base_price=1000,
            duration_hours=2,
        )
        self.package.experiences.add(self.experience)

        # Create hotel tier
        self.hotel_tier = HotelTier.objects.create(
            name="Standard", description="Standard hotel", price_multiplier=1.0
        )
        self.package.hotel_tiers.add(self.hotel_tier)

        # Create transport option
        self.transport = TransportOption.objects.create(
            name="Bus", description="Bus transport", base_price=500
        )
        self.package.transport_options.add(self.transport)

    def create_draft_booking(self):
        """Helper to create a DRAFT booking."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            selected_hotel_tier=self.hotel_tier,
            selected_transport=self.transport,
            booking_date=date.today() + timedelta(days=5),
            num_travelers=2,
            total_price=15000,
            status="DRAFT",
        )
        booking.selected_experiences.add(self.experience)
        return booking

    def test_draft_booking_has_expiry(self):
        """Test that DRAFT bookings have expires_at set."""
        booking = self.create_draft_booking()
        self.assertIsNotNone(booking.expires_at)
        # Should expire in approximately 20 minutes
        expected_expiry = timezone.now() + timedelta(minutes=20)
        time_diff = abs((booking.expires_at - expected_expiry).total_seconds())
        self.assertLess(time_diff, 5)  # Within 5 seconds

    def test_draft_to_pending_payment(self):
        """Test valid transition from DRAFT to PENDING_PAYMENT."""
        booking = self.create_draft_booking()
        booking.transition_to("PENDING_PAYMENT")
        booking.refresh_from_db()
        self.assertEqual(booking.status, "PENDING_PAYMENT")

    def test_draft_to_expired(self):
        """Test valid transition from DRAFT to EXPIRED."""
        booking = self.create_draft_booking()
        booking.transition_to("EXPIRED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, "EXPIRED")

    def test_draft_to_cancelled(self):
        """Test valid transition from DRAFT to CANCELLED."""
        booking = self.create_draft_booking()
        booking.transition_to("CANCELLED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, "CANCELLED")

    def test_draft_to_confirmed_invalid(self):
        """Test invalid transition from DRAFT to CONFIRMED."""
        booking = self.create_draft_booking()
        with self.assertRaises(ValidationError):
            booking.transition_to("CONFIRMED")

    def test_pending_payment_to_confirmed(self):
        """Test valid transition from PENDING_PAYMENT to CONFIRMED."""
        booking = self.create_draft_booking()
        booking.transition_to("PENDING_PAYMENT")
        booking.transition_to("CONFIRMED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, "CONFIRMED")

    def test_pending_payment_to_cancelled(self):
        """Test valid transition from PENDING_PAYMENT to CANCELLED."""
        booking = self.create_draft_booking()
        booking.transition_to("PENDING_PAYMENT")
        booking.transition_to("CANCELLED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, "CANCELLED")

    def test_confirmed_to_cancelled(self):
        """Test valid transition from CONFIRMED to CANCELLED."""
        booking = self.create_draft_booking()
        booking.transition_to("PENDING_PAYMENT")
        booking.transition_to("CONFIRMED")
        booking.transition_to("CANCELLED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, "CANCELLED")

    def test_confirmed_to_draft_invalid(self):
        """Test invalid transition from CONFIRMED to DRAFT."""
        booking = self.create_draft_booking()
        booking.transition_to("PENDING_PAYMENT")
        booking.transition_to("CONFIRMED")
        with self.assertRaises(ValidationError):
            booking.transition_to("DRAFT")

    def test_cancelled_is_terminal(self):
        """Test that CANCELLED is a terminal state."""
        booking = self.create_draft_booking()
        booking.transition_to("CANCELLED")
        with self.assertRaises(ValidationError):
            booking.transition_to("DRAFT")
        with self.assertRaises(ValidationError):
            booking.transition_to("PENDING_PAYMENT")
        with self.assertRaises(ValidationError):
            booking.transition_to("CONFIRMED")

    def test_expired_is_terminal(self):
        """Test that EXPIRED is a terminal state."""
        booking = self.create_draft_booking()
        booking.transition_to("EXPIRED")
        with self.assertRaises(ValidationError):
            booking.transition_to("DRAFT")
        with self.assertRaises(ValidationError):
            booking.transition_to("PENDING_PAYMENT")
        with self.assertRaises(ValidationError):
            booking.transition_to("CONFIRMED")

    def test_is_expired_method(self):
        """Test is_expired() method."""
        booking = self.create_draft_booking()
        # Should not be expired initially
        self.assertFalse(booking.is_expired())

        # Set expiry to past
        booking.expires_at = timezone.now() - timedelta(minutes=1)
        booking.save()
        self.assertTrue(booking.is_expired())

    def test_is_expired_only_for_draft(self):
        """Test is_expired() only applies to DRAFT status."""
        booking = self.create_draft_booking()
        booking.transition_to("PENDING_PAYMENT")
        # Should not be expired even if expires_at is in past
        booking.expires_at = timezone.now() - timedelta(minutes=1)
        booking.save()
        self.assertFalse(booking.is_expired())

    def test_can_transition_to(self):
        """Test can_transition_to() method."""
        booking = self.create_draft_booking()

        # DRAFT can transition to these
        self.assertTrue(booking.can_transition_to("PENDING_PAYMENT"))
        self.assertTrue(booking.can_transition_to("EXPIRED"))
        self.assertTrue(booking.can_transition_to("CANCELLED"))

        # DRAFT cannot transition to these
        self.assertFalse(booking.can_transition_to("CONFIRMED"))
        self.assertFalse(booking.can_transition_to("DRAFT"))
