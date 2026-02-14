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

    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, write_only=True)

    def validate(self, attrs):
        # Backward-compatible email login support for clients that send
        # `email` instead of `username`.
        if attrs.get("email") and not attrs.get("username"):
            attrs["username"] = attrs["email"]

        data = super().validate(attrs)

        # Add user data to response
        data["user"] = UserSerializer(self.user).data

        return data


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""

    phone = serializers.CharField(max_length=15)


class LoginWithOTPSerializer(serializers.Serializer):
    """Serializer for logging in with OTP"""

    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request"""

    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with OTP"""

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data
