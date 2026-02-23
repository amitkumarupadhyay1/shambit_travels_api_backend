import logging
import os
import random
import string

from django.conf import settings
from django.core.cache import cache

import requests

logger = logging.getLogger(__name__)


class OTPService:
    ERROR_MESSAGES = {
        "GENERATE_FAILED": "Failed to generate OTP",
        "SEND_FAILED": "Failed to send OTP",
        "VERIFY_FAILED": "Invalid OTP",
        "EXPIRED": "OTP has expired",
    }

    @staticmethod
    def generate_otp(length=6):
        """Generate a numeric OTP of given length"""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def get_cache_key(identifier, purpose="login"):
        """Generate cache key for OTP"""
        return f"otp:{purpose}:{identifier}"

    @staticmethod
    def store_otp(identifier, otp, purpose="login", ttl=300):
        """Store OTP in cache with TTL (default 5 mins)"""
        key = OTPService.get_cache_key(identifier, purpose)
        cache.set(key, otp, timeout=ttl)

    @staticmethod
    def verify_otp(identifier, otp, purpose="login"):
        """Verify OTP against cache"""
        key = OTPService.get_cache_key(identifier, purpose)
        cached_otp = cache.get(key)

        if cached_otp and str(cached_otp) == str(otp):
            cache.delete(key)  # Delete after successful verification
            return True
        return False

    @staticmethod
    def send_otp(phone, otp):
        """
        Send OTP via Fast2SMS API.
        Requires FAST2SMS_API_KEY in settings or env.
        """
        api_key = getattr(
            settings, "FAST2SMS_API_KEY", os.environ.get("FAST2SMS_API_KEY")
        )

        if not api_key:
            logger.warning(f"Fast2SMS API key not found. OTP for {phone}: {otp}")
            # For development, just log it and return Success
            if settings.DEBUG:
                return True
            return False

        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "otp",
            "variables_values": otp,
            "numbers": phone,
        }
        headers = {
            "authorization": api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("return") == True:  # noqa: E712
                logger.info(f"OTP sent successfully to {phone}")
                return True
            else:
                logger.error(f"Fast2SMS error: {data}")
                return False

        except Exception as e:
            logger.error(f"Failed to send OTP to {phone}: {str(e)}")
            return False

    @staticmethod
    def send_booking_confirmation_sms(booking):
        """
        Send booking confirmation SMS.

        Args:
            booking: Booking instance

        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        api_key = getattr(
            settings, "FAST2SMS_API_KEY", os.environ.get("FAST2SMS_API_KEY")
        )

        if not api_key:
            logger.warning(
                f"Fast2SMS API key not found. Booking confirmation for {booking.customer_phone}"
            )
            if settings.DEBUG:
                logger.info(
                    f"[DEV] Booking confirmation SMS for {booking.customer_phone}: "
                    f"Ref: {booking.booking_reference}, Package: {booking.package.name}"
                )
                return True
            return False

        phone = booking.customer_phone
        if not phone:
            logger.warning(f"No phone number for booking {booking.id}")
            return False

        # SMS message
        message = (
            f"Booking Confirmed! Ref: {booking.booking_reference}. "
            f"Package: {booking.package.name}. "
            f"Date: {booking.booking_date}. "
            f"Download voucher from your account. -ShamBit Travels"
        )

        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": phone,
        }
        headers = {
            "authorization": api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("return") == True:  # noqa: E712
                logger.info(
                    f"Booking confirmation SMS sent to {phone} for booking {booking.id}"
                )
                return True
            else:
                logger.error(f"Fast2SMS error for booking {booking.id}: {data}")
                return False

        except Exception as e:
            logger.error(
                f"Failed to send booking confirmation SMS for booking {booking.id}: {str(e)}"
            )
            return False
