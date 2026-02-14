from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .auth_views import (
    CurrentUserView,
    CustomTokenObtainPairView,
    ForgotPasswordView,
    GuestCheckoutView,
    LoginWithOTPView,
    LogoutView,
    RegisterView,
    ResetPasswordView,
    SendOTPView,
)
from .views import NextAuthSyncView

urlpatterns = [
    # Authentication endpoints
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("guest-checkout/", GuestCheckoutView.as_view(), name="guest_checkout"),
    # OTP & Password Reset
    path("send-otp/", SendOTPView.as_view(), name="send_otp"),
    path("login-otp/", LoginWithOTPView.as_view(), name="login_otp"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    # NextAuth sync (legacy)
    path("nextauth-sync/", NextAuthSyncView.as_view(), name="nextauth-sync"),
]
