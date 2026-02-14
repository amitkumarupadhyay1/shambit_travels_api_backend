import logging

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    GuestUserSerializer,
    LoginWithOTPSerializer,
    ResetPasswordSerializer,
    SendOTPSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from .services.email_service import EmailService
from .services.otp_service import OTPService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Authentication"])
class RegisterView(APIView):
    """User registration endpoint"""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="register_user",
        summary="Register new user",
        description="Create a new user account with email and password",
        request=UserRegistrationSerializer,
        responses={
            201: inline_serializer(
                name="RegisterResponse",
                fields={
                    "user": UserSerializer(),
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                },
            ),
            400: OpenApiExample(
                "Registration failed",
                value={"error": "Email already exists"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Registration request",
                value={
                    "email": "user@example.com",
                    "password": "SecurePass123!",
                    "password_confirm": "SecurePass123!",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+919876543210",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()

                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)

                    logger.info(f"New user registered: {user.email}")

                    return Response(
                        {
                            "user": UserSerializer(user).data,
                            "access": str(refresh.access_token),
                            "refresh": str(refresh),
                        },
                        status=status.HTTP_201_CREATED,
                    )
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                return Response(
                    {"error": "Registration failed. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class SendOTPView(APIView):
    """Send OTP for login or verification"""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="send_otp",
        summary="Send OTP",
        request=SendOTPSerializer,
        responses={200: {"message": "OTP sent successfully"}},
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            otp = OTPService.generate_otp()
            OTPService.store_otp(phone, otp, purpose="login")

            if OTPService.send_otp(phone, otp):
                return Response({"message": "OTP sent successfully"})
            return Response(
                {"error": "Failed to send OTP"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class LoginWithOTPView(APIView):
    """Login with Phone and OTP"""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="login_otp",
        summary="Login with OTP",
        request=LoginWithOTPSerializer,
        responses={200: "JWT Tokens"},
    )
    def post(self, request):
        serializer = LoginWithOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            otp = serializer.validated_data["otp"]

            if OTPService.verify_otp(phone, otp, purpose="login"):
                try:
                    user = User.objects.get(phone=phone)
                    refresh = RefreshToken.for_user(user)
                    return Response(
                        {
                            "user": UserSerializer(user).data,
                            "access": str(refresh.access_token),
                            "refresh": str(refresh),
                        }
                    )
                except User.DoesNotExist:
                    # Optional: Create user if not exists? Reqs differ.
                    # Requirement says "sign in again using ... OTP" implying user exists.
                    # But often OTP login creates user. I'll stick to login existing user for now
                    # OR create a skeletal user if strict requirement.
                    # Reqs: "I shall be able to sign in again..." implies existing user.
                    return Response(
                        {"error": "User with this phone not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            return Response(
                {"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class ForgotPasswordView(APIView):
    """Initiate password reset via SMS OTP"""

    permission_classes = [AllowAny]

    @extend_schema(request=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            try:
                user = User.objects.get(phone=phone)
                otp = OTPService.generate_otp()
                OTPService.store_otp(phone, otp, purpose="reset_password")

                # Send OTP via SMS
                sms_sent = OTPService.send_otp(phone, otp)

                if sms_sent:
                    logger.info(f"Password reset OTP sent to {phone}")
                    return Response({"message": "OTP sent to your phone"})
                else:
                    logger.error(f"Failed to send password reset OTP to {phone}")
                    return Response(
                        {"error": "Failed to send SMS. Please try again."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            except User.DoesNotExist:
                logger.warning(
                    f"Password reset attempted for non-existent phone: {phone}"
                )
                return Response(
                    {"error": "User with this phone number not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error in forgot password for {phone}: {str(e)}",
                    exc_info=True,
                )
                return Response(
                    {"error": "An error occurred. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class ResetPasswordView(APIView):
    """Reset password using SMS OTP"""

    permission_classes = [AllowAny]

    @extend_schema(request=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            otp = serializer.validated_data["otp"]
            password = serializer.validated_data["password"]

            if OTPService.verify_otp(phone, otp, purpose="reset_password"):
                try:
                    user = User.objects.get(phone=phone)
                    user.set_password(password)
                    user.save()
                    logger.info(f"Password reset successful for {phone}")
                    return Response({"message": "Password reset successful"})
                except User.DoesNotExist:
                    return Response(
                        {"error": "User with this phone number not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {"error": "Invalid or expired OTP"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class GuestCheckoutView(APIView):
    """Guest checkout endpoint - creates temporary user for booking"""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="guest_checkout",
        summary="Guest checkout",
        description="Create a temporary guest user for booking without full registration",
        request=GuestUserSerializer,
        responses={
            201: inline_serializer(
                name="GuestCheckoutResponse",
                fields={
                    "user": UserSerializer(),
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "is_guest": serializers.BooleanField(),
                },
            ),
            400: OpenApiExample(
                "Guest checkout failed",
                value={"error": "Email already exists"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Guest checkout request",
                value={
                    "email": "guest@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+919876543210",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = GuestUserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Check if user already exists
                email = serializer.validated_data["email"]
                user = User.objects.filter(email=email).first()

                if user:
                    # User exists, generate tokens for existing user
                    refresh = RefreshToken.for_user(user)
                    logger.info(f"Existing user used guest checkout: {user.email}")
                else:
                    # Create new guest user
                    with transaction.atomic():
                        user = serializer.save()
                        refresh = RefreshToken.for_user(user)
                        logger.info(f"New guest user created: {user.email}")

                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "is_guest": True,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logger.error(f"Guest checkout failed: {str(e)}", exc_info=True)
                return Response(
                    {"error": f"Guest checkout failed: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Return validation errors
        logger.error(f"Guest checkout validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with user data"""

    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        operation_id="login",
        summary="Login",
        description="Obtain JWT access and refresh tokens",
        examples=[
            OpenApiExample(
                "Login request",
                value={"email": "user@example.com", "password": "SecurePass123!"},
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        # Backward-compatible input normalization:
        # allow clients to send {email, password} for login.
        data = request.data.copy()
        if not data.get("username") and data.get("email"):
            data["username"] = data.get("email")

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentication"])
class LogoutView(APIView):
    """Logout endpoint - blacklists refresh token"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="logout",
        summary="Logout",
        description="Blacklist refresh token to logout user",
        request=inline_serializer(
            name="LogoutRequest",
            fields={"refresh": serializers.CharField()},
        ),
        responses={
            200: OpenApiExample(
                "Logout successful",
                value={"message": "Logout successful"},
                response_only=True,
            ),
        },
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"User logged out: {request.user.email}")
                return Response({"message": "Logout successful"})
            return Response(
                {"error": "Refresh token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response(
                {"error": "Logout failed"}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=["Authentication"])
class CurrentUserView(APIView):
    """Get current authenticated user"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="get_current_user",
        summary="Get current user",
        description="Get details of currently authenticated user",
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        operation_id="update_current_user",
        summary="Update current user",
        description="Update details of currently authenticated user",
        request=UserSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
