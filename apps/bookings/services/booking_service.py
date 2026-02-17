import logging
from decimal import Decimal

from django.db import transaction

from notifications.services.notification_service import NotificationService
from packages.models import Experience, HotelTier, TransportOption
from pricing_engine.services.pricing_service import PricingService

from ..models import Booking

logger = logging.getLogger(__name__)


class BookingService:
    @staticmethod
    def transition_status(booking, new_status):
        """
        Handles state transitions for bookings with notifications.
        Uses the model's transition_to method for validation.
        """
        from django.core.exceptions import ValidationError

        old_status = booking.status

        try:
            # Use model's transition_to method which validates the transition
            booking.transition_to(new_status)

            # Send appropriate notifications
            try:
                if new_status == "PENDING_PAYMENT":
                    NotificationService.notify_payment_pending(booking)
                elif new_status == "CONFIRMED":
                    NotificationService.notify_booking_confirmed(booking)
                elif new_status == "CANCELLED":
                    NotificationService.notify_booking_cancelled(booking)
            except Exception as e:
                logger.warning(f"Failed to send notification: {str(e)}")
                # Don't fail the transition if notification fails

            logger.info(
                f"Booking {booking.id} transitioned from {old_status} to {new_status}"
            )
            return True

        except ValidationError as e:
            logger.warning(
                f"Invalid transition for Booking {booking.id}: {old_status} -> {new_status}. Error: {str(e)}"
            )
            return False

    @staticmethod
    def calculate_and_create_booking(
        package,
        experience_ids,
        hotel_tier_id,
        transport_option_id,
        user,
        booking_date,
        num_travelers,
        customer_name,
        customer_email,
        customer_phone,
        traveler_details=None,
        special_requests="",
    ):
        """
        BACKEND-AUTHORITATIVE: Calculate price and create booking.
        Frontend NEVER sends total_price.

        Args:
            traveler_details: List of dicts with 'name', 'age', 'gender' for each traveler
        """
        try:
            # Fetch all components
            experiences = Experience.objects.filter(id__in=experience_ids)
            if len(experiences) != len(experience_ids):
                raise ValueError("One or more experiences not found")

            hotel_tier = HotelTier.objects.get(id=hotel_tier_id)
            transport_option = TransportOption.objects.get(id=transport_option_id)

            # Validate traveler details if provided
            if traveler_details:
                if len(traveler_details) != num_travelers:
                    raise ValueError(
                        f"Traveler details count ({len(traveler_details)}) "
                        f"does not match num_travelers ({num_travelers})"
                    )

            # Calculate price on backend only (per-person price)
            calculated_price = PricingService.calculate_total(
                package, experiences, hotel_tier, transport_option
            )

            logger.info(
                f"Booking price calculated for user {user.id}: "
                f"${calculated_price} per person (components: exp={len(experiences)}, "
                f"hotel={hotel_tier.name}, transport={transport_option.name})"
            )

            # Create booking with calculated price and all details
            with transaction.atomic():
                booking = Booking.objects.create(
                    user=user,
                    package=package,
                    selected_hotel_tier=hotel_tier,
                    selected_transport=transport_option,
                    total_price=calculated_price,  # Per-person price
                    status="DRAFT",
                    booking_date=booking_date,
                    num_travelers=num_travelers,
                    traveler_details=traveler_details or [],
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    special_requests=special_requests,
                )
                booking.selected_experiences.set(experiences)

                # Send booking created notification
                try:
                    NotificationService.notify_booking_created(booking)
                except Exception as e:
                    logger.warning(
                        f"Failed to send booking created notification: {str(e)}"
                    )

            return booking

        except Exception as e:
            logger.error(f"Booking creation failed: {str(e)}")
            raise

    @staticmethod
    def validate_price(booking, reference_price=None, tolerance_percent=0.01):
        """
        COMPREHENSIVE price validation with age-based pricing.
        Used to detect tampering or pricing rule changes.

        Args:
            booking: Booking instance
            reference_price: Optional reference price to compare against
            tolerance_percent: Tolerance percentage (default 0.01% for strict validation)

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        try:
            # Recalculate price with traveler details
            recalculated_breakdown = PricingService.get_price_breakdown(
                booking.package,
                booking.selected_experiences.all(),
                booking.selected_hotel_tier,
                booking.selected_transport,
                booking.traveler_details if booking.traveler_details else None,
            )

            # Validate traveler count matches traveler details
            if booking.traveler_details:
                if len(booking.traveler_details) != booking.num_travelers:
                    return False, (
                        f"Traveler count mismatch: {len(booking.traveler_details)} "
                        f"details vs {booking.num_travelers} declared"
                    )

                # Validate chargeable travelers
                chargeable_count = booking.get_chargeable_travelers_count()
                if (
                    recalculated_breakdown.get("chargeable_travelers")
                    != chargeable_count
                ):
                    return False, (
                        f"Chargeable traveler count mismatch: "
                        f"{recalculated_breakdown.get('chargeable_travelers')} "
                        f"calculated vs {chargeable_count} from booking"
                    )

            # Get per-person price from recalculation
            recalculated_per_person = recalculated_breakdown["final_total"]

            # Validate per-person price (strict - no tolerance for per-person)
            if booking.total_price != recalculated_per_person:
                difference = abs(booking.total_price - recalculated_per_person)
                tolerance = recalculated_per_person * Decimal(
                    str(tolerance_percent / 100)
                )

                if difference > tolerance:
                    logger.warning(
                        f"Booking {booking.id} per-person price mismatch: "
                        f"stored=${booking.total_price}, recalculated=${recalculated_per_person}, "
                        f"diff=${difference} (tolerance=${tolerance})"
                    )
                    return False, (
                        f"Price mismatch: stored ${booking.total_price} vs "
                        f"recalculated ${recalculated_per_person}"
                    )

            logger.info(f"Booking {booking.id} price validation passed")
            return True, None

        except Exception as e:
            logger.error(f"Price validation error for booking {booking.id}: {str(e)}")
            return False, f"Validation error: {str(e)}"
