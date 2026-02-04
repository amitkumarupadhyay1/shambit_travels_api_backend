from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PackageViewSet, ExperienceViewSet, HotelTierViewSet, TransportOptionViewSet

# Main packages router
router = DefaultRouter()
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'experiences', ExperienceViewSet, basename='experience')
router.register(r'hotel-tiers', HotelTierViewSet, basename='hoteltier')
router.register(r'transport-options', TransportOptionViewSet, basename='transportoption')

urlpatterns = [
    path('', include(router.urls)),
]