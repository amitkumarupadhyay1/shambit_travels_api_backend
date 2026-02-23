from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    ExperienceViewSet,
    HotelTierViewSet,
    PackageViewSet,
    TransportOptionViewSet,
)
from .views_vehicle_suggestions import VehicleSuggestionsView

# Main packages router
router = DefaultRouter()
router.register(r"packages", PackageViewSet, basename="package")
router.register(r"experiences", ExperienceViewSet, basename="experience")
router.register(r"hotel-tiers", HotelTierViewSet, basename="hoteltier")
router.register(
    r"transport-options", TransportOptionViewSet, basename="transportoption"
)

urlpatterns = [
    path("", include(router.urls)),
    path("vehicle-suggestions/", VehicleSuggestionsView.as_view(), name="vehicle-suggestions"),
]
