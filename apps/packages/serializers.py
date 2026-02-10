from rest_framework import serializers

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

    def get_featured_image_url(self, obj):
        if obj.featured_image and obj.featured_image.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.featured_image.file.url)
            return obj.featured_image.file.url
        return None


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
