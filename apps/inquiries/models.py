from django.db import models
from django.utils import timezone


class Inquiry(models.Model):
    """
    Customer inquiry/contact form submissions.
    Stores messages from the contact page for admin review and response.
    """

    STATUS_CHOICES = [
        ("NEW", "New"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
    ]

    SUBJECT_CHOICES = [
        ("booking", "Booking Inquiry"),
        ("package", "Package Customization"),
        ("support", "Customer Support"),
        ("feedback", "Feedback"),
        ("other", "Other"),
    ]

    # Customer Information
    name = models.CharField(max_length=255, help_text="Customer's full name")
    email = models.EmailField(help_text="Customer's email address")
    phone = models.CharField(
        max_length=20, blank=True, help_text="Customer's phone number (optional)"
    )

    # Inquiry Details
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES,
        default="other",
        help_text="Inquiry subject/category",
    )
    message = models.TextField(help_text="Customer's message")

    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="NEW",
        db_index=True,
        help_text="Current status of the inquiry",
    )

    # Admin Management
    admin_notes = models.TextField(
        blank=True, help_text="Internal notes for admin use only"
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True, help_text="When the inquiry was resolved"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text="When the inquiry was submitted"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")

    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="Submitter's IP address for spam prevention"
    )
    user_agent = models.TextField(
        blank=True, help_text="Browser user agent for analytics"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Inquiry"
        verbose_name_plural = "Inquiries"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.status})"

    def mark_resolved(self):
        """Mark inquiry as resolved"""
        self.status = "RESOLVED"
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def mark_in_progress(self):
        """Mark inquiry as in progress"""
        self.status = "IN_PROGRESS"
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_new(self):
        """Check if inquiry is new"""
        return self.status == "NEW"

    @property
    def response_time(self):
        """Calculate response time if resolved"""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
