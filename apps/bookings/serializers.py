from typing import Optional

from drf_spectacular.utils import extend_schema_field
from packages.serializers import (
    ExperienceSerializer,
    HotelTierSerializer,
    PackageSerializer,
    TransportOptionSerializer,
)
from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying bookings with complete price breakdown"""

    package = PackageSerializer(read_only=True)
    selected_experiences = ExperienceSerializer(many=True, read_only=True)
    selected_hotel_tier = HotelTierSerializer(read_only=True)
    selected_transport = TransportOptionSerializer(read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    booking_reference = serializers.SerializerMethodField()
    price_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "booking_reference",
            "user_email",
            "package",
            "selected_experiences",
            "selected_hotel_tier",
            "selected_transport",
            "booking_date",
            "num_travelers",
            "traveler_details",
            "customer_name",
            "customer_email",
            "customer_phone",
            "special_requests",
            "total_price",
            "total_amount_paid",
            "price_breakdown",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "booking_reference",
            "user_email",
            "total_price",
            "total_amount_paid",
            "price_breakdown",
            "expires_at",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_booking_reference(self, obj) -> str:
        # Generate a user-friendly booking reference
        # Format: SB-YYYY-NNNNNN (e.g., SB-2024-000123)
        year = obj.created_at.year
        return f"SB-{year}-{str(obj.id).zfill(6)}"

    @extend_schema_field(serializers.DictField)
    def get_price_breakdown(self, obj) -> dict:
        """
        SECURITY: All price calculations done on backend.
        Frontend NEVER calculates - only displays these values.
        Includes age-based pricing calculations.
        """
        from decimal import Decimal

        from pricing_engine.services.pricing_service import PricingService

        # Get detailed breakdown from pricing service with traveler details
        breakdown = PricingService.get_price_breakdown(
            obj.package,
            obj.selected_experiences.all(),
            obj.selected_hotel_tier,
            obj.selected_transport,
            obj.traveler_details if obj.traveler_details else None,
        )

        # Per-person price (stored in booking)
        per_person_price = obj.total_price

        # Calculate total based on chargeable travelers if traveler details exist
        if obj.traveler_details and breakdown.get("chargeable_travelers") is not None:
            chargeable_count = breakdown["chargeable_travelers"]
            total_amount = per_person_price * chargeable_count
        else:
            # Fallback to num_travelers if no traveler details
            total_amount = per_person_price * obj.num_travelers
            chargeable_count = obj.num_travelers

        return {
            # Individual component prices (backend calculated)
            "base_experience_total": str(breakdown["base_experience_total"]),
            "transport_cost": str(breakdown["transport_cost"]),
            "subtotal_before_hotel": str(breakdown["subtotal_before_hotel"]),
            "hotel_multiplier": str(breakdown["hotel_multiplier"]),
            "subtotal_after_hotel": str(breakdown["subtotal_after_hotel"]),
            "total_markup": str(breakdown["total_markup"]),
            "total_discount": str(breakdown["total_discount"]),
            "applied_rules": breakdown["applied_rules"],
            # Per-person and total (backend calculated)
            "per_person_price": str(per_person_price),
            "num_travelers": obj.num_travelers,
            "chargeable_travelers": chargeable_count,
            "total_amount": str(total_amount),
            "chargeable_age_threshold": breakdown.get("chargeable_age_threshold", 5),
            # Individual experience prices
            "experiences": [
                {
                    "id": exp.id,
                    "name": exp.name,
                    "price": str(exp.base_price),
                }
                for exp in obj.selected_experiences.all()
            ],
            # Hotel and transport details
            "hotel_tier": {
                "name": obj.selected_hotel_tier.name,
                "multiplier": str(obj.selected_hotel_tier.price_multiplier),
            },
            "transport": {
                "name": obj.selected_transport.name,
                "price": str(obj.selected_transport.base_price),
            },
            # Currency
            "currency": "INR",
            "currency_symbol": "₹",
        }


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Create serializer: DOES NOT accept total_price.
    Price calculated entirely on backend.
    """

    selected_experience_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    # Compatibility alias for older clients
    experience_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    hotel_tier_id = serializers.IntegerField(write_only=True, required=True)
    transport_option_id = serializers.IntegerField(write_only=True, required=True)
    package_id = serializers.IntegerField(write_only=True, required=True)

    # Booking details
    booking_date = serializers.DateField(required=True)
    num_travelers = serializers.IntegerField(required=True, min_value=1)

    # Traveler details with age-based pricing
    traveler_details = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="List of traveler details: [{name, age, gender}, ...]",
    )

    # Customer information (optional for DRAFT bookings)
    customer_name = serializers.CharField(
        required=False, max_length=255, allow_blank=True, default=""
    )
    customer_email = serializers.EmailField(
        required=False, allow_blank=True, default=""
    )
    customer_phone = serializers.CharField(
        required=False, max_length=15, allow_blank=True, default=""
    )
    special_requests = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    class Meta:
        model = Booking
        fields = [
            "package_id",
            "selected_experience_ids",
            "experience_ids",
            "hotel_tier_id",
            "transport_option_id",
            "booking_date",
            "num_travelers",
            "traveler_details",
            "customer_name",
            "customer_email",
            "customer_phone",
            "special_requests",
        ]

    def validate_traveler_details(self, value):
        """Validate traveler details structure"""
        if not value:
            return value

        for i, traveler in enumerate(value):
            # Validate required fields
            if "name" not in traveler:
                raise serializers.ValidationError(
                    f"Traveler {i+1}: 'name' field is required"
                )
            if "age" not in traveler:
                raise serializers.ValidationError(
                    f"Traveler {i+1}: 'age' field is required"
                )

            # Validate age is a valid integer
            try:
                age = int(traveler["age"])
                if age < 0 or age > 120:
                    raise serializers.ValidationError(
                        f"Traveler {i+1}: age must be between 0 and 120"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Traveler {i+1}: age must be a valid number"
                )

            # Validate name is not empty
            if not traveler["name"].strip():
                raise serializers.ValidationError(
                    f"Traveler {i+1}: name cannot be empty"
                )

        return value

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
        """Validate all component IDs exist and traveler details match count"""
        from packages.models import Experience, HotelTier, Package, TransportOption

        # Backward compatibility: accept `experience_ids` and normalize.
        if not data.get("selected_experience_ids") and data.get("experience_ids"):
            data["selected_experience_ids"] = data["experience_ids"]

        experience_ids = data.get("selected_experience_ids", [])
        hotel_tier_id = data.get("hotel_tier_id")
        transport_option_id = data.get("transport_option_id")
        package_id = data.get("package_id")
        num_travelers = data.get("num_travelers")
        traveler_details = data.get("traveler_details", [])

        if not experience_ids:
            raise serializers.ValidationError(
                {"selected_experience_ids": "At least one experience is required"}
            )

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

        # Validate traveler details count matches num_travelers
        if traveler_details and len(traveler_details) != num_travelers:
            raise serializers.ValidationError(
                f"Number of traveler details ({len(traveler_details)}) "
                f"must match num_travelers ({num_travelers})"
            )

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
            traveler_details=validated_data.get("traveler_details", []),
            customer_name=validated_data["customer_name"],
            customer_email=validated_data["customer_email"],
            customer_phone=validated_data["customer_phone"],
            special_requests=validated_data.get("special_requests", ""),
        )

        return booking


class BookingCreateResponseSerializer(serializers.ModelSerializer):
    """Compact booking response for successful booking creation."""

    booking_reference = serializers.SerializerMethodField()
    payment_url = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "booking_reference",
            "status",
            "total_price",
            "total_amount_paid",
            "payment_url",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_booking_reference(self, obj) -> str:
        # Keep compatibility with frontend route that expects a reference.
        return str(obj.id)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_payment_url(self, obj) -> Optional[str]:
        # Placeholder until payment flow wires explicit URL generation.
        return None


class BookingPreviewSerializer(serializers.Serializer):
    """
    Preview booking price with traveler details WITHOUT creating a booking.
    Used on review page to show accurate pricing before submission.
    """

    package_id = serializers.IntegerField(required=True)
    selected_experience_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True
    )
    # Compatibility alias
    experience_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    hotel_tier_id = serializers.IntegerField(required=True)
    transport_option_id = serializers.IntegerField(required=True)
    num_travelers = serializers.IntegerField(required=True, min_value=1)
    traveler_details = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="List of traveler details: [{name, age, gender}, ...]",
    )

    def validate_traveler_details(self, value):
        """Validate traveler details structure"""
        if not value:
            return value

        for i, traveler in enumerate(value):
            if "name" not in traveler:
                raise serializers.ValidationError(
                    f"Traveler {i+1}: 'name' field is required"
                )
            if "age" not in traveler:
                raise serializers.ValidationError(
                    f"Traveler {i+1}: 'age' field is required"
                )

            try:
                age = int(traveler["age"])
                if age < 0 or age > 120:
                    raise serializers.ValidationError(
                        f"Traveler {i+1}: age must be between 0 and 120"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Traveler {i+1}: age must be a valid number"
                )

            if not traveler["name"].strip():
                raise serializers.ValidationError(
                    f"Traveler {i+1}: name cannot be empty"
                )

        return value

    def validate(self, data):
        """Validate all component IDs exist and traveler details match count"""
        from packages.models import Experience, HotelTier, Package, TransportOption

        # Backward compatibility
        if not data.get("selected_experience_ids") and data.get("experience_ids"):
            data["selected_experience_ids"] = data["experience_ids"]

        experience_ids = data.get("selected_experience_ids", [])
        hotel_tier_id = data.get("hotel_tier_id")
        transport_option_id = data.get("transport_option_id")
        package_id = data.get("package_id")
        num_travelers = data.get("num_travelers")
        traveler_details = data.get("traveler_details", [])

        if not experience_ids:
            raise serializers.ValidationError(
                {"selected_experience_ids": "At least one experience is required"}
            )

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

        # Validate traveler details count matches num_travelers
        if traveler_details and len(traveler_details) != num_travelers:
            raise serializers.ValidationError(
                f"Number of traveler details ({len(traveler_details)}) "
                f"must match num_travelers ({num_travelers})"
            )

        return data


class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer for DRAFT bookings only.
    Allows updating booking details before payment.
    """

    selected_experience_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    hotel_tier_id = serializers.IntegerField(write_only=True, required=False)
    transport_option_id = serializers.IntegerField(write_only=True, required=False)

    # Traveler details
    traveler_details = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Booking
        fields = [
            "selected_experience_ids",
            "hotel_tier_id",
            "transport_option_id",
            "booking_date",
            "num_travelers",
            "traveler_details",
            "customer_name",
            "customer_email",
            "customer_phone",
            "special_requests",
        ]

    def validate(self, data):
        """Validate booking can be updated and recalculate price if selections changed"""
        booking = self.instance

        # Only DRAFT bookings can be updated
        if booking.status != "DRAFT":
            raise serializers.ValidationError("Only DRAFT bookings can be updated")

        # Check if booking has expired
        if booking.is_expired():
            raise serializers.ValidationError(
                "This booking has expired and cannot be updated"
            )

        # Validate traveler details count if provided
        num_travelers = data.get("num_travelers", booking.num_travelers)
        traveler_details = data.get("traveler_details")

        if traveler_details is not None and len(traveler_details) != num_travelers:
            raise serializers.ValidationError(
                f"Number of traveler details ({len(traveler_details)}) "
                f"must match num_travelers ({num_travelers})"
            )

        return data

    def validate_traveler_details(self, value):
        """Validate traveler details structure"""
        if not value:
            return value

        for i, traveler in enumerate(value):
            if "name" not in traveler or "age" not in traveler:
                raise serializers.ValidationError(
                    f"Traveler {i+1}: 'name' and 'age' fields are required"
                )

            try:
                age = int(traveler["age"])
                if age < 0 or age > 120:
                    raise serializers.ValidationError(
                        f"Traveler {i+1}: age must be between 0 and 120"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Traveler {i+1}: age must be a valid number"
                )

        return value

    def update(self, instance, validated_data):
        """Update booking and recalculate price if selections changed"""
        from django.db import transaction

        from packages.models import Experience, HotelTier, TransportOption
        from pricing_engine.services.pricing_service import PricingService

        # Check if price-affecting fields changed
        price_changed = False

        experience_ids = validated_data.pop("selected_experience_ids", None)
        hotel_tier_id = validated_data.pop("hotel_tier_id", None)
        transport_option_id = validated_data.pop("transport_option_id", None)

        with transaction.atomic():
            # Update experiences if provided
            if experience_ids is not None:
                experiences = Experience.objects.filter(id__in=experience_ids)
                if len(experiences) != len(experience_ids):
                    raise serializers.ValidationError(
                        "One or more experiences not found"
                    )
                instance.selected_experiences.set(experiences)
                price_changed = True

            # Update hotel tier if provided
            if hotel_tier_id is not None:
                hotel_tier = HotelTier.objects.get(id=hotel_tier_id)
                instance.selected_hotel_tier = hotel_tier
                price_changed = True

            # Update transport option if provided
            if transport_option_id is not None:
                transport_option = TransportOption.objects.get(id=transport_option_id)
                instance.selected_transport = transport_option
                price_changed = True

            # Update other fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            # Recalculate price if selections changed
            if price_changed:
                calculated_price = PricingService.calculate_total(
                    instance.package,
                    instance.selected_experiences.all(),
                    instance.selected_hotel_tier,
                    instance.selected_transport,
                )
                instance.total_price = calculated_price

            instance.save()

        return instance
