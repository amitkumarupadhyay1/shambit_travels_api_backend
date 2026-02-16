from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Experience, HotelTier, Package, TransportOption


class ExperienceSerializer(serializers.ModelSerializer):
    featured_image_url = serializers.SerializerMethodField()
    city_name = serializers.CharField(
        source="city.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Experience
        fields = [
            "id",
            "name",
            "description",
            "base_price",
            "is_active",
            "featured_image_url",
            "duration_hours",
            "max_participants",
            "difficulty_level",
            "category",
            "city_name",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_featured_image_url(self, obj) -> Optional[str]:
        if obj.featured_image and obj.featured_image.file:
            request = self.context.get("request")
            if request:
                url = request.build_absolute_uri(obj.featured_image.file.url)
            else:
                url = obj.featured_image.file.url
            version_source = getattr(obj.featured_image, "updated_at", None) or getattr(
                obj, "updated_at", None
            )
            return self._append_cache_buster(url, version_source)
        return None

    def _append_cache_buster(self, url: str, version_source) -> str:
        if not url or not version_source:
            return url

        # Skip cache-busting for Cloudinary URLs - they have their own versioning
        if "cloudinary.com" in url:
            return url

        timestamp = int(version_source.timestamp())
        parts = urlsplit(url)
        query_params = dict(parse_qsl(parts.query))
        query_params["v"] = str(timestamp)

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query_params),
                parts.fragment,
            )
        )

    def validate_base_price(self, value):
        """Validate base price is within acceptable range"""
        if value < 100:
            raise ValidationError("Base price must be at least ₹100")
        if value > 100000:
            raise ValidationError("Base price cannot exceed ₹100,000")
        return value

    def validate_duration_hours(self, value):
        """Validate duration is positive"""
        if value < 0.5:
            raise ValidationError("Duration must be at least 0.5 hours")
        return value

    def validate_max_participants(self, value):
        """Validate max participants is positive"""
        if value < 1:
            raise ValidationError("Must allow at least 1 participant")
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Ensure name is not empty or just whitespace
        if "name" in data and not data["name"].strip():
            raise ValidationError({"name": "Experience name cannot be empty"})

        # Ensure description is meaningful
        if "description" in data and len(data["description"].strip()) < 50:
            raise ValidationError(
                {"description": "Description must be at least 50 characters"}
            )

        return data


class HotelTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelTier
        fields = ["id", "name", "description", "price_multiplier"]


class TransportOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportOption
        fields = ["id", "name", "description", "base_price"]


class PackageSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, read_only=True)
    hotel_tiers = HotelTierSerializer(many=True, read_only=True)
    transport_options = TransportOptionSerializer(many=True, read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "city_name",
            "experiences",
            "hotel_tiers",
            "transport_options",
            "is_active",
            "created_at",
        ]
