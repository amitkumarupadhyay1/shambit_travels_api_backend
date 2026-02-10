from packages.serializers import (
    ExperienceSerializer,
    HotelTierSerializer,
    PackageSerializer,
    TransportOptionSerializer,
)
from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying bookings"""

    package = PackageSerializer(read_only=True)
    selected_experiences = ExperienceSerializer(many=True, read_only=True)
    selected_hotel_tier = HotelTierSerializer(read_only=True)
    selected_transport = TransportOptionSerializer(read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user_email",
            "package",
            "selected_experiences",
            "selected_hotel_tier",
            "selected_transport",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "total_price",
            "created_at",
            "updated_at",
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Create serializer: DOES NOT accept total_price.
    Price calculated entirely on backend.
    """

    selected_experience_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=True
    )
    hotel_tier_id = serializers.IntegerField(write_only=True, required=True)
    transport_option_id = serializers.IntegerField(write_only=True, required=True)
    package_id = serializers.IntegerField(write_only=True, required=True)

    # Booking details
    booking_date = serializers.DateField(required=True)
    num_travelers = serializers.IntegerField(required=True, min_value=1)

    # Customer information
    customer_name = serializers.CharField(required=True, max_length=255)
    customer_email = serializers.EmailField(required=True)
    customer_phone = serializers.CharField(required=True, max_length=15)
    special_requests = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    class Meta:
        model = Booking
        fields = [
            "package_id",
            "selected_experience_ids",
            "hotel_tier_id",
            "transport_option_id",
            "booking_date",
            "num_travelers",
            "customer_name",
            "customer_email",
            "customer_phone",
            "special_requests",
        ]

    def validate_booking_date(self, value):
        """Validate booking date is at least 3 days in the future"""
        from datetime import date, timedelta

        min_date = date.today() + timedelta(days=3)
        if value < min_date:
            raise serializers.ValidationError(
                f"Booking date must be at least 3 days in advance. Minimum date: {min_date}"
            )
        return value

    def validate(self, data):
        """Validate all component IDs exist"""
        from packages.models import Experience, HotelTier, Package, TransportOption

        experience_ids = data.get("selected_experience_ids", [])
        hotel_tier_id = data.get("hotel_tier_id")
        transport_option_id = data.get("transport_option_id")
        package_id = data.get("package_id")

        # Check package exists
        if not Package.objects.filter(id=package_id).exists():
            raise serializers.ValidationError("Package not found")

        # Check experiences exist
        if experience_ids:
            count = Experience.objects.filter(id__in=experience_ids).count()
            if count != len(experience_ids):
                raise serializers.ValidationError("One or more experiences not found")

        # Check hotel tier exists
        if not HotelTier.objects.filter(id=hotel_tier_id).exists():
            raise serializers.ValidationError("Hotel tier not found")

        # Check transport option exists
        if not TransportOption.objects.filter(id=transport_option_id).exists():
            raise serializers.ValidationError("Transport option not found")

        return data

    def create(self, validated_data):
        """Create booking using service (price calculated here)"""
        from packages.models import Package

        from .services.booking_service import BookingService

        package = Package.objects.get(id=validated_data["package_id"])

        booking = BookingService.calculate_and_create_booking(
            package=package,
            experience_ids=validated_data["selected_experience_ids"],
            hotel_tier_id=validated_data["hotel_tier_id"],
            transport_option_id=validated_data["transport_option_id"],
            user=self.context["request"].user,
            booking_date=validated_data["booking_date"],
            num_travelers=validated_data["num_travelers"],
            customer_name=validated_data["customer_name"],
            customer_email=validated_data["customer_email"],
            customer_phone=validated_data["customer_phone"],
            special_requests=validated_data.get("special_requests", ""),
        )

        return booking
