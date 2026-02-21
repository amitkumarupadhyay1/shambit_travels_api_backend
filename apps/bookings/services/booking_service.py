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
        # PHASE 1: New parameters
        booking_end_date=None,
        num_rooms=1,
        room_allocation=None,
        room_preferences="",
    ):
        """
        BACKEND-AUTHORITATIVE: Calculate price and create booking.
        Frontend NEVER sends total_price.

        PHASE 1 UPDATE: Now supports date ranges and room allocation.

        Args:
            traveler_details: List of dicts with 'name', 'age', 'gender' for each traveler
            booking_end_date: Trip end date (PHASE 1)
            num_rooms: Number of rooms required (PHASE 1)
            room_allocation: Room allocation details (PHASE 1)
            room_preferences: User's room preferences (PHASE 1)
        """
        from datetime import timedelta

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

            # PHASE 1: Set default end date if not provided
            if not booking_end_date:
                booking_end_date = booking_date + timedelta(days=1)

            # Calculate price on backend only (per-person price)
            # PHASE 1: Pass date range and room count
            calculated_price = PricingService.calculate_total(
                package,
                experiences,
                hotel_tier,
                transport_option,
                start_date=booking_date,
                end_date=booking_end_date,
                num_rooms=num_rooms,
            )

            # Calculate total amount to be paid (per-person × chargeable travelers)
            if traveler_details:
                chargeable_count = sum(
                    1 for t in traveler_details if t.get("age", 0) >= 5
                )
            else:
                chargeable_count = num_travelers

            total_amount_paid = calculated_price * chargeable_count

            # PHASE 1: Calculate hotel costs separately for breakdown
            hotel_cost_info = PricingService.calculate_hotel_cost(
                hotel_tier, booking_date, booking_end_date, num_rooms
            )

            logger.info(
                f"BOOKING CREATION AUDIT: user={user.id}, package={package.slug}, "
                f"per_person_price={calculated_price}, num_travelers={num_travelers}, "
                f"chargeable_travelers={chargeable_count}, total_amount_paid={total_amount_paid}, "
                f"dates={booking_date} to {booking_end_date}, num_rooms={num_rooms}, "
                f"hotel_cost={hotel_cost_info.get('total_cost')}, "
                f"traveler_ages={[t.get('age') for t in (traveler_details or [])]}, "
                f"components: exp={len(experiences)}, hotel={hotel_tier.name}, transport={transport_option.name}"
            )

            # Create booking with calculated price and all details
            with transaction.atomic():
                booking = Booking.objects.create(
                    user=user,
                    package=package,
                    selected_hotel_tier=hotel_tier,
                    selected_transport=transport_option,
                    total_price=calculated_price,  # Per-person price
                    total_amount_paid=total_amount_paid,  # Total amount to be charged
                    status="DRAFT",
                    # PHASE 1: New date fields
                    booking_date=booking_date,  # Keep for backward compatibility
                    booking_start_date=booking_date,
                    booking_end_date=booking_end_date,
                    # num_nights will be auto-calculated in model save()
                    # PHASE 1: Room fields
                    num_rooms_required=num_rooms,
                    room_allocation=room_allocation or [],
                    room_preferences=room_preferences,
                    # PHASE 1: Hotel cost breakdown
                    hotel_cost_per_night=hotel_cost_info.get("cost_per_night"),
                    total_hotel_cost=hotel_cost_info.get("total_cost"),
                    # Existing fields
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
