from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import Inquiry
from .serializers import (
    InquiryCreateSerializer,
    InquiryDetailSerializer,
    InquiryListSerializer,
    InquiryUpdateSerializer,
)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class InquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customer inquiries.

    Public endpoints:
    - POST /api/inquiries/ - Submit new inquiry (rate-limited)

    Admin endpoints:
    - GET /api/inquiries/ - List all inquiries
    - GET /api/inquiries/{id}/ - Get inquiry details
    - PATCH /api/inquiries/{id}/ - Update inquiry status/notes
    - DELETE /api/inquiries/{id}/ - Delete inquiry
    """

    queryset = Inquiry.objects.all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return InquiryCreateSerializer
        elif self.action == "list":
            return InquiryListSerializer
        elif self.action in ["update", "partial_update"]:
            return InquiryUpdateSerializer
        return InquiryDetailSerializer

    def get_permissions(self):
        """
        Public: create
        Admin only: list, retrieve, update, destroy
        """
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]

    def create(self, request, *args, **kwargs):
        """
        Create new inquiry with rate limiting and email notifications.
        Rate limit: 5 submissions per hour per IP address.
        """
        # Get client IP for rate limiting
        client_ip = get_client_ip(request)

        # Rate limiting check
        cache_key = f"inquiry_rate_limit_{client_ip}"
        submission_count = cache.get(cache_key, 0)

        if submission_count >= 5:
            return Response(
                {
                    "error": "Rate limit exceeded",
                    "detail": "You have submitted too many inquiries. Please try again in an hour.",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Validate and create inquiry
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Add metadata
        inquiry = serializer.save(
            ip_address=client_ip,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

        # Increment rate limit counter (expires in 1 hour)
        cache.set(cache_key, submission_count + 1, 3600)

        # Send email notifications (async in production)
        self._send_notifications(inquiry)

        # Return success response
        return Response(
            {
                "success": True,
                "message": "Thank you for contacting us! We'll get back to you within 24 hours.",
                "inquiry_id": inquiry.id,
            },
            status=status.HTTP_201_CREATED,
        )

    def _send_notifications(self, inquiry):
        """Send email notifications to admin and customer"""
        try:
            # Admin notification
            admin_subject = (
                f"New Inquiry: {inquiry.get_subject_display()} from {inquiry.name}"
            )
            admin_message = f"""
New inquiry received:

Name: {inquiry.name}
Email: {inquiry.email}
Phone: {inquiry.phone or 'Not provided'}
Subject: {inquiry.get_subject_display()}

Message:
{inquiry.message}

---
Submitted at: {inquiry.created_at.strftime('%Y-%m-%d %H:%M:%S')}
IP Address: {inquiry.ip_address or 'Unknown'}

View in admin: {settings.FRONTEND_URL}/admin/inquiries/inquiry/{inquiry.id}/
            """

            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )

            # Customer confirmation
            customer_subject = "We received your inquiry - ShamBit Travels"
            customer_message = f"""
Dear {inquiry.name},

Thank you for contacting ShamBit Travels!

We have received your inquiry regarding: {inquiry.get_subject_display()}

Our team will review your message and get back to you within 24 hours.

Your inquiry details:
---
Subject: {inquiry.get_subject_display()}
Message: {inquiry.message}
Submitted: {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}

If you have any urgent questions, please feel free to call us at +91 9005457111 or WhatsApp us.

Best regards,
ShamBit Travels Team

---
This is an automated confirmation email. Please do not reply to this email.
            """

            send_mail(
                subject=customer_subject,
                message=customer_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[inquiry.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send inquiry notification emails: {e}")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def mark_resolved(self, request, pk=None):
        """Mark inquiry as resolved"""
        inquiry = self.get_object()
        inquiry.mark_resolved()
        serializer = self.get_serializer(inquiry)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def mark_in_progress(self, request, pk=None):
        """Mark inquiry as in progress"""
        inquiry = self.get_object()
        inquiry.mark_in_progress()
        serializer = self.get_serializer(inquiry)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get inquiry statistics"""
        total = Inquiry.objects.count()
        new = Inquiry.objects.filter(status="NEW").count()
        in_progress = Inquiry.objects.filter(status="IN_PROGRESS").count()
        resolved = Inquiry.objects.filter(status="RESOLVED").count()

        return Response(
            {
                "total": total,
                "new": new,
                "in_progress": in_progress,
                "resolved": resolved,
            }
        )
