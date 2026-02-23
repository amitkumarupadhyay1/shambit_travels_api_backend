from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Traveler(models.Model):
    """
    Saved traveler profiles for quick booking
    Each user can save multiple travelers (family, friends, etc.)
    """

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    # Ownership
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="travelers",
        help_text="User who owns this traveler profile",
    )

    # Basic Information (Required)
    name = models.CharField(max_length=255, help_text="Full name of the traveler")
    date_of_birth = models.DateField(
        help_text="Date of birth (age will be calculated from this)"
    )

    # Optional Information
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        help_text="Gender of the traveler",
    )
    email = models.EmailField(blank=True, null=True, help_text="Email address")
    phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Phone number"
    )
    nationality = models.CharField(
        max_length=100, blank=True, null=True, help_text="Nationality"
    )
    aadhaar_number = models.CharField(
        max_length=12, blank=True, null=True, help_text="Aadhaar number (optional)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Traveler"
        verbose_name_plural = "Travelers"
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
            models.Index(fields=["user", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.age} years) - {self.user.email}"

    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date

        today = date.today()
        dob = self.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age

    @property
    def age_group(self):
        """Return age group category"""
        age = self.age
        if age < 5:
            return "infant"
        elif age < 12:
            return "child"
        elif age < 18:
            return "teen"
        elif age < 60:
            return "adult"
        else:
            return "senior"
