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
    def _validate_vehicle_allocation(vehicle_allocation, num_travelers, start_date, end_date):
        """
        Validate vehicle allocation structure and capacity.

        Args:
            vehicle_allocation: List of {"transport_option_id": int, "count": int}
            num_travelers: Number of travelers
            start_date: Trip start date
            end_date: Trip end date

        Raises:
            ValueError: If validation fails
        """
        from math import ceil

        if not isinstance(vehicle_allocation, list):
            raise ValueError("vehicle_allocation must be a list")

        if len(vehicle_allocation) == 0:
            raise ValueError("vehicle_allocation cannot be empty")

        seen_ids = set()
        total_capacity = 0

        for allocation in vehicle_allocation:
            if not isinstance(allocation, dict):
                raise ValueError("Each allocation must be a dictionary")

            transport_id = allocation.get("transport_option_id")
            count = allocation.get("count", 0)

            if not transport_id:
                raise ValueError("transport_option_id is required")

            if count < 1:
                raise ValueError(f"count must be at least 1 for transport_option_id {transport_id}")

            if transport_id in seen_ids:
                raise ValueError(f"Duplicate transport_option_id: {transport_id}")

            seen_ids.add(transport_id)

            # Validate transport option exists and is active
            try:
                transport = TransportOption.objects.get(id=transport_id)
                if not transport.is_active:
                    raise ValueError(f"Transport option {transport_id} is not active")

                total_capacity += transport.passenger_capacity * count
            except TransportOption.DoesNotExist:
                raise ValueError(f"Transport option {transport_id} not found")

        # Validate total capacity meets passenger count
        if total_capacity < num_travelers:
            raise ValueError(
                f"Vehicle allocation capacity ({total_capacity}) is less than "
                f"passenger count ({num_travelers})"
            )

        logger.info(
            f"Vehicle allocation validated: {len(vehicle_allocation)} vehicle types, "
            f"total capacity {total_capacity} for {num_travelers} passengers"
        )

    @staticmethod
    def get_canonical_amounts(booking, recalculated_total=None):
        """
        Resolve total/per-person amounts in a backward-compatible way.

        Priority:
        1) total_amount_paid (new source of truth)
        2) total_price interpreted as aggregate total
        3) legacy fallback: total_price interpreted as per-person (x chargeable travelers)
        """
        chargeable_count = booking.get_chargeable_travelers_count()
        quant = Decimal("0.01")

        if booking.total_amount_paid is not None:
            total_amount = booking.total_amount_paid.quantize(quant)
        else:
            aggregate_candidate = booking.total_price.quantize(quant)
            legacy_candidate = (
                booking.total_price * Decimal(str(max(chargeable_count, 1)))
            ).quantize(quant)

            if recalculated_total is not None:
                recalculated_total = Decimal(str(recalculated_total)).quantize(quant)
                aggregate_diff = abs(aggregate_candidate - recalculated_total)
                legacy_diff = abs(legacy_candidate - recalculated_total)
                total_amount = (
                    aggregate_candidate
                    if aggregate_diff <= legacy_diff
                    else legacy_candidate
                )
            else:
                total_amount = aggregate_candidate

        if chargeable_count > 0:
            per_person_amount = (
                total_amount / Decimal(str(chargeable_count))
            ).quantize(quant)
        else:
            per_person_amount = total_amount

        return {
            "total_amount": total_amount,
            "per_person_amount": per_person_amount,
            "chargeable_travelers": chargeable_count,
        }

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
        # VEHICLE OPTIMIZATION: New parameter
        vehicle_allocation=None,
    ):
        """
        BACKEND-AUTHORITATIVE: Calculate price and create booking.
        Frontend NEVER sends total_price.

        PHASE 1 UPDATE: Now supports date ranges and room allocation.
        VEHICLE OPTIMIZATION: Now supports vehicle_allocation override.

        Args:
            traveler_details: List of dicts with 'name', 'age', 'gender' for each traveler
            booking_end_date: Trip end date (PHASE 1)
            num_rooms: Number of rooms required (PHASE 1)
            room_allocation: Room allocation details (PHASE 1)
            room_preferences: User's room preferences (PHASE 1)
            vehicle_allocation: Optional list of {"transport_option_id": int, "count": int}
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

            # VEHICLE OPTIMIZATION: Validate vehicle_allocation if provided
            if vehicle_allocation:
                BookingService._validate_vehicle_allocation(
                    vehicle_allocation, num_travelers, booking_date, booking_end_date
                )

            # PHASE 1: Set default end date if not provided
            if not booking_end_date:
                booking_end_date = booking_date + timedelta(days=1)

            # Calculate total price on backend only (aggregate for all chargeable travelers)
            # PHASE 1: Pass date range and room count
            # VEHICLE OPTIMIZATION: Pass vehicle_allocation
            calculated_price = PricingService.calculate_total(
                package,
                experiences,
                hotel_tier,
                transport_option,
                travelers=traveler_details if traveler_details else None,
                start_date=booking_date,
                end_date=booking_end_date,
                num_rooms=num_rooms,
                num_travelers=num_travelers,
                vehicle_allocation=vehicle_allocation,
            )

            # calculated_price is the TOTAL for all chargeable travelers.
            # Set total_amount_paid to the same aggregate total.
            total_amount_paid = calculated_price

            age_threshold = PricingService.get_chargeable_age_threshold()
            if traveler_details:
                chargeable_count = sum(
                    1 for t in traveler_details if t.get("age", 0) >= age_threshold
                )
            else:
                chargeable_count = num_travelers

            # PHASE 1: Calculate hotel costs separately for breakdown
            hotel_cost_info = PricingService.calculate_hotel_cost(
                hotel_tier, booking_date, booking_end_date, num_rooms
            )

            logger.info(
                f"BOOKING CREATION AUDIT: user={user.id}, package={package.slug}, "
                f"total_price={calculated_price}, num_travelers={num_travelers}, "
                f"chargeable_travelers={chargeable_count}, total_amount_paid={total_amount_paid}, "
                f"chargeable_age_threshold={age_threshold}, "
                f"dates={booking_date} to {booking_end_date}, num_rooms={num_rooms}, "
                f"hotel_cost={hotel_cost_info.get('total_cost')}, "
                f"vehicle_allocation={vehicle_allocation}, "
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
                    vehicle_allocation=vehicle_allocation or [],
                    total_price=calculated_price,  # Aggregate total price
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
                start_date=booking.booking_start_date or booking.booking_date,
                end_date=booking.booking_end_date,
                num_rooms=booking.num_rooms_required,
                num_travelers=booking.num_travelers,
                vehicle_allocation=booking.vehicle_allocation if booking.vehicle_allocation else None,
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

            recalculated_total = recalculated_breakdown["final_total"]
            canonical_amounts = BookingService.get_canonical_amounts(
                booking, recalculated_total=recalculated_total
            )
            stored_total = canonical_amounts["total_amount"]

            difference = abs(stored_total - recalculated_total)
            tolerance = recalculated_total * Decimal(str(tolerance_percent / 100))

            if difference > tolerance:
                logger.warning(
                    f"Booking {booking.id} total price mismatch: "
                    f"stored=${stored_total}, recalculated=${recalculated_total}, "
                    f"diff=${difference} (tolerance=${tolerance})"
                )
                return False, (
                    f"Price mismatch: stored ${stored_total} vs "
                    f"recalculated ${recalculated_total}"
                )

            logger.info(f"Booking {booking.id} price validation passed")
            return True, None

        except Exception as e:
            logger.error(f"Price validation error for booking {booking.id}: {str(e)}")
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def detect_price_change(
        package,
        experiences,
        hotel_tier,
        transport_option,
        previous_price,
        start_date=None,
        end_date=None,
        num_rooms=1,
        num_travelers=1,
    ):
        """
        PHASE 3: Detect significant price changes between preview and booking.

        Args:
            package: Package instance
            experiences: QuerySet of Experience instances
            hotel_tier: HotelTier instance
            transport_option: TransportOption instance
            previous_price: Previously calculated price (from preview)
            start_date: Booking start date
            end_date: Booking end date
            num_rooms: Number of rooms
            num_travelers: Number of travelers

        Returns:
            dict: {
                'changed': bool,
                'old_price': Decimal,
                'new_price': Decimal,
                'change_percent': Decimal,
                'exceeds_threshold': bool,
                'message': str
            }
        """
        from pricing_engine.models import PricingConfiguration

        try:
            # Get configuration
            config = PricingConfiguration.get_config()

            # Recalculate current price
            breakdown = PricingService.get_price_breakdown(
                package,
                experiences,
                hotel_tier,
                transport_option,
                start_date=start_date,
                end_date=end_date,
                num_rooms=num_rooms,
                num_travelers=num_travelers,
            )

            current_price = breakdown["final_total"]
            previous_price = Decimal(str(previous_price))

            # Calculate change
            if previous_price == 0:
                change_percent = Decimal("0")
            else:
                change_percent = abs(
                    (current_price - previous_price) / previous_price * 100
                )

            exceeds_threshold = change_percent > config.price_change_alert_threshold

            result = {
                "changed": current_price != previous_price,
                "old_price": previous_price,
                "new_price": current_price,
                "change_percent": change_percent,
                "exceeds_threshold": exceeds_threshold,
                "message": "",
            }

            if result["changed"]:
                direction = (
                    "increased" if current_price > previous_price else "decreased"
                )
                result["message"] = (
                    f"Price {direction} from ₹{previous_price} to ₹{current_price} "
                    f"({change_percent:.2f}% change)"
                )

                # Log significant changes
                if exceeds_threshold:
                    logger.warning(
                        f"SIGNIFICANT PRICE CHANGE DETECTED: Package {package.slug}, "
                        f"Old: ₹{previous_price}, New: ₹{current_price}, "
                        f"Change: {change_percent:.2f}% (Threshold: {config.price_change_alert_threshold}%)"
                    )

                    # Send admin alert if enabled
                    if config.enable_price_change_alerts:
                        try:
                            NotificationService.notify_admin_price_change(
                                package=package,
                                old_price=previous_price,
                                new_price=current_price,
                                change_percent=change_percent,
                            )
                        except Exception as e:
                            logger.error(f"Failed to send price change alert: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Price change detection failed: {str(e)}")
            return {
                "changed": False,
                "old_price": previous_price,
                "new_price": previous_price,
                "change_percent": Decimal("0"),
                "exceeds_threshold": False,
                "message": f"Error: {str(e)}",
            }
