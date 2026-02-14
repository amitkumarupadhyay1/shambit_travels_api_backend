import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    @staticmethod
    def send_otp_email(email, otp, purpose="login"):
        """
        Send OTP via email for authentication purposes.

        Args:
            email: Recipient email address
            otp: One-time password to send
            purpose: Purpose of OTP (login, reset_password, etc.)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject_map = {
                "login": "Your Login OTP",
                "reset_password": "Password Reset OTP",
                "verification": "Email Verification OTP",
            }

            subject = subject_map.get(purpose, "Your OTP")
            from_email = settings.DEFAULT_FROM_EMAIL

            # Plain text message
            message = f"""
Hello,

Your OTP for {purpose.replace('_', ' ')} is: {otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Best regards,
ShamBit Team
            """.strip()

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info(f"OTP email sent successfully to {email} for {purpose}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(email, otp):
        """
        Send password reset OTP email.

        Args:
            email: Recipient email address
            otp: One-time password for reset

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        return EmailService.send_otp_email(email, otp, purpose="reset_password")
