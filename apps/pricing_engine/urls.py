from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PricingRuleViewSet

router = DefaultRouter()
router.register(r'rules', PricingRuleViewSet, basename='pricing-rule')

urlpatterns = [
    path('', include(router.urls)),
]