import logging
import re

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import (OpenApiExample, extend_schema,
                                   inline_serializer)
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.auth_service import AuthService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Authentication"])
class NextAuthSyncView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="oauth_sync",
        summary="OAuth user synchronization",
        description="Synchronize OAuth user data from NextAuth.js frontend with Django backend. Creates or updates user and returns JWT tokens.",
        request=inline_serializer(
            name="OAuthSyncRequest",
            fields={
                "email": serializers.EmailField(help_text="User email address"),
                "first_name": serializers.CharField(
                    help_text="User first name", required=False
                ),
                "last_name": serializers.CharField(
                    help_text="User last name", required=False
                ),
                "provider": serializers.ChoiceField(
                    choices=["google", "github"],
                    help_text="OAuth provider (google or github)",
                ),
                "uid": serializers.CharField(help_text="OAuth provider user ID"),
                "token": serializers.CharField(
                    help_text="OAuth access token for verification"
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name="OAuthSyncResponse",
                fields={
                    "user_id": serializers.IntegerField(),
                    "email": serializers.EmailField(),
                    "first_name": serializers.CharField(),
                    "last_name": serializers.CharField(),
                    "access": serializers.CharField(help_text="JWT access token"),
                    "refresh": serializers.CharField(help_text="JWT refresh token"),
                },
            ),
            400: OpenApiExample(
                "Bad Request",
                value={"error": "email, provider, uid, and token are required"},
                response_only=True,
            ),
            403: OpenApiExample(
                "Forbidden",
                value={"error": "OAuth token verification failed"},
                response_only=True,
            ),
            500: OpenApiExample(
                "Internal Server Error",
                value={"error": "Authentication failed"},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Google OAuth sync",
                value={
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "provider": "google",
                    "uid": "google_user_id_123",
                    "token": "oauth_access_token_here",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Successful sync response",
                value={
                    "user_id": 1,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                },
                response_only=True,
            ),
        ],
    )
    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        provider = request.data.get("provider", "").strip().lower()
        uid = request.data.get("uid", "").strip()
        oauth_token = request.data.get("token")  # ← NOW REQUIRED

        # Validation
        if not all([email, provider, uid, oauth_token]):
            logger.warning(
                f"Incomplete sync request: email={bool(email)}, "
                f"provider={bool(provider)}, uid={bool(uid)}, token={bool(oauth_token)}"
            )
            return Response(
                {"error": "email, provider, uid, and token are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate email format
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return Response(
                {"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate provider
        if provider not in ["google", "github"]:
            return Response(
                {"error": f"Unsupported provider: {provider}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # This now verifies the token with the OAuth provider
            user = AuthService.sync_oauth_user(
                email, first_name, last_name, provider, uid, oauth_token
            )
            tokens = AuthService.get_tokens_for_user(user)

            logger.info(f"Successful OAuth sync for {email} via {provider}")

            return Response(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    **tokens,
                },
                status=status.HTTP_200_OK,
            )

        except PermissionError as e:
            logger.warning(f"OAuth verification failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            logger.error(f"OAuth sync validation error: {str(e)}")
            return Response(
                {"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"OAuth sync unexpected error: {str(e)}")
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
