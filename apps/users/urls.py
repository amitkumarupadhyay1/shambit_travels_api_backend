from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .auth_views import (
    CurrentUserView,
    CustomTokenObtainPairView,
    GuestCheckoutView,
    LogoutView,
    RegisterView,
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
    # NextAuth sync (legacy)
    path("nextauth-sync/", NextAuthSyncView.as_view(), name="nextauth-sync"),
]
