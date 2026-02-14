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

            # Send email with timeout handling
            from django.core.mail import get_connection

            connection = get_connection(
                fail_silently=False,
                timeout=30,  # 30 second timeout for SMTP connection
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
                connection=connection,
            )

            logger.info(f"OTP email sent successfully to {email} for {purpose}")
            return True

        except OSError as e:
            # Network-related errors (errno 101: Network unreachable)
            logger.error(f"Network error sending OTP email to {email}: {str(e)}")
            logger.error(f"Error code: {e.errno if hasattr(e, 'errno') else 'N/A'}")
            logger.error(
                f"Email settings - HOST: {settings.EMAIL_HOST}, PORT: {settings.EMAIL_PORT}, "
                f"USER: {settings.EMAIL_HOST_USER}, BACKEND: {settings.EMAIL_BACKEND}"
            )
            logger.error(
                "HINT: If running on Railway, Gmail SMTP may be blocked. "
                "Consider using SendGrid, Mailgun, or Resend instead."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(
                f"Email settings - HOST: {settings.EMAIL_HOST}, PORT: {settings.EMAIL_PORT}, "
                f"USER: {settings.EMAIL_HOST_USER}, BACKEND: {settings.EMAIL_BACKEND}"
            )
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
