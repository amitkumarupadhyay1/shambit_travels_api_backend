from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "phone", "is_active")
        read_only_fields = ("id", "is_active")


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
        )

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class GuestUserSerializer(serializers.Serializer):
    """Serializer for guest user creation"""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=15)

    def create(self, validated_data):
        # Create a guest user with a random password
        import secrets

        password = secrets.token_urlsafe(32)
        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data.get("last_name", ""),
            phone=validated_data["phone"],
            is_active=True,
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with user data"""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data to response
        data["user"] = UserSerializer(self.user).data

        return data
