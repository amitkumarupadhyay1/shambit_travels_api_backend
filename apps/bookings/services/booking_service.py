from decimal import Decimal
from django.db import transaction
from ..models import Booking
from packages.models import Experience, HotelTier, TransportOption
from pricing_engine.services.pricing_service import PricingService
from notifications.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

class BookingService:
    @staticmethod
    def transition_status(booking, new_status):
        """
        Handles state transitions for bookings with notifications.
        """
        old_status = booking.status
        if booking.can_transition_to(new_status):
            booking.status = new_status
            booking.save()
            
            # Send appropriate notifications
            try:
                if new_status == 'PENDING_PAYMENT':
                    NotificationService.notify_payment_pending(booking)
                elif new_status == 'CONFIRMED':
                    NotificationService.notify_booking_confirmed(booking)
                elif new_status == 'CANCELLED':
                    NotificationService.notify_booking_cancelled(booking)
            except Exception as e:
                logger.warning(f"Failed to send notification: {str(e)}")
                # Don't fail the transition if notification fails
            
            logger.info(f"Booking {booking.id} transitioned from {old_status} to {new_status}")
            return True
        
        logger.warning(f"Invalid transition for Booking {booking.id}: {old_status} -> {new_status}")
        return False
    
    @staticmethod
    def calculate_and_create_booking(package, experience_ids, hotel_tier_id, 
                                   transport_option_id, user):
        """
        BACKEND-AUTHORITATIVE: Calculate price and create booking.
        Frontend NEVER sends total_price.
        """
        try:
            # Fetch all components
            experiences = Experience.objects.filter(id__in=experience_ids)
            if len(experiences) != len(experience_ids):
                raise ValueError("One or more experiences not found")
            
            hotel_tier = HotelTier.objects.get(id=hotel_tier_id)
            transport_option = TransportOption.objects.get(id=transport_option_id)
            
            # Calculate price on backend only
            calculated_price = PricingService.calculate_total(
                package, experiences, hotel_tier, transport_option
            )
            
            logger.info(
                f"Booking price calculated for user {user.id}: "
                f"${calculated_price} (components: exp={len(experiences)}, "
                f"hotel={hotel_tier.name}, transport={transport_option.name})"
            )
            
            # Create booking with calculated price
            with transaction.atomic():
                booking = Booking.objects.create(
                    user=user,
                    package=package,
                    selected_hotel_tier=hotel_tier,
                    selected_transport=transport_option,
                    total_price=calculated_price,
                    status='DRAFT'
                )
                booking.selected_experiences.set(experiences)
                
                # Send booking created notification
                try:
                    NotificationService.notify_booking_created(booking)
                except Exception as e:
                    logger.warning(f"Failed to send booking created notification: {str(e)}")
            
            return booking
        
        except Exception as e:
            logger.error(f"Booking creation failed: {str(e)}")
            raise
    
    @staticmethod
    def validate_price(booking, reference_price, tolerance_percent=0.5):
        """
        Validate that booking price matches recalculated price.
        Used to detect tampering or pricing rule changes.
        """
        # Recalculate price
        recalculated = PricingService.calculate_total(
            booking.package,
            booking.selected_experiences.all(),
            booking.selected_hotel_tier,
            booking.selected_transport
        )
        
        # Check if prices match within tolerance
        tolerance = recalculated * Decimal(str(tolerance_percent / 100))
        difference = abs(booking.total_price - recalculated)
        
        if difference > tolerance:
            logger.warning(
                f"Booking {booking.id} price mismatch: "
                f"stored=${booking.total_price}, recalculated=${recalculated}, "
                f"diff=${difference} (tolerance=${tolerance})"
            )
            return False
        
        return True
