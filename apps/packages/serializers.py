from rest_framework import serializers
from .models import Package, Experience, HotelTier, TransportOption

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'name', 'description', 'base_price', 'created_at']

class HotelTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelTier
        fields = ['id', 'name', 'description', 'price_multiplier']

class TransportOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportOption
        fields = ['id', 'name', 'description', 'base_price']

class PackageSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, read_only=True)
    hotel_tiers = HotelTierSerializer(many=True, read_only=True)
    transport_options = TransportOptionSerializer(many=True, read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = Package
        fields = [
            'id', 'name', 'slug', 'description', 'city_name',
            'experiences', 'hotel_tiers', 'transport_options',
            'is_active', 'created_at'
        ]