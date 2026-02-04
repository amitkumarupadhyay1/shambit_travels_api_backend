import json
import logging

from bookings.services.booking_service import BookingService
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import Payment
from .services.payment_service import RazorpayService

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def razorpay_webhook(request):
    """
    Razorpay webhook handler with FULL VALIDATION.
    """
    signature = request.headers.get("X-Razorpay-Signature")
    body = request.body.decode("utf-8")

    # Step 1: Verify webhook signature
    razorpay_service = RazorpayService()
    if not razorpay_service.verify_webhook_signature(body, signature):
        logger.warning(f"Invalid Razorpay signature detected")
        return HttpResponse(status=400)

    data = json.loads(body)
    event = data.get("event")

    logger.info(f"Razorpay webhook event received: {event}")

    if event == "payment.captured":
        payment_entity = data["payload"]["payment"]["entity"]
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        # Step 2: Validate payment against booking
        is_valid, validation_message = RazorpayService.validate_payment_against_booking(
            order_id, payment_entity
        )

        if not is_valid:
            logger.error(
                f"Payment validation failed for order {order_id}: {validation_message}"
            )
            # Still return 200 to acknowledge webhook, but DON'T transition booking
            return HttpResponse(status=200)

        # Step 3: Atomically update payment and booking
        try:
            with transaction.atomic():
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.razorpay_payment_id = payment_id
                payment.status = "SUCCESS"
                payment.save(update_fields=["razorpay_payment_id", "status"])

                # Transition booking to CONFIRMED
                success = BookingService.transition_status(payment.booking, "CONFIRMED")

                if success:
                    logger.info(
                        f"Payment SUCCESS and booking CONFIRMED: "
                        f"order={order_id}, payment={payment_id}, booking={payment.booking.id}"
                    )
                else:
                    logger.error(
                        f"Failed to transition booking to CONFIRMED: "
                        f"booking={payment.booking.id}"
                    )
                    # Transaction rolled back
                    return HttpResponse(status=500)

        except Payment.DoesNotExist:
            logger.error(f"Payment not found for order {order_id}")
            return HttpResponse(status=404)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return HttpResponse(status=500)

    elif event == "payment.failed":
        payment_entity = data["payload"]["payment"]["entity"]
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        try:
            with transaction.atomic():
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.razorpay_payment_id = payment_id
                payment.status = "FAILED"
                payment.save(update_fields=["razorpay_payment_id", "status"])

                # Revert booking to DRAFT
                BookingService.transition_status(payment.booking, "DRAFT")

                logger.warning(
                    f"Payment FAILED: order={order_id}, payment={payment_id}, "
                    f"booking={payment.booking.id} reverted to DRAFT"
                )
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for failed event: {order_id}")
        except Exception as e:
            logger.error(f"Failed payment processing error: {str(e)}")

    return HttpResponse(status=200)
