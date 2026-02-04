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
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, booking):
        amount = int(booking.total_price * 100)  # In paise
        order_data = {
            "amount": amount,
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
                    "amount": booking.total_price,
                    "status": "PENDING",
                },
            )
            logger.info(
                f"Razorpay order created: {razorpay_order['id']} "
                f"for booking {booking.id}, amount={booking.total_price}"
            )
            return razorpay_order
        except Exception as e:
            logger.error(f"Razorpay Order Creation Failed: {str(e)}")
            raise e

    def verify_webhook_signature(self, body, signature, secret=None):
        webhook_secret = secret or getattr(
            settings, "RAZORPAY_WEBHOOK_SECRET", "placeholder_secret"
        )
        try:
            self.client.utility.verify_webhook_signature(
                body, signature, webhook_secret
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    @staticmethod
    def validate_payment_amount(payment, payment_entity):
        """
        Verify that payment amount matches booking total_price.
        Razorpay sends amount in paise; booking is in rupees.
        """
        booking = payment.booking

        # Payment amount from webhook (in paise -> convert to rupees)
        webhook_amount = Decimal(str(payment_entity.get("amount", 0))) / Decimal("100")

        # Expected amount from booking
        expected_amount = booking.total_price

        # Check for exact match
        if webhook_amount != expected_amount:
            logger.error(
                f"PAYMENT AMOUNT MISMATCH for booking {booking.id}: "
                f"webhook=${webhook_amount}, expected=${expected_amount}, "
                f"payment_id={payment_entity.get('id')}"
            )
            return False

        logger.info(
            f"Payment amount verified for booking {booking.id}: ${expected_amount}"
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
