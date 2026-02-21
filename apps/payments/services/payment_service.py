import logging
from decimal import Decimal

from django.conf import settings

import razorpay
from bookings.models import Booking

from ..models import Payment

logger = logging.getLogger(__name__)


class RazorpayService:
    def __init__(self):
        self.key_id = getattr(settings, "RAZORPAY_KEY_ID", "rzp_test_placeholder")
        self.key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "placeholder_secret")
        try:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}")
            self.client = None

    def create_order(self, booking):
        """
        Create Razorpay order with correct total amount.
        Uses stored total_amount_paid (source of truth) or calculates as fallback.
        """
        # Use stored total_amount_paid (preferred - source of truth)
        if booking.total_amount_paid:
            total_amount = booking.total_amount_paid
            logger.info(
                f"Using stored total_amount_paid for booking {booking.id}: ${total_amount}"
            )
        else:
            # Fallback for old bookings without total_amount_paid
            per_person_price = booking.total_price
            chargeable_travelers = booking.get_chargeable_travelers_count()
            total_amount = per_person_price * chargeable_travelers
            logger.warning(
                f"Fallback calculation for booking {booking.id}: "
                f"per_person=${per_person_price} × {chargeable_travelers} = ${total_amount}"
            )

        amount_in_paise = int(total_amount * 100)  # Convert to paise

        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"booking_{booking.id}",
            "payment_capture": 1,
        }
        try:
            razorpay_order = self.client.order.create(data=order_data)
            Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": total_amount,  # Store total amount
                    "status": "PENDING",
                },
            )
            logger.info(
                f"Razorpay order created: {razorpay_order['id']} "
                f"for booking {booking.id}, total_amount=${total_amount}, "
                f"amount_in_paise={amount_in_paise}"
            )
            return razorpay_order
        except Exception as e:
            logger.error(f"Razorpay Order Creation Failed: {str(e)}")
            raise e

    def verify_webhook_signature(self, body, signature, secret=None):
        webhook_secret = secret or getattr(
            settings, "RAZORPAY_WEBHOOK_SECRET", "placeholder_secret"
        )

        if not signature:
            logger.warning("No signature provided in webhook request")
            return False

        if not self.client:
            logger.error("Razorpay client not initialized")
            return False

        try:
            self.client.utility.verify_webhook_signature(
                body, signature, webhook_secret
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            return False

    @staticmethod
    def validate_payment_amount(payment, payment_entity):
        """
        Verify that payment amount matches booking total amount.
        Razorpay sends amount in paise; booking is in rupees.
        Uses stored total_amount_paid (source of truth) or calculates as fallback.
        """
        booking = payment.booking

        # Payment amount from webhook (in paise -> convert to rupees)
        webhook_amount = Decimal(str(payment_entity.get("amount", 0))) / Decimal("100")

        # Expected amount: use stored total_amount_paid or calculate
        if booking.total_amount_paid:
            expected_amount = booking.total_amount_paid
        else:
            # Fallback for old bookings
            per_person_price = booking.total_price
            chargeable_travelers = booking.get_chargeable_travelers_count()
            expected_amount = per_person_price * chargeable_travelers

        # Check for exact match
        if webhook_amount != expected_amount:
            logger.error(
                f"PAYMENT AMOUNT MISMATCH for booking {booking.id}: "
                f"webhook=${webhook_amount}, expected=${expected_amount}, "
                f"per_person=${booking.total_price}, "
                f"chargeable_travelers={booking.get_chargeable_travelers_count()}, "
                f"payment_id={payment_entity.get('id')}"
            )
            return False

        logger.info(
            f"Payment amount verified for booking {booking.id}: ${expected_amount} "
            f"(stored_total_amount_paid=${booking.total_amount_paid})"
        )
        return True

    @staticmethod
    def validate_payment_against_booking(razorpay_order_id, payment_entity):
        """
        Full validation before marking payment SUCCESS.
        """
        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

            # Verify order ID matches
            webhook_order_id = payment_entity.get("order_id")
            if webhook_order_id != razorpay_order_id:
                logger.error(
                    f"Order ID mismatch: webhook has {webhook_order_id}, "
                    f"expected {razorpay_order_id}"
                )
                return False, "Order ID mismatch"

            # Verify payment amount
            if not RazorpayService.validate_payment_amount(payment, payment_entity):
                return False, "Payment amount does not match booking"

            # Verify payment status is captured
            if payment_entity.get("status") != "captured":
                logger.warning(
                    f"Payment not in captured status: {payment_entity.get('status')}"
                )
                return False, "Payment not captured"

            return True, "Payment validated successfully"

        except Payment.DoesNotExist:
            logger.error(f"Payment not found for order {razorpay_order_id}")
            return False, "Payment record not found"
        except Exception as e:
            logger.error(f"Payment validation error: {str(e)}")
            return False, str(e)
