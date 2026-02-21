from django.urls import path

from .test_views import webhook_health_check
from .views import razorpay_webhook

urlpatterns = [
    path("webhook/razorpay/", razorpay_webhook, name="razorpay-webhook"),
    path("webhook/test/", webhook_health_check, name="webhook-health-check"),
]
