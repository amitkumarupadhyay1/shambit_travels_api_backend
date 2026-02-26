from rest_framework import serializers

from .models import Inquiry


class InquiryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new inquiries (public endpoint).
    Only accepts customer-facing fields.
    """

    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "subject", "message"]
        extra_kwargs = {
            "name": {"required": True},
            "email": {"required": True},
            "message": {"required": True},
        }

    def validate_email(self, value):
        """Validate email format"""
        if not value or "@" not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.lower().strip()

    def validate_name(self, value):
        """Validate name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Please provide your full name (at least 2 characters)."
            )
        return value.strip()

    def validate_message(self, value):
        """Validate message"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Please provide a message with at least 10 characters."
            )
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Message is too long. Please keep it under 5000 characters."
            )
        return value.strip()

    def validate_phone(self, value):
        """Validate phone if provided"""
        if value:
            # Remove common formatting characters
            cleaned = (
                value.replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
            if not cleaned.replace("+", "").isdigit():
                raise serializers.ValidationError(
                    "Please provide a valid phone number."
                )
        return value.strip() if value else ""


class InquiryListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing inquiries (admin endpoint).
    Includes all fields except sensitive metadata.
    """

    subject_display = serializers.CharField(
        source="get_subject_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    response_time = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "subject",
            "subject_display",
            "message",
            "status",
            "status_display",
            "admin_notes",
            "resolved_at",
            "created_at",
            "updated_at",
            "response_time",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "resolved_at"]

    def get_response_time(self, obj):
        """Get response time in human-readable format"""
        if obj.response_time:
            total_seconds = int(obj.response_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 24:
                days = hours // 24
                return f"{days} day{'s' if days > 1 else ''}"
            elif hours > 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{minutes} minute{'s' if minutes > 1 else ''}"
        return None


class InquiryDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for inquiry details (admin endpoint).
    Includes all fields including metadata.
    """

    subject_display = serializers.CharField(
        source="get_subject_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "subject",
            "subject_display",
            "message",
            "status",
            "status_display",
            "admin_notes",
            "resolved_at",
            "created_at",
            "updated_at",
            "ip_address",
            "user_agent",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "ip_address",
            "user_agent",
        ]


class InquiryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating inquiries (admin endpoint).
    Only allows updating status and admin notes.
    """

    class Meta:
        model = Inquiry
        fields = ["status", "admin_notes"]

    def validate_status(self, value):
        """Validate status transition"""
        if value not in ["NEW", "IN_PROGRESS", "RESOLVED"]:
            raise serializers.ValidationError("Invalid status value.")
        return value
