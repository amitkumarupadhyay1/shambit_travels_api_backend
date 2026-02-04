from django.urls import path

from .views import CityContextView

urlpatterns = [
    path("city-context/<slug:slug>/", CityContextView.as_view(), name="city-context"),
]
