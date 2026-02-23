import re
from datetime import date, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email as django_validate_email

from rest_framework import serializers

from .models import Traveler


class TravelerSerializer(serializers.ModelSerializer):
    """Serializer for Traveler model with comprehensive validation and sanitization"""

    age_group = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()  # Age is calculated from date_of_birth

    class Meta:
        model = Traveler
        fields = [
            "id",
            "name",
            "age",
            "gender",
            "email",
            "phone",
            "nationality",
            "aadhaar_number",
            "date_of_birth",
            "age_group",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "age", "created_at", "updated_at", "age_group"]

    def sanitize_text(self, value):
        """
        Sanitize text input by removing dangerous characters
        Allows: letters (including Unicode), numbers, spaces, hyphens, apostrophes, dots
        """
        if not value:
            return value
        # Remove leading/trailing whitespace
        value = value.strip()
        # Remove multiple consecutive spaces
        value = re.sub(r"\s+", " ", value)
        # Remove any HTML-like tags
        value = re.sub(r"<[^>]*>", "", value)
        # Remove control characters except newlines and tabs
        value = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", value)
        return value

    def validate_name(self, value):
        """
        Validate and sanitize name
        - Required field
        - 2-255 characters
        - Supports Unicode (Hindi, etc.)
        - No special characters except spaces, hyphens, apostrophes, dots
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required")

        # Sanitize
        value = self.sanitize_text(value)

        # Length check
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters")
        if len(value) > 255:
            raise serializers.ValidationError("Name must not exceed 255 characters")

        # Pattern check: Allow Unicode letters, spaces, hyphens, apostrophes, dots
        if not re.match(r"^[\w\s\-\'.]+$", value, re.UNICODE):
            raise serializers.ValidationError("Name contains invalid characters")

        return value

    def validate_date_of_birth(self, value):
        """
        Validate date of birth
        - Required field
        - Must be in the past
        - Not more than 150 years ago
        - Not in the future
        """
        if not value:
            raise serializers.ValidationError("Date of birth is required")

        today = date.today()

        # Check if date is in the future
        if value > today:
            raise serializers.ValidationError("Date of birth cannot be in the future")

        # Check if date is more than 150 years ago
        min_date = today - timedelta(days=150 * 365)
        if value < min_date:
            raise serializers.ValidationError(
                "Date of birth cannot be more than 150 years ago"
            )

        return value

    def validate_email(self, value):
        """
        Validate and sanitize email
        - Optional field
        - Must be valid email format
        - Max 254 characters (RFC 5321)
        """
        if not value:
            return value

        # Sanitize
        value = value.strip().lower()

        # Length check
        if len(value) > 254:
            raise serializers.ValidationError("Email must not exceed 254 characters")

        # Use Django's email validator
        try:
            django_validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid email address")

        return value

    def validate_phone(self, value):
        """
        Validate and sanitize phone number
        - Optional field
        - Allows: digits, spaces, hyphens, plus sign, parentheses
        - 10 digits (without leading 0) OR 11 digits (with leading 0)
        """
        if not value:
            return value

        # Sanitize: remove all except digits, spaces, +, -, (, )
        value = re.sub(r"[^\d\s\+\-\(\)]", "", value.strip())

        # Remove extra spaces
        value = re.sub(r"\s+", " ", value)

        # Extract only digits for validation
        digits_only = re.sub(r"\D", "", value)

        # Validation rules:
        # - 10 digits: must NOT start with 0
        # - 11 digits: must start with 0
        if len(digits_only) == 10:
            if digits_only[0] == "0":
                raise serializers.ValidationError(
                    "10-digit phone number cannot start with 0"
                )
        elif len(digits_only) == 11:
            if digits_only[0] != "0":
                raise serializers.ValidationError(
                    "11-digit phone number must start with 0"
                )
        else:
            raise serializers.ValidationError(
                "Phone number must be 10 digits (without leading 0) or 11 digits (with leading 0)"
            )

        return value

    def validate_nationality(self, value):
        """
        Validate and sanitize nationality
        - Optional field
        - 2-100 characters
        - Letters and spaces only
        """
        if not value:
            return value

        # Sanitize
        value = self.sanitize_text(value)

        # Length check
        if len(value) < 2:
            raise serializers.ValidationError(
                "Nationality must be at least 2 characters"
            )

        if len(value) > 100:
            raise serializers.ValidationError(
                "Nationality must not exceed 100 characters"
            )

        # Only letters and spaces
        if not re.match(r"^[a-zA-Z\s]+$", value):
            raise serializers.ValidationError(
                "Nationality must contain only letters and spaces"
            )

        return value

    def validate_aadhaar_number(self, value):
        """
        Validate and sanitize Aadhaar number
        - Optional field
        - Must be exactly 12 digits if provided
        - Remove spaces and hyphens
        """
        if not value:
            return value

        # Remove spaces and hyphens
        value = re.sub(r"[\s\-]", "", value.strip())

        # Must be exactly 12 digits
        if not re.match(r"^\d{12}$", value):
            raise serializers.ValidationError(
                "Aadhaar number must be exactly 12 digits"
            )

        # Basic validation: first digit cannot be 0 or 1
        if value[0] in ["0", "1"]:
            raise serializers.ValidationError("Invalid Aadhaar number format")

        return value

    def validate(self, data):
        """
        Cross-field validation
        """
        # Date of birth is required
        if "date_of_birth" not in data or not data["date_of_birth"]:
            raise serializers.ValidationError(
                {"date_of_birth": "Date of birth is required"}
            )

        return data
