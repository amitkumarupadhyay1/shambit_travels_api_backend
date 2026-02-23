from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import BookingViewSet
from .views_draft import BookingDraftViewSet

router = DefaultRouter()
router.register(
    r"", BookingViewSet, basename="booking"
)  # This will make /api/bookings/ work directly
router.register(
    r"drafts", BookingDraftViewSet, basename="booking-draft"
)  # /api/bookings/drafts/

urlpatterns = [
    path("", include(router.urls)),
]
